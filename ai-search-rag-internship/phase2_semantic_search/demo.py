"""Run a model-free RRF demo before installing BGE-M3 and Faiss."""

from .fusion import reciprocal_rank_fusion
from .metrics import evaluate_qrels


def main() -> None:
    lexical = {
        "q1": ["chunk-exact", "chunk-semantic", "chunk-noise"],
        "q2": ["chunk-noise", "chunk-exact", "chunk-semantic"],
    }
    dense = {
        "q1": ["chunk-semantic", "chunk-exact", "chunk-noise"],
        "q2": ["chunk-semantic", "chunk-exact", "chunk-noise"],
    }
    fused = {
        query_id: [item.doc_id for item in reciprocal_rank_fusion({"bm25": lexical[query_id], "dense": dense[query_id]})]
        for query_id in lexical
    }
    qrels = {"q1": {"chunk-exact"}, "q2": {"chunk-semantic"}}
    print("fused rankings:", fused)
    print("metrics:", evaluate_qrels(fused, qrels, k=3))


if __name__ == "__main__":
    main()

