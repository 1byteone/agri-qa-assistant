"""Optional BGE-M3 embedding adapter with a stable project-level contract."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


class OptionalDependencyError(RuntimeError):
    """Raised when an optional model/index dependency is not installed."""


@dataclass(frozen=True, slots=True)
class DenseEncoding:
    vectors: np.ndarray
    model_id: str
    dimension: int
    normalized: bool


def normalize_vectors(vectors: Any) -> np.ndarray:
    """Return float32 row-normalized vectors for inner-product search."""

    array = np.asarray(vectors, dtype="float32")
    if array.ndim != 2:
        raise ValueError("vectors must be a 2D array")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return array / np.maximum(norms, 1e-12)


def encode_with_bge_m3(
    texts: Sequence[str],
    *,
    model_id: str = "BAAI/bge-m3",
    batch_size: int = 4,
    max_length: int = 512,
    use_fp16: bool = False,
) -> DenseEncoding:
    """Encode texts using BGE-M3 without importing FlagEmbedding at module load."""

    if batch_size <= 0 or max_length <= 0:
        raise ValueError("batch_size and max_length must be positive")
    try:
        from FlagEmbedding import BGEM3FlagModel
    except ImportError as exc:
        raise OptionalDependencyError(
            "BGE-M3 requires FlagEmbedding. Install requirements/phase2.txt first."
        ) from exc

    model = BGEM3FlagModel(model_id, use_fp16=use_fp16)
    encoded = model.encode(
        list(texts),
        batch_size=batch_size,
        max_length=max_length,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    dense_vectors = encoded.get("dense_vecs")
    if dense_vectors is None:
        raise RuntimeError("BGE-M3 did not return dense_vecs")
    normalized = normalize_vectors(dense_vectors)
    return DenseEncoding(
        vectors=normalized,
        model_id=model_id,
        dimension=int(normalized.shape[1]),
        normalized=True,
    )
