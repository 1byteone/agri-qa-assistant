"""A compact BM25 retriever used by the end-to-end project."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from collections.abc import Callable, Mapping, Sequence


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """Tokenize English words and Chinese characters for a deterministic baseline."""

    return TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True, slots=True)
class SearchResult:
    doc_id: str
    score: float
    text: str
    metadata: dict[str, object]


class BM25Retriever:
    """In-memory BM25 index for small knowledge bases and teaching experiments."""

    def __init__(
        self,
        documents: Sequence[Mapping[str, object]],
        *,
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Callable[[str], list[str]] = tokenize,
    ) -> None:
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 > 0 and 0 <= b <= 1")
        self.k1 = k1
        self.b = b
        self.tokenizer = tokenizer
        self.documents = [dict(document) for document in documents]
        self._tokens = [tokenizer(str(document.get("text", ""))) for document in self.documents]
        self._term_frequencies = [Counter(tokens) for tokens in self._tokens]
        self._doc_frequency = Counter(
            term for frequencies in self._term_frequencies for term in frequencies.keys()
        )
        self._document_count = len(self.documents)
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / self._document_count
            if self._document_count
            else 0.0
        )

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        predicate: Callable[[Mapping[str, object]], bool] | None = None,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query_terms = set(self.tokenizer(query))
        if not query_terms or not self.documents:
            return []

        scored: list[SearchResult] = []
        for document, frequencies, tokens in zip(self.documents, self._term_frequencies, self._tokens):
            if predicate is not None and not predicate(document):
                continue
            score = 0.0
            length = len(tokens)
            for term in query_terms:
                term_frequency = frequencies.get(term, 0)
                if not term_frequency:
                    continue
                document_frequency = self._doc_frequency[term]
                idf = math.log(1 + (self._document_count - document_frequency + 0.5) / (document_frequency + 0.5))
                denominator = term_frequency + self.k1 * (
                    1 - self.b + self.b * length / max(self._average_length, 1e-12)
                )
                score += idf * term_frequency * (self.k1 + 1) / denominator
            if score > 0:
                scored.append(
                    SearchResult(
                        doc_id=str(document["id"]),
                        score=score,
                        text=str(document.get("text", "")),
                        metadata={key: value for key, value in document.items() if key not in {"id", "text"}},
                    )
                )

        return sorted(scored, key=lambda item: (-item.score, item.doc_id))[:top_k]

