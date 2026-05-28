from dataclasses import dataclass
from pathlib import Path

from app.models.source import Source

LOCAL_SOURCE_PREFIX = "data/approved_sources/"
SUPPORTED_TEXT_SUFFIXES = {".md", ".txt"}


class DocumentLoadError(Exception):
    """Raised when an approved source cannot be loaded for indexing."""


@dataclass(frozen=True)
class LoadedDocument:
    text: str
    resolved_path: Path


def load_source_document(source: Source, approved_sources_root: str) -> LoadedDocument:
    if not source.location.startswith(LOCAL_SOURCE_PREFIX):
        raise DocumentLoadError("only local approved source files can be indexed in this prototype")

    relative_path = source.location.removeprefix(LOCAL_SOURCE_PREFIX)
    resolved_path = (Path(approved_sources_root) / relative_path).resolve()
    approved_root = Path(approved_sources_root).resolve()

    if approved_root not in resolved_path.parents and resolved_path != approved_root:
        raise DocumentLoadError("source path escapes the approved sources root")

    if resolved_path.suffix.lower() not in SUPPORTED_TEXT_SUFFIXES:
        raise DocumentLoadError("only Markdown and text files are supported for indexing")

    if not resolved_path.exists() or not resolved_path.is_file():
        raise DocumentLoadError("source file does not exist")

    text = resolved_path.read_text(encoding="utf-8").strip()
    if not text:
        raise DocumentLoadError("source file is empty")

    return LoadedDocument(text=text, resolved_path=resolved_path)

