"""Optional Faiss Flat/HNSW index builders used by the Dense retriever."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from .embedding import OptionalDependencyError


IndexKind = Literal["flat", "hnsw"]


def _require_faiss() -> Any:
    try:
        import faiss
    except ImportError as exc:
        raise OptionalDependencyError(
            "Faiss requires faiss-cpu. Install requirements/phase2.txt first."
        ) from exc
    return faiss


def build_faiss_index(
    vectors: np.ndarray,
    *,
    kind: IndexKind = "flat",
    hnsw_m: int = 32,
    ef_construction: int = 128,
    ef_search: int = 64,
) -> Any:
    """Build an inner-product index from normalized float32 vectors."""

    if kind not in {"flat", "hnsw"}:
        raise ValueError("kind must be 'flat' or 'hnsw'")
    if hnsw_m <= 0 or ef_construction <= 0 or ef_search <= 0:
        raise ValueError("HNSW parameters must be positive")
    array = np.asarray(vectors, dtype="float32")
    if array.ndim != 2 or array.shape[0] == 0:
        raise ValueError("vectors must be a non-empty 2D array")

    faiss = _require_faiss()
    dimension = int(array.shape[1])
    if kind == "flat":
        index = faiss.IndexFlatIP(dimension)
    else:
        index = faiss.IndexHNSWFlat(dimension, hnsw_m, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = ef_construction
        index.hnsw.efSearch = ef_search
    index.add(array)
    return index


def search_faiss(
    index: Any,
    query_vectors: np.ndarray,
    *,
    top_k: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    queries = np.asarray(query_vectors, dtype="float32")
    if queries.ndim != 2:
        raise ValueError("query_vectors must be a 2D array")
    return index.search(queries, top_k)


def save_faiss_index(index: Any, path: str | Path) -> None:
    faiss = _require_faiss()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output))


def load_faiss_index(path: str | Path) -> Any:
    faiss = _require_faiss()
    return faiss.read_index(str(path))
