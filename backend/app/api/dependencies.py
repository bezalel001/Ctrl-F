from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.models.user import UserProfile
from app.services.answer_service import (
    AnswerGenerator,
    AnthropicAnswerGenerator,
    OllamaAnswerGenerator,
    OpenAIAnswerGenerator,
)
from app.services.auth_service import AuthenticationError, resolve_user_from_token
from app.services.embedding_service import EmbeddingProvider, OllamaEmbeddingProvider, OpenAIEmbeddingProvider
from app.storage.database import get_session
from app.storage.vector_store import ChromaVectorStore, VectorStore

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserProfile:
    if credentials is None:
        raise _unauthorized()

    try:
        return resolve_user_from_token(credentials.credentials, settings.jwt_secret)
    except AuthenticationError as exc:
        raise _unauthorized() from exc


def require_permission(permission: str):
    def dependency(current_user: Annotated[UserProfile, Depends(get_current_user)]) -> UserProfile:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )

        return current_user

    return dependency


SessionDep = Annotated[Session, Depends(get_session)]


def get_embedding_provider(settings: Annotated[Settings, Depends(get_settings)]) -> EmbeddingProvider:
    if settings.embedding_provider in {"openai", "auto"} and settings.openai_api_key:
        return OpenAIEmbeddingProvider(api_key=settings.openai_api_key, model=settings.embedding_model)

    if settings.embedding_provider in {"openai", "ollama", "auto"}:
        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )

    if settings.embedding_provider != "openai":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported embedding provider",
        )


def get_vector_store(settings: Annotated[Settings, Depends(get_settings)]) -> VectorStore:
    if settings.vector_store_provider != "chroma":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported vector store provider",
        )

    return ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_collection,
    )


def get_answer_generator(settings: Annotated[Settings, Depends(get_settings)]) -> AnswerGenerator:
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicAnswerGenerator(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIAnswerGenerator(api_key=settings.openai_api_key, model=settings.openai_chat_model)

    if settings.llm_provider == "ollama":
        return OllamaAnswerGenerator(base_url=settings.ollama_base_url, model=settings.ollama_chat_model)

    if settings.llm_provider == "auto":
        if settings.anthropic_api_key:
            return AnthropicAnswerGenerator(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
        if settings.openai_api_key:
            return OpenAIAnswerGenerator(api_key=settings.openai_api_key, model=settings.openai_chat_model)
        return OllamaAnswerGenerator(base_url=settings.ollama_base_url, model=settings.ollama_chat_model)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unsupported LLM provider",
    )


EmbeddingProviderDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]
AnswerGeneratorDep = Annotated[AnswerGenerator, Depends(get_answer_generator)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
