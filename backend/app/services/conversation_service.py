from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session, select

from app.models.conversation import Conversation, ConversationMessage
from app.models.user import UserProfile


class ConversationAccessError(Exception):
    """Raised when a user attempts to access another user's conversation."""


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content: str


def get_or_create_conversation(
    session: Session,
    *,
    conversation_id: str | None,
    user: UserProfile,
) -> Conversation:
    if conversation_id:
        conversation = session.get(Conversation, conversation_id)
        if conversation is not None:
            if conversation.user_id != user.id:
                raise ConversationAccessError("Conversation is not available for this user")

            return conversation

    conversation = Conversation(id=conversation_id or str(uuid4()), user_id=user.id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def load_recent_messages(
    session: Session,
    *,
    conversation_id: str,
    limit: int = 6,
) -> list[ConversationTurn]:
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(session.exec(statement).all())
    messages.reverse()
    return [ConversationTurn(role=message.role, content=message.content) for message in messages]


def record_message(
    session: Session,
    *,
    conversation: Conversation,
    role: str,
    content: str,
    message_id: str | None = None,
) -> ConversationMessage:
    message = ConversationMessage(
        id=message_id or str(uuid4()),
        conversation_id=conversation.id,
        role=role,
        content=content,
    )
    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
