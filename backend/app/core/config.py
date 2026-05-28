from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ctrl-F Backend"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="APP_ENV")
    jwt_secret: str = Field(default="change-me", validation_alias="JWT_SECRET")
    database_url: str = Field(
        default="sqlite:///./ctrlf.db",
        validation_alias="DATABASE_URL",
    )
    approved_sources_root: str = Field(default="../data/approved_sources", validation_alias="APPROVED_SOURCES_ROOT")
    vector_store_provider: str = Field(default="chroma", validation_alias="VECTOR_STORE_PROVIDER")
    chroma_host: str = Field(default="localhost", validation_alias="CHROMA_HOST")
    chroma_port: int = Field(default=8001, validation_alias="CHROMA_PORT")
    chroma_collection: str = Field(default="ctrl_f_sources", validation_alias="CHROMA_COLLECTION")
    embedding_provider: str = Field(default="openai", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", validation_alias="OLLAMA_EMBEDDING_MODEL")
    ollama_chat_model: str = Field(default="llama3.2", validation_alias="OLLAMA_CHAT_MODEL")
    llm_provider: str = Field(default="auto", validation_alias="LLM_PROVIDER")
    openai_chat_model: str = Field(default="gpt-4.1-mini", validation_alias="OPENAI_CHAT_MODEL")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", validation_alias="ANTHROPIC_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
