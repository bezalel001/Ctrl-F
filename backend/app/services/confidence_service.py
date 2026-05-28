from app.services.retrieval_service import RetrievedChunk

LOW_CONFIDENCE_THRESHOLD = 0.85
RELIABLE_ANSWER_THRESHOLD = 0.5


def estimate_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0

    top_score = max(chunk.score for chunk in chunks)
    source_bonus = 0.05 if len({chunk.source_id for chunk in chunks}) > 1 else 0.0
    chunk_bonus = 0.05 if len(chunks) >= 2 else 0.0
    return round(min(1.0, top_score + source_bonus + chunk_bonus), 2)


def confidence_warning(confidence: float) -> str | None:
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "Confidence is below 85%; verify with a human owner before acting on this answer."

    return None


def is_reliable_confidence(confidence: float) -> bool:
    return confidence >= RELIABLE_ANSWER_THRESHOLD
