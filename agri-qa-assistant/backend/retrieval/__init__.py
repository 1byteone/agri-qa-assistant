# -*- coding: utf-8 -*-
"""
检索增强模块 — RAG Pipeline 组件。

提供以下能力：
- RRF 融合检索（Reciprocal Rank Fusion）
- Parent-Child 分块索引（父子文档上下文恢复）
- QueryRouter 查询路由（意图分类 → 路径选择）
- QueryTransformer 查询改写（术语规范化 + 子查询分解）
"""
from retrieval.rrf_fusion import rrf_fusion, RRFFusion
from retrieval.parent_child import ParentChildIndexer
from retrieval.query_router import QueryRouter, Route
from retrieval.query_transformer import QueryTransformer

__all__ = [
    "rrf_fusion",
    "RRFFusion",
    "ParentChildIndexer",
    "QueryRouter",
    "Route",
    "QueryTransformer",
]
