from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    text: str


def chunk_text(text: str, *, max_chars: int = 1800, overlap_chars: int = 200) -> list[DocumentChunk]:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        return []

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be greater than or equal to 0 and smaller than max_chars")

    chunks: list[DocumentChunk] = []
    start = 0

    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(DocumentChunk(index=len(chunks), text=chunk))

        if end == len(normalized):
            break

        start = end - overlap_chars

    return chunks

