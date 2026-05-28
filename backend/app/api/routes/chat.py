from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    AnswerGeneratorDep,
    EmbeddingProviderDep,
    VectorStoreDep,
    get_current_user,
)
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.models.user import UserProfile
from app.services.answer_service import AnswerGenerationError
from app.services.confidence_service import confidence_warning, estimate_confidence
from app.services.retrieval_service import RetrievedChunk, retrieve_authorized_chunks

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    answer_generator: AnswerGeneratorDep,
) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid4())
    chunks = retrieve_authorized_chunks(
        question=request.question,
        user=current_user,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    if not chunks:
        return _fallback_response(conversation_id, confidence=0.0)

    confidence = estimate_confidence(chunks)
    warning = confidence_warning(confidence)

    try:
        answer = answer_generator.generate_answer(question=request.question, chunks=chunks)
    except AnswerGenerationError:
        return _fallback_response(conversation_id, confidence=confidence)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=str(uuid4()),
        answer=answer,
        sources=[_to_chat_source(chunk) for chunk in chunks],
        confidence=confidence,
        warning=warning,
        suggested_contacts=[],
    )


def _fallback_response(conversation_id: str, *, confidence: float) -> ChatResponse:
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=str(uuid4()),
        answer="I don't know based on the approved company sources available to me.",
        sources=[],
        confidence=confidence,
        warning=confidence_warning(confidence),
        suggested_contacts=["Human Resources", "IT Support"],
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
