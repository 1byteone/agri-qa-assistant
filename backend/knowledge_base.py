import os
import logging
import hashlib
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import requests
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)


class LocalHashingEmbeddingFunction:
    """Dependency-free Chinese-friendly vector fallback for local RAG operation."""

    dimension = 384

    def _tokens(self, text: str) -> List[str]:
        compact = re.sub(r"\s+", "", text.lower())
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        tokens.extend(compact[index:index + 2] for index in range(max(0, len(compact) - 1)))
        return tokens or [compact]

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        for token in self._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimension
            vector[index] += -1.0 if value & 1 else 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed_documents(input)


class BGEEmbeddingFunction:
    """BGE-M3 Embedding 函数，优先使用 BGE-M3 API，不可用时回退到本地哈希。

    配置方式：
    - RAG_EMBEDDING_MODE=bge_m3  → 使用 BGE-M3
    - RAG_EMBEDDING_MODE=local   → 使用本地哈希（默认）
    - RAG_EMBEDDING_MODE=remote  → 使用 Agnes AI

    环境变量：
    - BGE_M3_API_URL: BGE-M3 API 地址
    - BGE_M3_API_KEY: BGE-M3 API 密钥
    """

    dimension = 1024

    def __init__(self):
        self._bge_instance = None
        self._fallback = LocalHashingEmbeddingFunction()
        self._init_bge()

    def _init_bge(self):
        try:
            from retrieval.bge_m3_embedding import BGEM3EmbeddingFunction
            api_url = os.getenv("BGE_M3_API_URL", "")
            api_key = os.getenv("BGE_M3_API_KEY", "")
            mode = "api" if api_url else "local"
            self._bge_instance = BGEM3EmbeddingFunction(
                mode=mode,
                api_url=api_url,
                api_key=api_key,
            )
            if self._bge_instance.mode == "unavailable":
                logger.warning("BGE-M3 不可用，使用本地哈希回退")
                self._bge_instance = None
            else:
                logger.info(f"BGE-M3 嵌入初始化成功 (mode={mode})")
        except ImportError:
            logger.info("BGE-M3 模块未安装，使用本地哈希")
            self._bge_instance = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._bge_instance:
            try:
                return self._bge_instance.embed_documents(texts)
            except Exception as e:
                logger.warning(f"BGE-M3 嵌入失败，回退到哈希: {e}")
        return self._fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if self._bge_instance:
            try:
                return self._bge_instance.embed_query(text)
            except Exception as e:
                logger.warning(f"BGE-M3 嵌入失败，回退到哈希: {e}")
        return self._fallback.embed_query(text)

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed_documents(input)


class AgnesEmbeddingFunction:
    """自定义 Embedding 函数，直接调用 Agnes AI，绕过 tiktoken。"""

    def __init__(self):
        self.api_key = settings.agnes_api_key
        base_url = settings.agnes_base_url.rstrip("/")
        # 兼容 base_url 已带 /v1 的情况
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        self.base_url = base_url
        self.model = settings.agnes_embedding_model

    def _call_api(self, input: List[str]) -> List[List[float]]:
        if not input:
            return []

        url = f"{self.base_url}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": input}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        except Exception as e:
            logger.error(f"获取 Embedding 失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Chroma 文档嵌入接口"""
        return self._call_api(texts)

    def embed_query(self, text: str) -> List[float]:
        """Chroma 查询嵌入接口"""
        return self._call_api([text])[0]

    def __call__(self, input: List[str]) -> List[List[float]]:
        """兼容直接调用"""
        return self.embed_documents(input)


class KnowledgeBase:
    """农业领域私有知识库（ChromaDB + BM25 混合检索）"""

    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        self.embedding_mode = settings.rag_embedding_mode.lower()
        if self.embedding_mode not in {"local", "remote", "bge_m3"}:
            raise ValueError("RAG_EMBEDDING_MODE 必须为 local / remote / bge_m3")
        self.collection_name = f"agri_knowledge_{self.embedding_mode}_v1"

        # 嵌入函数选择
        if self.embedding_mode == "bge_m3":
            self.embedding_fn = BGEEmbeddingFunction()
        elif self.embedding_mode == "local":
            self.embedding_fn = LocalHashingEmbeddingFunction()
        else:
            self.embedding_fn = AgnesEmbeddingFunction()

        self._vectorstore: Optional[Chroma] = None
        self._bm25_retriever = None
        self._bm25_indexed = False
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

    def _get_vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_dir,
                embedding_function=self.embedding_fn,
            )
        return self._vectorstore

    def add_documents(self, documents: List[Document]) -> int:
        """添加文档到知识库"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "；", " ", ""],
        )
        chunks = text_splitter.split_documents(documents)

        vectorstore = self._get_vectorstore()
        vectorstore.add_documents(chunks)
        return len(chunks)

    def ingest_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Chunk, embed and persist one approved document with hash-based dedupe."""
        metadata = dict(metadata or {})
        content_hash = str(metadata.get("content_hash", ""))
        vectorstore = self._get_vectorstore()
        if content_hash:
            existing = vectorstore.get(where={"content_hash": content_hash}, include=["metadatas"])
            existing_ids = existing.get("ids", [])
            existing_metadata = existing.get("metadatas", [])
            if existing_ids:
                if all(item and all(item.get(key) == value for key, value in metadata.items()) for item in existing_metadata):
                    return {"added_chunks": 0, "duplicate": True, "content_hash": content_hash}
                # Preserve idempotency while allowing a verified source record
                # to gain new governance metadata such as evidence_scope.
                vectorstore.delete(ids=existing_ids)
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "；", " ", ""],
        ).split_documents([Document(page_content=text, metadata=metadata)])
        if not chunks:
            return {"added_chunks": 0, "duplicate": False, "content_hash": content_hash}
        vectorstore.add_documents(chunks)
        return {"added_chunks": len(chunks), "duplicate": False, "content_hash": content_hash}

    def remove_by_content_hash(self, content_hash: str) -> int:
        """Remove one imported document version for an explicit evidence rollback."""
        if not content_hash:
            return 0
        vectorstore = self._get_vectorstore()
        matches = vectorstore.get(where={"content_hash": content_hash}, include=[])
        ids = matches.get("ids", [])
        if ids:
            vectorstore.delete(ids=ids)
        return len(ids)

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> int:
        """添加纯文本到知识库"""
        documents = [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(texts, metadatas or [{}] * len(texts))
        ]
        return self.add_documents(documents)

    @staticmethod
    def choose_strategy(query: str) -> str:
        text = (query or "").lower()
        if re.search(r"政策|标准|规范|文件|编号|产品型号|id", text):
            return "hybrid-metadata"
        if re.search(r"第几天|什么时候|去年|上周|最近|农时|播期|生育期", text):
            return "hybrid-temporal"
        return "hybrid"

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        compact = re.sub(r"\s+", "", (query or "").lower())
        terms = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", compact)
        bigrams = [compact[index:index + 2] for index in range(max(0, len(compact) - 1))]
        return list(dict.fromkeys(terms + bigrams))

    @staticmethod
    def _metadata_boost(metadata: Dict[str, Any], query: str) -> float:
        """Small evidence-quality boost; it never overrides textual match."""
        compact = (query or "").lower()
        boost = 0.0
        if "江西" in compact and str(metadata.get("region", "")) == "江西":
            boost += 0.08
        if any(word in compact for word in ("政策", "规范", "标准", "官方")) and metadata.get("source"):
            boost += 0.05
        if any(word in compact for word in ("病", "虫", "症状", "防治")) and metadata.get("category") == "pest":
            boost += 0.05
        return boost

    def search(self, query: str, top_k: int = 5, max_distance: float = 1.7, strategy: str = "hybrid") -> List[Dict[str, Any]]:
        """Hybrid retrieval: vector candidates + Chinese lexical rerank + metadata quality."""
        vectorstore = self._get_vectorstore()
        # Retrieve a wider candidate set, then apply a small lexical signal.
        # The local hashing embedding is deterministic and offline, but Chinese
        # short queries can otherwise rank a semantically unrelated chunk above
        # an exact crop/disease match.
        results = vectorstore.similarity_search_with_score(query, k=max(top_k, 12))
        query_terms = self._query_terms(query)

        def lexical_overlap(text: str) -> float:
            compact_query = re.sub(r"\s+", "", (query or "").lower())
            compact_text = re.sub(r"\s+", "", (text or "").lower())
            if not compact_query or not compact_text:
                return 0.0
            if compact_query in compact_text:
                return 1.0
            query_bigrams = {compact_query[i:i + 2] for i in range(max(0, len(compact_query) - 1))}
            if not query_bigrams:
                return 0.0
            return len(query_bigrams & {
                compact_text[i:i + 2] for i in range(max(0, len(compact_text) - 1))
            }) / len(query_bigrams)

        filtered = []
        for doc, distance in results:
            if distance <= max_distance:
                vector_relevance = max(0.0, 1.0 - float(distance) / 2)
                lexical_relevance = lexical_overlap(doc.page_content)
                if strategy == "vector":
                    relevance = vector_relevance
                else:
                    text = re.sub(r"\s+", "", doc.page_content.lower())
                    term_hits = sum(1 for term in query_terms if term in text)
                    bm25_signal = min(1.0, term_hits / max(1, min(len(query_terms), 8)))
                    relevance = min(1.0, 0.52 * vector_relevance + 0.33 * max(lexical_relevance, bm25_signal) + self._metadata_boost(doc.metadata, query))
                filtered.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "distance": float(distance),
                        "relevance": relevance,
                        "score_breakdown": {
                            "vector": round(vector_relevance, 4),
                            "lexical": round(lexical_relevance, 4),
                            "metadata": round(self._metadata_boost(doc.metadata, query), 4),
                        },
                        "_rank_score": relevance,
                        "retrieval_strategy": strategy,
                    })
        filtered.sort(key=lambda item: item["_rank_score"], reverse=True)
        for item in filtered:
            item.pop("_rank_score", None)
        return filtered[:top_k]

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        max_distance: float = 1.7,
        use_bm25: bool = True,
        use_reranker: bool = True,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60,
    ) -> Dict[str, Any]:
        """
        真正的混合检索：Vector + BM25 + RRF + Reranker。

        Returns:
            Dict with keys: results, trace
        """
        import time
        trace = {
            "query": query,
            "strategy": "hybrid_rrf_rerank",
            "branches": {},
            "rrf_k": rrf_k,
        }

        # ---- Vector Branch ----
        vector_start = time.perf_counter()
        vector_results = self.search(query, top_k=top_k * 3, max_distance=max_distance, strategy="vector")
        vector_latency = (time.perf_counter() - vector_start) * 1000
        trace["branches"]["vector"] = {
            "candidates": len(vector_results),
            "latency_ms": round(vector_latency, 2),
            "weight": vector_weight,
        }

        if not use_bm25:
            trace["rrf_applied"] = False
            return {"results": vector_results[:top_k], "trace": trace}

        # ---- BM25 Branch ----
        bm25_start = time.perf_counter()
        bm25_results = self._bm25_search(query, top_k=top_k * 3)
        bm25_latency = (time.perf_counter() - bm25_start) * 1000
        trace["branches"]["bm25"] = {
            "candidates": len(bm25_results),
            "latency_ms": round(bm25_latency, 2),
            "weight": bm25_weight,
        }

        # ---- RRF Fusion ----
        rrf_start = time.perf_counter()
        try:
            from retrieval.rrf_fusion import RRFFusion
            fusion = RRFFusion(k=rrf_k, weights={"vector": vector_weight, "bm25": bm25_weight})
            ranked_lists = {}
            if vector_results:
                ranked_lists["vector"] = vector_results
            if bm25_results:
                ranked_lists["bm25"] = bm25_results

            if len(ranked_lists) > 1:
                fused_results, rrf_trace = fusion.fuse_with_trace(
                    ranked_lists,
                    content_key="content",
                    score_key="relevance",
                )
                trace["rrf_applied"] = True
                trace["rrf_trace"] = rrf_trace
            elif ranked_lists:
                fused_results = list(ranked_lists.values())[0]
                trace["rrf_applied"] = False
                trace["rrf_reason"] = "single_branch"
            else:
                fused_results = []
                trace["rrf_applied"] = False
                trace["rrf_reason"] = "no_results"
        except ImportError:
            fused_results = self._simple_fusion(vector_results, bm25_results, vector_weight, bm25_weight)
            trace["rrf_applied"] = False
            trace["rrf_reason"] = "import_error"

        rrf_latency = (time.perf_counter() - rrf_start) * 1000
        trace["rrf_latency_ms"] = round(rrf_latency, 2)

        # ---- Reranker ----
        rerank_latency = 0
        if use_reranker and fused_results:
            try:
                from retrieval.reranker import default_reranker
                rerank_start = time.perf_counter()
                reranked_results, rerank_trace = default_reranker.rerank(
                    query, fused_results, top_k=top_k,
                )
                rerank_latency = (time.perf_counter() - rerank_start) * 1000
                trace["reranker"] = rerank_trace
                trace["total_latency_ms"] = round(vector_latency + bm25_latency + rrf_latency + rerank_latency, 2)
                trace["final_count"] = len(reranked_results)
                return {"results": reranked_results, "trace": trace}
            except Exception as e:
                logger.warning(f"Reranker 失败，回退到 RRF 结果: {e}")
                trace["reranker"] = {"reranker_applied": False, "error": str(e)}

        # 回退：直接使用 RRF 结果
        trace["reranker"] = {"reranker_applied": False, "reason": "disabled_or_unavailable"}
        trace["total_latency_ms"] = round(vector_latency + bm25_latency + rrf_latency, 2)
        trace["final_count"] = len(fused_results[:top_k])

        return {"results": fused_results[:top_k], "trace": trace}

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """BM25 检索（懒加载索引）"""
        try:
            from retrieval.bm25_retriever import BM25Retriever
            if self._bm25_retriever is None:
                self._bm25_retriever = BM25Retriever()

            # 懒加载：第一次使用时从 ChromaDB 构建 BM25 索引
            if not self._bm25_indexed:
                self._build_bm25_index()

            results = self._bm25_retriever.search(query, top_k=top_k)
            return [
                {
                    "content": r.content,
                    "metadata": r.metadata,
                    "relevance": r.score,
                    "retrieval_strategy": "bm25",
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"BM25 检索失败: {e}")
            return []

    def _build_bm25_index(self):
        """从 ChromaDB 构建 BM25 索引"""
        try:
            from retrieval.bm25_retriever import BM25Retriever
            vectorstore = self._get_vectorstore()
            # 获取所有文档
            collection = vectorstore._collection
            data = collection.get(include=["documents", "metadatas"])
            documents = []
            for doc_text, meta in zip(data.get("documents", []), data.get("metadatas", [])):
                documents.append({"content": doc_text, "metadata": meta or {}})

            if documents:
                self._bm25_retriever = BM25Retriever()
                self._bm25_retriever.build_index(documents)
                self._bm25_indexed = True
                logger.info(f"BM25 索引构建完成: {len(documents)} 篇文档")
        except Exception as e:
            logger.warning(f"BM25 索引构建失败: {e}")

    def _simple_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        vector_weight: float,
        bm25_weight: float,
    ) -> List[Dict[str, Any]]:
        """简单加权融合（RRF 不可用时的回退）"""
        doc_scores: Dict[str, float] = {}
        doc_data: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(vector_results):
            key = item.get("content", "")[:200]
            doc_scores[key] = doc_scores.get(key, 0) + vector_weight / (1 + rank)
            if key not in doc_data:
                doc_data[key] = item

        for rank, item in enumerate(bm25_results):
            key = item.get("content", "")[:200]
            doc_scores[key] = doc_scores.get(key, 0) + bm25_weight / (1 + rank)
            if key not in doc_data:
                doc_data[key] = item

        sorted_keys = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)
        results = []
        for key in sorted_keys:
            item = dict(doc_data[key])
            item["rrf_score"] = doc_scores[key]
            results.append(item)
        return results

    def get_status(self) -> Dict[str, Any]:
        """获取知识库状态"""
        try:
            vectorstore = self._get_vectorstore()
            count = vectorstore._collection.count()
            bm25_stats = {}
            if self._bm25_retriever and self._bm25_indexed:
                bm25_stats = self._bm25_retriever.get_stats()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_dir": self.persist_dir,
                "embedding_mode": self.embedding_mode,
                "bm25_indexed": self._bm25_indexed,
                "bm25_stats": bm25_stats,
            }
        except Exception as e:
            logger.error(f"获取知识库状态失败: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "embedding_mode": self.embedding_mode,
                "error": str(e),
            }

    def clear(self):
        """清空知识库"""
        try:
            import shutil
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
            self._vectorstore = None
            self._ensure_db_dir()
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")


# 全局知识库实例
knowledge_base = KnowledgeBase()


def init_default_knowledge_base():
    """初始化默认农业知识库"""
    default_docs = [
        # 作物种植
        Document(
            page_content="水稻种植技术：水稻喜高温、多湿、短日照，对土壤要求不严。播种前需进行种子处理，包括晒种、选种、浸种催芽。插秧时每穴3-5株苗，行距30cm，株距20cm。分蘖期保持浅水层，抽穗期保持3-5cm水层，成熟期适时排水晒田。",
            metadata={"category": "crop", "crop": "水稻", "topic": "planting"}
        ),
        Document(
            page_content="小麦种植技术：小麦适应性强，耐寒耐旱。播种前深耕细耙，施足底肥。播种深度3-5cm，播种量每亩15-20kg。返青期追施拔节肥，抽穗期防治锈病和白粉病，成熟期及时收获。",
            metadata={"category": "crop", "crop": "小麦", "topic": "planting"}
        ),
        Document(
            page_content="玉米种植技术：玉米喜温，种子发芽最低温度8-10℃。播种深度5-6cm，亩保苗3500-4000株。拔节期追施穗肥，大喇叭口期防治玉米螟，抽雄期遇高温干旱需灌溉。",
            metadata={"category": "crop", "crop": "玉米", "topic": "planting"}
        ),
        # 病虫害防治
        Document(
            page_content="水稻稻飞虱防治：稻飞虱分白背飞虱、褐飞虱和灰飞虱。防治适期为若虫盛发期，可用吡虫啉、噻虫嗪等药剂喷雾。同时保护田间蜘蛛、青蛙等天敌。",
            metadata={"category": "pest", "crop": "水稻", "pest": "稻飞虱", "topic": "control"}
        ),
        Document(
            page_content="小麦锈病防治：小麦锈病分条锈病、叶锈病和秆锈病。防治策略：选用抗病品种，合理密植，增施磷钾肥。药剂防治可用戊唑醇、三唑酮等，在发病初期喷雾。",
            metadata={"category": "pest", "crop": "小麦", "pest": "锈病", "topic": "control"}
        ),
        Document(
            page_content="玉米螟防治：玉米螟是玉米主要害虫，幼虫钻蛀茎秆和果穗。防治方法：心叶期用苏云金杆菌(Bt)制剂颗粒剂撒入心叶；喇叭口期用辛硫磷颗粒剂灌心；生物防治释放赤眼蜂。",
            metadata={"category": "pest", "crop": "玉米", "pest": "玉米螟", "topic": "control"}
        ),
        Document(
            page_content="蚜虫综合防治：蚜虫可危害小麦、玉米、蔬菜等多种作物。农业防治：清除杂草，合理密植。物理防治：黄色粘虫板诱杀。生物防治：释放蚜茧蜂、瓢虫。化学防治：吡虫啉、啶虫脒喷雾。",
            metadata={"category": "pest", "topic": "control"}
        ),
        # 肥料施用
        Document(
            page_content="氮磷钾肥施用原则：氮肥促进茎叶生长，磷肥促进根系发育和开花结果，钾肥增强抗逆性。施肥原则：有机肥为主，化肥为辅；氮磷钾配合，适量补充微肥。水稻分蘖期施氮肥，孕穗期补钾；小麦拔节期追氮，抽穗前喷磷酸二氢钾。",
            metadata={"category": "fertilizer", "topic": "npk"}
        ),
        Document(
            page_content="测土配方施肥：根据土壤化验结果和作物需肥特性，制定施肥方案。步骤：1.取土样检测；2.确定目标产量；3.计算养分需求量；4.确定肥料品种和用量；5.调整施肥方法。可减少化肥用量10-20%，提高产量5-15%。",
            metadata={"category": "fertilizer", "topic": "soil_testing"}
        ),
        Document(
            page_content="叶面肥施用技术：叶面肥可作为根部施肥的补充。适宜时期：作物生长后期、根系吸收能力下降时、出现缺素症时。常用叶面肥：尿素(0.5-1%)、磷酸二氢钾(0.3%)、硼砂(0.1-0.2%)。喷施时间：傍晚或阴天，避开高温。",
            metadata={"category": "fertilizer", "topic": "foliar"}
        ),
        # 土壤管理
        Document(
            page_content="土壤改良技术：酸性土壤施用石灰调节pH值至6.0-7.0；盐碱地增施有机肥、种植耐盐作物；黏重土壤掺沙改良质地；沙质土壤增施有机肥提高保水保肥能力。深翻深度20-30cm，打破犁底层。",
            metadata={"category": "soil", "topic": "amendment"}
        ),
        Document(
            page_content="节水灌溉技术：水稻浅水勤灌，亩均用水量300-400m³；小麦玉米滴灌亩均用水量150-200m³，比漫灌节水50%以上。推广喷灌、微喷灌、水肥一体化技术。灌溉水质标准：pH 5.5-8.5，含盐量<1g/L。",
            metadata={"category": "irrigation", "topic": "water_saving"}
        ),
        # 农机具
        Document(
            page_content="旋耕机使用与维护：旋耕机适用于水旱田整地，耕深12-18cm。使用前检查刀片是否紧固，齿轮箱油位是否正常。作业时先结合动力输出轴，再缓慢降落，严禁急转弯。每工作50小时更换齿轮箱润滑油，季节性作业后彻底清洗保养。",
            metadata={"category": "machinery", "topic": "tillage"}
        ),
        Document(
            page_content="植保无人机操作规范：植保无人机适用于病虫害防治和叶面施肥。作业前检查电池电量、药箱密封性、喷头是否堵塞。飞行高度距作物冠层2-3米，飞行速度3-5米/秒。避免在高温(>35℃)、大风(>4级)、降雨天气作业。作业后清洗药箱、滤网和喷头。",
            metadata={"category": "machinery", "topic": "spraying"}
        ),
        # 江西农业大学重点知识域（本地可核验的基础知识包）
        Document(
            page_content="江西家猪遗传育种基础：家猪育种应先明确繁殖性能、生长速度、料肉比和胴体品质等目标，建立可追溯的系谱和生产记录。选择亲本需结合健康状况、近交风险和多性状综合育种值，配种前进行疫病检测；具体品种和配方应由动物遗传育种与兽医人员依据群体数据复核。",
            metadata={"category": "jiangxi_focus", "topic": "pig_breeding", "region": "江西", "source": "CropWise江农专题基础知识包"}
        ),
        Document(
            page_content="鄱阳湖流域农业生态基础：鄱阳湖周边农田管理要兼顾稻作生产、湿地和水质保护。施肥应以测土结果为依据，严格控制氮磷流失；灌排沟渠设置缓冲带，农药按登记作物和安全间隔使用，暴雨或湖区水位变化前应做好排水与污染风险巡查。",
            metadata={"category": "jiangxi_focus", "topic": "poyang_ecology", "region": "江西", "source": "CropWise江农专题基础知识包"}
        ),
        Document(
            page_content="赣南脐橙采后保鲜基础：采收应选择成熟度适宜、无机械伤的果实，分级后及时预冷、清洁和通风贮藏。包装和运输要避免挤压、日晒及温度剧烈波动，定期检查腐烂果；保鲜剂和处理浓度必须符合现行登记、标签及食品安全要求，不能仅凭外观图片判断品质或病害。",
            metadata={"category": "jiangxi_focus", "topic": "gannan_orange_postharvest", "region": "江西", "source": "CropWise江农专题基础知识包"}
        ),
        Document(
            page_content="江西双季稻生产要点：早稻和晚稻应根据当地积温、无霜期和水源条件安排播期，育秧、移栽密度和水肥管理需要结合品种熟期与田块条件。遇寒潮、暴雨或高温，应优先参考江西气象预警和当地农技部门意见，不能用单一日期替代区域化农时判断。",
            metadata={"category": "jiangxi_focus", "topic": "double_crop_rice", "region": "江西", "source": "CropWise江农专题基础知识包"}
        ),
        Document(
            page_content="江西现代农业装备与植保：植保无人机作业前应核验登记药剂、飞防区域、风速和周边敏感目标，作业中保持稳定高度与航线，作业后清洗设备并留存药剂和地块记录。涉及学校试验田、饮用水源或大面积病虫害时，应由植保和农机专业人员现场复核。",
            metadata={"category": "jiangxi_focus", "topic": "agri_equipment", "region": "江西", "source": "CropWise江农专题基础知识包"}
        ),
    ]

    kb = knowledge_base
    current_count = kb.get_status()["total_documents"]
    if current_count == 0:
        added = kb.add_documents(default_docs)
        logger.info(f"默认农业知识库初始化完成，添加 {added} 个文档片段")
    else:
        # Existing installations receive the Jiangxi focus pack exactly once.
        existing = kb._get_vectorstore().get(include=["metadatas"]).get("metadatas", [])
        has_focus_pack = any(meta and meta.get("source") == "CropWise江农专题基础知识包" for meta in existing)
        if not has_focus_pack:
            focus_docs = [doc for doc in default_docs if doc.metadata.get("category") == "jiangxi_focus"]
            added = kb.add_documents(focus_docs)
            logger.info(f"已补充江农专题知识包，添加 {added} 个文档片段")
        else:
            logger.info(f"知识库已存在 {current_count} 个文档片段，跳过初始化")
