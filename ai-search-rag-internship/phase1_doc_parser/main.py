"""Batch CLI: parse a directory and write structured chunks as JSON."""

from __future__ import annotations

import argparse
from hashlib import sha1
import json
from pathlib import Path

from .parser import parse_file
from .splitter import RecursiveSplitter


def build_chunks(input_dir: Path, splitter: RecursiveSplitter) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    supported = {".pdf", ".md", ".markdown", ".txt"}
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in supported:
            continue
        for document in parse_file(path):
            for index, text in enumerate(splitter.split(document.text)):
                stable_key = f"{document.source}:{document.page}:{index}:{text}"
                chunks.append(
                    {
                        "id": sha1(stable_key.encode("utf-8")).hexdigest()[:16],
                        "text": text,
                        "source": document.source,
                        "page": document.page,
                        "chunk_index": index,
                        "metadata": document.metadata,
                    }
                )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=128)
    args = parser.parse_args()

    splitter = RecursiveSplitter(chunk_size=args.chunk_size, overlap=args.overlap)
    chunks = build_chunks(args.input_dir, splitter)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {args.output}")


if __name__ == "__main__":
    main()

