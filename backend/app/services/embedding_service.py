from typing import Protocol

import httpx
from openai import OpenAI


class EmbeddingError(Exception):
    """Raised when embeddings cannot be generated."""


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding per input text."""


class OpenAIEmbeddingProvider:
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY is required for OpenAI embeddings")

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]


class OllamaEmbeddingProvider:
    def __init__(self, *, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                response = client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": text},
                )
                response.raise_for_status()
                payload = response.json()
                embeddings.append(_extract_ollama_embedding(payload))

        return embeddings


def _extract_ollama_embedding(payload: dict[str, object]) -> list[float]:
    embeddings = payload.get("embeddings")
    if isinstance(embeddings, list) and embeddings:
        first_embedding = embeddings[0]
        if isinstance(first_embedding, list):
            return [float(value) for value in first_embedding]

    embedding = payload.get("embedding")
    if isinstance(embedding, list):
        return [float(value) for value in embedding]

    raise EmbeddingError("Ollama did not return an embedding")
