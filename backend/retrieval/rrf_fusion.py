# -*- coding: utf-8 -*-
"""
RRF (Reciprocal Rank Fusion) 融合检索。

将多路排序结果融合为统一排序，核心公式：
    RRF_score(d) = Σ weight_i / (k + rank_i(d))

参考论文: "Reciprocal Rank Fusion outperforms Condorcet and individual
Rank Learning Methods" (Cormack et al., 2009)
"""
from __future__ import annotations
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def rrf_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    weights: Optional[List[float]] = None,
    content_key: str = "content",
    score_key: str = "relevance",
) -> List[Dict[str, Any]]:
    """将多路排序结果通过 RRF 融合为统一排序。

    Parameters
    ----------
    ranked_lists : list of list of dict
        每个子列表是一路独立的排序结果，每项为包含 content_key 的字典。
    k : int
        RRF 常数，控制排名靠后结果的衰减速度。默认 60（论文推荐值）。
    weights : list of float, optional
        各路权重，长度须与 ranked_lists 一致。默认等权。
    content_key : str
        用于去重的文档内容键名。
    score_key : str
        保留原始分数的键名。

    Returns
    -------
    list of dict
        融合后按 rrf_score 降序排列的结果列表，每项附加 rrf_score 字段。
    """
    if not ranked_lists:
        return []

    n_lists = len(ranked_lists)
    if weights is None:
        weights = [1.0 / n_lists] * n_lists
    elif len(weights) != n_lists:
        raise ValueError(f"weights 长度 ({len(weights)}) 须与 ranked_lists 长度 ({n_lists}) 一致")

    # 累加 RRF 分数
    doc_scores: Dict[str, float] = defaultdict(float)
    doc_map: Dict[str, Dict[str, Any]] = {}

    for ranked_list, weight in zip(ranked_lists, weights):
        for rank, item in enumerate(ranked_list):
            doc_id = _doc_identity(item, content_key)
            rrf_contribution = weight / (k + rank + 1)  # rank 从 1 开始
            doc_scores[doc_id] += rrf_contribution
            # 保留最相关的原始文档
            if doc_id not in doc_map or _safe_score(item, score_key) > _safe_score(doc_map[doc_id], score_key):
                doc_map[doc_id] = item

    # 按 RRF 分数降序排列
    sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids:
        merged = dict(doc_map[doc_id])
        merged["rrf_score"] = round(doc_scores[doc_id], 8)
        results.append(merged)

    return results


def _doc_identity(item: Dict[str, Any], content_key: str) -> str:
    """生成文档唯一标识，优先使用 content_hash，回退到内容摘要。"""
    metadata = item.get("metadata") or {}
    if metadata.get("content_hash"):
        return metadata["content_hash"]
    content = str(item.get(content_key, ""))
    # 使用内容前 200 字符 + metadata 关键字段作为去重键
    title = metadata.get("title", "")
    source = metadata.get("source", "")
    return f"{title}|{source}|{content[:200]}"


def _safe_score(item: Dict[str, Any], score_key: str) -> float:
    """安全提取分数，缺失时返回 0。"""
    try:
        return float(item.get(score_key, 0))
    except (TypeError, ValueError):
        return 0.0


class RRFFusion:
    """RRF 融合检索器，可配置参数并复用。

    Parameters
    ----------
    k : int
        RRF 常数。
    weights : dict, optional
        路由名 → 权重的映射，如 {"vector": 0.6, "lexical": 0.4}。
    """

    def __init__(
        self,
        k: int = 60,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.k = k
        self.weights = weights or {}

    def fuse(
        self,
        ranked_lists: Dict[str, List[Dict[str, Any]]],
        content_key: str = "content",
        score_key: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """融合多路排序结果。

        Parameters
        ----------
        ranked_lists : dict
            路由名 → 排序结果列表的映射，如
            {"vector": [...], "lexical": [...]}。
        """
        if not ranked_lists:
            return []

        names = list(ranked_lists.keys())
        lists = [ranked_lists[name] for name in names]
        weights = [self.weights.get(name, 1.0 / len(names)) for name in names]

        # 归一化权重
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]

        return rrf_fusion(
            lists,
            k=self.k,
            weights=weights,
            content_key=content_key,
            score_key=score_key,
        )
