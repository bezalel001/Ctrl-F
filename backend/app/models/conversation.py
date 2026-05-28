from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(primary_key=True, max_length=120)
    user_id: str = Field(index=True, max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_messages"

    id: str = Field(primary_key=True, max_length=120)
    conversation_id: str = Field(foreign_key="conversations.id", index=True, max_length=120)
    role: str = Field(index=True, max_length=40)
    content: str = Field(max_length=6000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
