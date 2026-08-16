from pathlib import Path

import pytest

from phase1_doc_parser.main import build_chunks
from phase1_doc_parser.parser import parse_file
from phase1_doc_parser.splitter import RecursiveSplitter


def test_splitter_respects_size_and_keeps_context() -> None:
    text = "第一段内容。" * 80
    chunks = RecursiveSplitter(chunk_size=64, overlap=16).split(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 64 for chunk in chunks)
    assert any(set(a[-16:]) & set(b[:16]) for a, b in zip(chunks, chunks[1:]))


def test_splitter_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        RecursiveSplitter(chunk_size=10, overlap=10)


def test_splitter_handles_oversized_unit_without_looping() -> None:
    chunks = RecursiveSplitter(chunk_size=32, overlap=8, separators=("\n", "")).split("x" * 100)

    assert len(chunks) == 4
    assert all(len(chunk) <= 32 for chunk in chunks)


def test_markdown_parser_collects_headings() -> None:
    path = Path("phase1_doc_parser/examples/input/quickstart.md")
    documents = parse_file(path)

    assert len(documents) == 1
    assert documents[0].metadata["format"] == "markdown"
    assert documents[0].metadata["headings"] == ["Phase 1 Quickstart", "Chunk 策略"]


def test_pdf_parser_returns_page_metadata(tmp_path: Path) -> None:
    pymupdf = pytest.importorskip("pymupdf")
    pdf_path = tmp_path / "sample.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "PDF parser smoke test")
        pdf.save(pdf_path)

    documents = parse_file(pdf_path)

    assert len(documents) == 1
    assert documents[0].page == 1
    assert documents[0].metadata["format"] == "pdf"
    assert "PDF parser smoke test" in documents[0].text


def test_batch_builder_emits_traceable_chunks(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "note.md").write_text("# Title\n\n内容。" * 20, encoding="utf-8")

    chunks = build_chunks(input_dir, RecursiveSplitter(chunk_size=40, overlap=8))

    assert chunks
    assert {"id", "text", "source", "page", "chunk_index", "metadata"} <= chunks[0].keys()
    assert all(chunk["source"].endswith("note.md") for chunk in chunks)
