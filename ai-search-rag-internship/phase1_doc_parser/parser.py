"""Small, dependency-light parsers for the Phase 1 learning project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass(slots=True)
class ParsedDocument:
    text: str
    source: str
    page: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


def _markdown_metadata(text: str) -> dict[str, object]:
    headings = [
        match.group(2).strip()
        for line in text.splitlines()
        if (match := re.match(r"^(#{1,6})\s+(.+?)\s*$", line))
    ]
    return {"format": "markdown", "headings": headings}


def parse_markdown(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8-sig")
    return ParsedDocument(
        text=text.strip(),
        source=str(path),
        metadata=_markdown_metadata(text),
    )


def parse_text(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8-sig")
    return ParsedDocument(text=text.strip(), source=str(path), metadata={"format": "text"})


def parse_pdf(path: Path) -> list[ParsedDocument]:
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - exercised in an unconfigured env
        try:
            import fitz as pymupdf
        except ImportError as fallback_exc:
            raise RuntimeError("PDF parsing requires PyMuPDF. Install requirements/phase1.txt.") from fallback_exc

    documents: list[ParsedDocument] = []
    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                documents.append(
                    ParsedDocument(
                        text=text,
                        source=str(path),
                        page=page_number,
                        metadata={"format": "pdf", "page_count": len(pdf)},
                    )
                )
    return documents


def parse_file(path: str | Path) -> list[ParsedDocument]:
    """Parse one supported file into one or more page-aware documents."""

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    if suffix in {".md", ".markdown"}:
        return [parse_markdown(file_path)]
    if suffix == ".txt":
        return [parse_text(file_path)]
    raise ValueError(f"Unsupported file type: {file_path.suffix or '<none>'}")
