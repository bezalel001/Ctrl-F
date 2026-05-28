from collections.abc import Sequence
from typing import Protocol

import httpx
from openai import OpenAI

from app.services.conversation_service import ConversationTurn
from app.services.retrieval_service import RetrievedChunk


class AnswerGenerationError(Exception):
    """Raised when the configured LLM provider cannot generate an answer."""


class AnswerGenerator(Protocol):
    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: Sequence[ConversationTurn],
    ) -> str:
        """Generate a grounded answer from retrieved chunks."""


class OpenAIAnswerGenerator:
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise AnswerGenerationError("OPENAI_API_KEY is required for OpenAI answer generation")

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: Sequence[ConversationTurn],
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "developer", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(question, chunks, history)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise AnswerGenerationError("OpenAI returned an empty answer")

        return content.strip()


class AnthropicAnswerGenerator:
    def __init__(self, *, api_key: str | None, model: str) -> None:
        if not api_key:
            raise AnswerGenerationError("ANTHROPIC_API_KEY is required for Anthropic answer generation")

        self._api_key = api_key
        self._model = model

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: Sequence[ConversationTurn],
    ) -> str:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 700,
                    "system": _system_prompt(),
                    "messages": [{"role": "user", "content": _user_prompt(question, chunks, history)}],
                },
            )
            response.raise_for_status()
            payload = response.json()

        return _extract_anthropic_text(payload)


class OllamaAnswerGenerator:
    def __init__(self, *, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: Sequence[ConversationTurn],
    ) -> str:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": _system_prompt()},
                        {"role": "user", "content": _user_prompt(question, chunks, history)},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()

        message = payload.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"].strip()

        raise AnswerGenerationError("Ollama returned an empty answer")


def _system_prompt() -> str:
    return (
        "You are Ctrl-F, a company knowledge assistant. Answer only from the approved source "
        "excerpts provided by the system. If the excerpts are insufficient, say you do not know. "
        "Use prior conversation only to understand follow-up wording, not as a source of truth. "
        "Keep answers concise and do not invent citations or policy details."
    )


def _user_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    history: Sequence[ConversationTurn],
) -> str:
    context = "\n\n".join(
        f"[Source {index + 1}: {chunk.source_title}]\n{chunk.text}"
        for index, chunk in enumerate(chunks)
    )
    history_context = _format_history(history)
    if history_context:
        return (
            f"Recent conversation:\n{history_context}\n\n"
            f"Question:\n{question}\n\n"
            f"Approved source excerpts:\n{context}"
        )

    return f"Question:\n{question}\n\nApproved source excerpts:\n{context}"


def _format_history(history: Sequence[ConversationTurn]) -> str:
    return "\n".join(
        f"{turn.role.title()}: {turn.content[:1000]}"
        for turn in history
        if turn.content.strip()
    )


def _extract_anthropic_text(payload: dict[str, object]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        raise AnswerGenerationError("Anthropic returned an empty answer")

    text_parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            text_parts.append(item["text"])

    answer = "\n".join(text_parts).strip()
    if not answer:
        raise AnswerGenerationError("Anthropic returned an empty answer")

    return answer
