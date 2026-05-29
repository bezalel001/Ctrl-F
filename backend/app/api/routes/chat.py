from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    AnswerGeneratorDep,
    EmbeddingProviderDep,
    SessionDep,
    VectorStoreDep,
    get_current_user,
)
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.models.user import UserProfile
from app.services.answer_service import AnswerGenerationError
from app.services.audit_service import create_audit_log
from app.services.confidence_service import confidence_warning, estimate_confidence, is_reliable_confidence
from app.services.conversation_service import (
    ConversationAccessError,
    get_or_create_conversation,
    load_recent_messages,
    record_message,
)
from app.services.retrieval_service import RetrievedChunk, retrieve_authorized_chunks
from app.services.safety_service import suggested_contacts

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    answer_generator: AnswerGeneratorDep,
    session: SessionDep,
) -> ChatResponse:
    try:
        conversation = get_or_create_conversation(
            session,
            conversation_id=request.conversation_id,
            user=current_user,
        )
    except ConversationAccessError as exc:
        create_audit_log(
            session,
            event_type="conversation.access_denied",
            actor=current_user,
            resource_type="conversation",
            resource_id=request.conversation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    history = load_recent_messages(session, conversation_id=conversation.id)
    chunks = retrieve_authorized_chunks(
        question=request.question,
        user=current_user,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )
    record_message(session, conversation=conversation, role="user", content=request.question)

    if not chunks:
        _audit_low_confidence(
            session,
            current_user,
            conversation_id=conversation.id,
            confidence=0.0,
            reason="no_authorized_chunks",
        )
        assistant_message = record_message(
            session,
            conversation=conversation,
            role="assistant",
            content=_fallback_answer(),
        )
        return _fallback_response(
            conversation.id,
            message_id=assistant_message.id,
            confidence=0.0,
            contacts=suggested_contacts(current_user, chunks),
        )

    confidence = estimate_confidence(chunks)
    warning = confidence_warning(confidence)

    if not is_reliable_confidence(confidence):
        _audit_low_confidence(
            session,
            current_user,
            conversation_id=conversation.id,
            confidence=confidence,
            reason="unreliable_retrieval",
            chunks=chunks,
        )
        assistant_message = record_message(
            session,
            conversation=conversation,
            role="assistant",
            content=_fallback_answer(),
        )
        return _fallback_response(
            conversation.id,
            message_id=assistant_message.id,
            confidence=confidence,
            contacts=suggested_contacts(current_user, chunks),
        )

    try:
        answer = answer_generator.generate_answer(
            question=request.question,
            chunks=chunks,
            history=history,
        )
    except AnswerGenerationError:
        if warning:
            _audit_low_confidence(
                session,
                current_user,
                conversation_id=conversation.id,
                confidence=confidence,
                reason="answer_generation_failed",
                chunks=chunks,
            )
        assistant_message = record_message(
            session,
            conversation=conversation,
            role="assistant",
            content=_fallback_answer(),
        )
        return _fallback_response(
            conversation.id,
            message_id=assistant_message.id,
            confidence=confidence,
            contacts=suggested_contacts(current_user, chunks),
        )

    assistant_message = record_message(
        session,
        conversation=conversation,
        role="assistant",
        content=answer,
    )

    if warning:
        _audit_low_confidence(
            session,
            current_user,
            conversation_id=conversation.id,
            confidence=confidence,
            reason="low_confidence_answer",
            chunks=chunks,
        )

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=answer,
        sources=[_to_chat_source(chunk) for chunk in chunks],
        confidence=confidence,
        warning=warning,
        suggested_contacts=[],
    )


def _fallback_response(
    conversation_id: str,
    *,
    message_id: str,
    confidence: float,
    contacts: list[str],
) -> ChatResponse:
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        answer=_fallback_answer(),
        sources=[],
        confidence=confidence,
        warning=confidence_warning(confidence),
        suggested_contacts=contacts,
    )


def _fallback_answer() -> str:
    return "I don't know based on the approved company sources available to me."


def _audit_low_confidence(
    session,
    user: UserProfile,
    *,
    conversation_id: str,
    confidence: float,
    reason: str,
    chunks: list[RetrievedChunk] | None = None,
) -> None:
    create_audit_log(
        session,
        event_type="chat.low_confidence",
        actor=user,
        resource_type="conversation",
        resource_id=conversation_id,
        details={
            "confidence": confidence,
            "reason": reason,
            "source_ids": [chunk.source_id for chunk in chunks or []],
        },
    )


def _to_chat_source(chunk: RetrievedChunk) -> ChatSource:
    excerpt = chunk.text[:320].strip()
    if len(chunk.text) > 320:
        excerpt = f"{excerpt}..."

    return ChatSource(
        source_id=chunk.source_id,
        title=chunk.source_title,
        location=chunk.source_location,
        excerpt=excerpt,
        score=round(chunk.score, 2),
    )
