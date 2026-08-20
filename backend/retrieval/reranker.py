"""
CropWise BGE-Reranker 重排序模块
==================================

基于 BAAI/bge-reranker-v2-m3 交叉编码器的检索结果重排序。

重排序在 RAG Pipeline 中的位置：
  检索（Vector + BM25 + RRF）→ 候选集（top-30）→ Reranker → 精排集（top-5）

支持三种模式：
1. 本地推理（需要 GPU + sentence-transformers）
2. API 调用（兼容 TEI / vLLM / 自定义端点）
3. 不可用时回退（跳过重排序，保留原始排名）

参考：
- BAAI/bge-reranker-v2-m3: 多语言交叉编码器，最大 2048 token
- sentence-transformers CrossEncoder API
"""

from __future__ import annotations
import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """重排序结果"""
    content: str
    metadata: Dict[str, Any]
    original_score: float       # 原始检索分数
    rerank_score: float         # 重排序分数
    rank: int                   # 重排序后排名
    original_rank: int          # 原始排名
    retrieval_strategy: str = "reranked"


class BGEReranker:
    """
    BGE-Reranker-v2-M3 重排序器。

    特性：
    - 多语言支持（中英文混合）
    - 最大 2048 token 输入
    - 可插拔：不可用时自动跳过
    - 批量处理：支持 64 batch_size

    使用示例：
        reranker = BGEReranker()
        results = reranker.rerank("水稻病虫害", candidates, top_k=5)
    """

    def __init__(
        self,
        mode: str = "auto",
        model_name: str = "BAAI/bge-reranker-v2-m3",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512,
        device: str = "cpu",
        score_threshold: Optional[float] = None,
    ):
        """
        初始化 Reranker。

        Args:
            mode: "local" / "api" / "auto"（自动检测）
            model_name: 模型名称
            api_url: API 端点（mode="api" 时）
            api_key: API 密钥
            batch_size: 批量大小
            max_length: 最大 token 长度
            device: 推理设备
            score_threshold: 分数阈值（低于此分数的文档被过滤）
        """
        self.mode = mode
        self.model_name = model_name
        self.api_url = api_url or os.getenv("RERANKER_API_URL", "")
        self.api_key = api_key or os.getenv("RERANKER_API_KEY", "")
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = device
        self.score_threshold = score_threshold
        self._model = None
        self._available = False

        self._init_model()

    def _init_model(self):
        """初始化模型"""
        if self.mode == "auto":
            # 尝试本地，失败尝试 API
            if self._try_local():
                return
            if self._try_api():
                return
            logger.info("Reranker 不可用，将跳过重排序")
            return
        elif self.mode == "local":
            self._try_local()
        elif self.mode == "api":
            self._try_api()

    def _try_local(self) -> bool:
        """尝试本地加载"""
        try:
            from sentence_transformers import CrossEncoder
            import torch

            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"加载 Reranker 模型: {self.model_name} (device={device})")
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=device,
                trust_remote_code=True,
            )
            self._available = True
            self.mode = "local"
            logger.info("Reranker 本地模型加载成功")
            return True
        except ImportError:
            logger.debug("sentence-transformers 未安装，跳过本地 Reranker")
            return False
        except Exception as e:
            logger.warning(f"Reranker 本地加载失败: {e}")
            return False

    def _try_api(self) -> bool:
        """尝试 API 模式"""
        if not self.api_url:
            return False
        try:
            import requests
            # 简单健康检查
            url = self.api_url.rstrip("/")
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # 测试请求
            payload = {
                "model": self.model_name,
                "query": "test",
                "documents": ["test document"],
            }
            resp = requests.post(f"{url}/rerank", headers=headers, json=payload, timeout=10)
            if resp.status_code < 500:
                self._available = True
                self.mode = "api"
                logger.info(f"Reranker API 连接成功: {url}")
                return True
        except Exception as e:
            logger.debug(f"Reranker API 连接失败: {e}")
        return False

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        content_key: str = "content",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        对候选文档进行重排序。

        Args:
            query: 查询文本
            candidates: 候选文档列表
            top_k: 返回数量
            content_key: 文档内容字段名

        Returns:
            (results, trace) 元组
        """
        trace = {
            "reranker_mode": self.mode,
            "reranker_available": self._available,
            "input_count": len(candidates),
            "top_k": top_k,
        }

        if not candidates:
            return [], trace

        if not self._available:
            trace["reranker_applied"] = False
            trace["reason"] = "reranker_unavailable"
            # 保留原始排名
            results = []
            for rank, item in enumerate(candidates[:top_k], start=1):
                result_item = dict(item)
                result_item["rerank_score"] = item.get("relevance", 0.0)
                result_item["original_rank"] = rank
                result_item["rank"] = rank
                results.append(result_item)
            return results, trace

        start_time = time.perf_counter()

        # 提取文本对
        passages = [str(item.get(content_key, "")) for item in candidates]
        scores = self._compute_scores(query, passages)

        # 合并分数并排序
        scored_items = []
        for i, (item, score) in enumerate(zip(candidates, scores)):
            result_item = dict(item)
            result_item["original_score"] = item.get("relevance", 0.0)
            result_item["rerank_score"] = float(score)
            result_item["original_rank"] = i + 1
            scored_items.append(result_item)

        # 按 rerank_score 降序排序
        scored_items.sort(key=lambda x: x["rerank_score"], reverse=True)

        # 分数阈值过滤
        if self.score_threshold is not None:
            scored_items = [
                item for item in scored_items
                if item["rerank_score"] >= self.score_threshold
            ]

        # 分配排名
        results = []
        for rank, item in enumerate(scored_items[:top_k], start=1):
            item["rank"] = rank
            item["retrieval_strategy"] = "reranked"
            results.append(item)

        latency = (time.perf_counter() - start_time) * 1000
        trace.update({
            "reranker_applied": True,
            "latency_ms": round(latency, 2),
            "output_count": len(results),
            "score_range": {
                "min": round(min(scores), 4) if scores else 0,
                "max": round(max(scores), 4) if scores else 0,
                "avg": round(sum(scores) / len(scores), 4) if scores else 0,
            },
        })

        return results, trace

    def _compute_scores(self, query: str, passages: List[str]) -> List[float]:
        """计算 query-passage 对的分数"""
        if self.mode == "local" and self._model:
            return self._compute_local(query, passages)
        elif self.mode == "api":
            return self._compute_api(query, passages)
        else:
            return [0.0] * len(passages)

    def _compute_local(self, query: str, passages: List[str]) -> List[float]:
        """本地推理"""
        try:
            input_pairs = [[query, passage] for passage in passages]
            scores = self._model.predict(
                input_pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )
            return [float(s) for s in scores]
        except Exception as e:
            logger.error(f"Reranker 本地推理失败: {e}")
            return [0.0] * len(passages)

    def _compute_api(self, query: str, passages: List[str]) -> List[float]:
        """API 调用"""
        import requests

        url = self.api_url.rstrip("/")
        if not url.endswith("/rerank"):
            url = f"{url}/rerank"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "query": query,
            "documents": passages,
            "top_n": len(passages),
            "return_documents": False,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # 兼容不同 API 格式
            if "results" in data:
                # Pinecone / vLLM 格式
                results = data["results"]
                scores = [0.0] * len(passages)
                for item in results:
                    idx = item.get("index", item.get("corpus_id", 0))
                    score = item.get("score", 0.0)
                    if 0 <= idx < len(passages):
                        scores[idx] = float(score)
                return scores
            elif "scores" in data:
                return [float(s) for s in data["scores"]]
            else:
                logger.warning(f"未知 API 响应格式: {list(data.keys())}")
                return [0.0] * len(passages)
        except Exception as e:
            logger.error(f"Reranker API 调用失败: {e}")
            return [0.0] * len(passages)

    def get_info(self) -> Dict[str, Any]:
        """获取 Reranker 信息"""
        return {
            "class": "BGEReranker",
            "mode": self.mode,
            "model": self.model_name,
            "available": self._available,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "score_threshold": self.score_threshold,
        }


# ============================================================
# 全局实例
# ============================================================

def get_reranker(**kwargs) -> BGEReranker:
    """获取 Reranker 实例（工厂函数）"""
    return BGEReranker(**kwargs)


# 默认 Reranker（auto 模式）
default_reranker = BGEReranker(mode="auto")
