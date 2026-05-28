from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=120)


class ChatSource(BaseModel):
    source_id: int
    title: str
    location: str
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: list[ChatSource]
    confidence: float
    warning: str | None = None
    suggested_contacts: list[str] = Field(default_factory=list)
