from app.api.dependencies import get_embedding_provider
from app.core.config import Settings
from app.services.embedding_service import OllamaEmbeddingProvider, OpenAIEmbeddingProvider, _extract_ollama_embedding


def test_embedding_provider_uses_openai_when_key_is_available() -> None:
    settings = Settings(
        embedding_provider="auto",
        openai_api_key="test-key",
        embedding_model="text-embedding-3-small",
    )

    provider = get_embedding_provider(settings)

    assert isinstance(provider, OpenAIEmbeddingProvider)


def test_embedding_provider_falls_back_to_ollama_without_openai_key() -> None:
    settings = Settings(
        embedding_provider="auto",
        openai_api_key=None,
        ollama_base_url="http://ollama:11434",
        ollama_embedding_model="nomic-embed-text",
    )

    provider = get_embedding_provider(settings)

    assert isinstance(provider, OllamaEmbeddingProvider)


def test_ollama_embedding_extraction_supports_embed_response_shape() -> None:
    payload = {"embeddings": [[0.1, 0.2, 0.3]]}

    assert _extract_ollama_embedding(payload) == [0.1, 0.2, 0.3]


def test_ollama_embedding_extraction_supports_legacy_response_shape() -> None:
    payload = {"embedding": [0.4, 0.5, 0.6]}

    assert _extract_ollama_embedding(payload) == [0.4, 0.5, 0.6]

