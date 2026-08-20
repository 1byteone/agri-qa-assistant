"""
CropWise BGE-M3 Embedding 函数
================================

替换 LocalHashingEmbeddingFunction，提供高质量农业语义嵌入。

支持两种模式：
1. 本地推理（需要 GPU + sentence-transformers）
2. API 调用（兼容 OpenAI / HuggingFace TEI / 自定义端点）

模型：BAAI/bge-m3
- 1024 维稠密向量
- 支持 100+ 语言
- 最大 8192 token 上下文
- 同时输出 Dense + Sparse + ColBERT 多向量
"""

from __future__ import annotations
import os
import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BGEM3EmbeddingFunction:
    """
    BGE-M3 Embedding 函数（ChromaDB 兼容接口）。

    模式：
    - local: 本地 sentence-transformers 推理
    - api: 远程 API 调用（OpenAI 兼容格式）
    """

    dimension = 1024

    def __init__(
        self,
        mode: str = "api",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 32,
        max_length: int = 8192,
        device: str = "cpu",
    ):
        """
        初始化 BGE-M3 Embedding 函数。

        Args:
            mode: "local" 或 "api"
            api_url: API 端点 URL（mode="api" 时必填）
            api_key: API 密钥
            model_name: 模型名称
            batch_size: 批量大小
            max_length: 最大 token 长度
            device: 推理设备（local 模式）
        """
        self.mode = mode
        self.api_url = api_url or os.getenv("BGE_M3_API_URL", "")
        self.api_key = api_key or os.getenv("BGE_M3_API_KEY", "")
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = device
        self._model = None

        if mode == "local":
            self._init_local_model()
        elif mode == "api" and not self.api_url:
            logger.warning(
                "BGE-M3 API 模式未配置 API URL，将回退到本地哈希 Embedding。"
                "请设置 BGE_M3_API_URL 环境变量。"
            )
        else:
            logger.info(f"BGE-M3 Embedding 初始化完成 (mode={mode}, model={model_name})")

    def _init_local_model(self):
        """初始化本地模型"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"加载 BGE-M3 模型: {self.model_name} (device={device})")
            self._model = SentenceTransformer(
                self.model_name,
                device=device,
                trust_remote_code=True,
            )
            logger.info(f"BGE-M3 模型加载成功，维度: {self.dimension}")
        except ImportError:
            logger.warning(
                "sentence-transformers 未安装。运行: pip install sentence-transformers"
            )
            self.mode = "unavailable"
        except Exception as e:
            logger.error(f"BGE-M3 模型加载失败: {e}")
            self.mode = "unavailable"

    def _encode_local(self, texts: List[str]) -> List[List[float]]:
        """本地推理"""
        if self._model is None:
            return []
        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [emb.tolist() for emb in embeddings]

    def _encode_api(self, texts: List[str]) -> List[List[float]]:
        """API 调用（OpenAI 兼容格式）"""
        import requests

        if not self.api_url:
            logger.error("BGE-M3 API URL 未配置")
            return []

        url = self.api_url.rstrip("/")
        if not url.endswith("/embeddings"):
            url = f"{url}/v1/embeddings" if "/v1" not in url else f"{url}/embeddings"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        all_embeddings = []

        # 分批调用
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            payload = {
                "model": self.model_name,
                "input": batch,
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                batch_embeddings = [
                    item["embedding"]
                    for item in sorted(data["data"], key=lambda x: x["index"])
                ]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"BGE-M3 API 调用失败: {e}")
                all_embeddings.extend([[] for _ in batch])

        return all_embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表（ChromaDB 接口）"""
        if self.mode == "local" and self._model:
            return self._encode_local(texts)
        elif self.mode == "api" and self.api_url:
            return self._encode_api(texts)
        else:
            logger.warning("BGE-M3 不可用，使用哈希回退")
            return self._hash_fallback(texts)

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询（ChromaDB 接口）"""
        results = self.embed_documents([text])
        return results[0] if results else []

    def __call__(self, input: List[str]) -> List[List[float]]:
        """兼容直接调用"""
        return self.embed_documents(input)

    def _hash_fallback(self, texts: List[str]) -> List[List[float]]:
        """哈希回退（当 BGE-M3 不可用时）"""
        import hashlib
        dimension = self.dimension
        results = []
        for text in texts:
            vector = [0.0] * dimension
            compact = re.sub(r"\s+", "", text.lower())
            tokens = re.findall(r"[a-z0-9]+", text.lower())
            tokens.extend(compact[i:i + 2] for i in range(max(0, len(compact) - 1)))
            for token in tokens:
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, "big")
                index = value % dimension
                vector[index] += -1.0 if value & 1 else 1.0
            norm = sum(v * v for v in vector) ** 0.5 or 1.0
            results.append([v / norm for v in vector])
        return results

    def get_info(self) -> Dict[str, Any]:
        """获取 Embedding 函数信息"""
        return {
            "class": "BGEM3EmbeddingFunction",
            "mode": self.mode,
            "model": self.model_name,
            "dimension": self.dimension,
            "max_length": self.max_length,
            "api_url": self.api_url or "未配置",
            "model_loaded": self._model is not None,
        }
