"""
CropWise BM25 关键词检索器
============================

基于 rank_bm25 实现的中文农业术语关键词检索。
支持自定义分词器和农业专业词典。

BM25 公式：
  score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))

参考：
- rank_bm25: 轻量级 BM25 Python 实现
- 适配中文农业文档：自定义分词 + 农业术语词典
"""

from __future__ import annotations
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================
# 中文农业分词器
# ============================================================

# 农业专业词典（高频术语，优先匹配）
AGRI_TERMS = [
    # 作物
    "水稻", "早稻", "晚稻", "双季稻", "小麦", "冬小麦", "春小麦", "玉米", "油菜",
    "脐橙", "赣南脐橙", "大豆", "棉花", "茶叶", "蔬菜", "柑橘",
    # 病虫害
    "稻瘟病", "纹枯病", "白叶枯病", "赤霉病", "锈病", "溃疡病", "炭疽病", "菌核病",
    "稻飞虱", "稻纵卷叶螟", "二化螟", "三化螟", "玉米螟", "蚜虫", "菜青虫", "红蜘蛛",
    "柑橘木虱", "棉铃虫",
    # 农药
    "吡虫啉", "噻虫嗪", "戊唑醇", "三唑酮", "氯虫苯甲酰胺", "阿维菌素",
    "井冈霉素", "春雷霉素", "代森锰锌", "苏云金杆菌",
    # 肥料
    "尿素", "磷酸二氢钾", "复合肥", "有机肥", "叶面肥", "硼砂",
    # 技术
    "测土配方", "节水灌溉", "滴灌", "喷灌", "水肥一体化", "浅水勤灌",
    "晒田", "浸种催芽", "插秧", "分蘖", "拔节", "孕穗", "抽穗", "灌浆",
    # 生育期
    "播种期", "秧田期", "移栽期", "分蘖期", "拔节期", "孕穗期", "抽穗期", "灌浆期", "成熟期",
    # 症状
    "叶尖干枯", "叶片黄化", "褐色斑点", "白穗", "倒伏", "卷叶", "虫蛀茎秆",
    "果实溃疡", "根腐", "萎蔫",
    # 地区
    "江西省", "南昌市", "赣州市", "上饶市", "吉安市", "宜春市", "抚州市",
    "九江市", "萍乡市", "景德镇市", "新余市", "鹰潭市",
    # 政策
    "农机补贴", "种粮补贴", "农业保险", "高标准农田", "农业机械化",
]


class ChineseAgriculturalTokenizer:
    """中文农业文本分词器"""

    def __init__(self, custom_terms: Optional[List[str]] = None):
        """
        初始化分词器。

        Args:
            custom_terms: 额外的自定义术语（会追加到内置词典）
        """
        self.terms = sorted(AGRI_TERMS + (custom_terms or []), key=len, reverse=True)
        # 预编译正则
        self._term_pattern = re.compile("|".join(re.escape(t) for t in self.terms))

    def tokenize(self, text: str) -> List[str]:
        """
        分词：先匹配农业术语，再用 bigram 兜底。

        策略：
        1. 优先匹配长农业术语（最长匹配）
        2. 未匹配部分用 bigram 切分
        3. 过滤停用词和单字符
        """
        if not text:
            return []

        tokens = []
        remaining = text.lower()
        last_end = 0

        # 长农业术语优先匹配
        for match in self._term_pattern.finditer(remaining):
            start, end = match.span()
            # 添加匹配前的 bigram
            if start > last_end:
                pre_text = remaining[last_end:start]
                tokens.extend(self._bigram_tokenize(pre_text))
            tokens.append(match.group())
            last_end = end

        # 处理尾部
        if last_end < len(remaining):
            tokens.extend(self._bigram_tokenize(remaining[last_end:]))

        # 去重但保留顺序
        seen = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen and len(token) >= 2:
                seen.add(token)
                unique_tokens.append(token)

        return unique_tokens

    def _bigram_tokenize(self, text: str) -> List[str]:
        """bigram 分词"""
        # 只保留中文和英文数字
        compact = re.sub(r"[^a-z0-9一-鿿]", "", text.lower())
        if not compact:
            return []
        tokens = []
        # 中文 bigram
        chinese_chars = re.findall(r"[一-鿿]+", compact)
        for segment in chinese_chars:
            for i in range(len(segment) - 1):
                tokens.append(segment[i:i + 2])
        # 英文数字 token
        alpha_tokens = re.findall(r"[a-z0-9]{2,}", compact)
        tokens.extend(alpha_tokens)
        return tokens


# ============================================================
# BM25 检索器
# ============================================================

@dataclass
class BM25Result:
    """BM25 检索结果"""
    content: str
    metadata: Dict[str, Any]
    score: float
    rank: int
    retrieval_strategy: str = "bm25"


class BM25Retriever:
    """
    BM25 关键词检索器。

    支持：
    - 中文农业术语分词
    - 可配置的 k1/b 参数
    - 元数据过滤
    - 与 Vector 检索结果融合（用于 RRF）
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Optional[ChineseAgriculturalTokenizer] = None,
    ):
        """
        初始化 BM25 检索器。

        Args:
            k1: BM25 k1 参数（词频饱和度，通常 1.2-2.0）
            b: BM25 b 参数（文档长度归一化，通常 0.5-0.8）
            tokenizer: 自定义分词器
        """
        self.k1 = k1
        self.b = b
        self.tokenizer = tokenizer or ChineseAgriculturalTokenizer()
        self._documents: List[Dict[str, Any]] = []
        self._tokenized_docs: List[List[str]] = []
        self._doc_lengths: List[int] = []
        self._avg_doc_length: float = 0.0
        self._idf: Dict[str, float] = {}
        self._built = False

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        构建 BM25 索引。

        Args:
            documents: 文档列表，每个文档为 dict，需包含 "content" 字段
        """
        self._documents = documents
        self._tokenized_docs = []
        self._doc_lengths = []

        # 分词
        for doc in documents:
            content = doc.get("content", "")
            tokens = self.tokenizer.tokenize(content)
            self._tokenized_docs.append(tokens)
            self._doc_lengths.append(len(tokens))

        # 计算平均文档长度
        total_length = sum(self._doc_lengths)
        self._avg_doc_length = total_length / max(1, len(self._doc_lengths))

        # 计算 IDF
        num_docs = len(documents)
        df: Dict[str, int] = {}  # 文档频率
        for tokens in self._tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        self._idf = {}
        for token, freq in df.items():
            # IDF 公式：log((N - df + 0.5) / (df + 0.5) + 1)
            self._idf[token] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)

        self._built = True
        logger.info(f"BM25 索引构建完成: {num_docs} 篇文档, 平均长度 {self._avg_doc_length:.1f}")

    def search(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[BM25Result]:
        """
        BM25 检索。

        Args:
            query: 查询文本
            top_k: 返回数量
            metadata_filter: 元数据过滤条件

        Returns:
            BM25Result 列表（按分数降序）
        """
        if not self._built:
            logger.warning("BM25 索引未构建")
            return []

        query_tokens = self.tokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores: List[Tuple[int, float]] = []

        for i, doc_tokens in enumerate(self._tokenized_docs):
            # 元数据过滤
            if metadata_filter:
                doc_meta = self._documents[i].get("metadata", {})
                if not all(doc_meta.get(k) == v for k, v in metadata_filter.items()):
                    continue

            score = self._compute_score(query_tokens, i, doc_tokens)
            if score > 0:
                scores.append((i, score))

        # 按分数降序排列
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(scores[:top_k], start=1):
            doc = self._documents[idx]
            results.append(BM25Result(
                content=doc.get("content", ""),
                metadata=doc.get("metadata", {}),
                score=score,
                rank=rank,
            ))

        return results

    def _compute_score(
        self,
        query_tokens: List[str],
        doc_idx: int,
        doc_tokens: List[str],
    ) -> float:
        """计算单篇文档的 BM25 分数"""
        doc_length = self._doc_lengths[doc_idx]
        # 词频统计
        tf_map: Dict[str, int] = {}
        for token in doc_tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        score = 0.0
        for qt in query_tokens:
            if qt not in self._idf:
                continue
            tf = tf_map.get(qt, 0)
            if tf == 0:
                continue

            idf = self._idf[qt]
            # BM25 公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / max(1, self._avg_doc_length))
            score += idf * numerator / denominator

        return score

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计"""
        return {
            "total_documents": len(self._documents),
            "avg_doc_length": self._avg_doc_length,
            "vocab_size": len(self._idf),
            "k1": self.k1,
            "b": self.b,
            "built": self._built,
        }


# ============================================================
# 全局实例
# ============================================================

# 默认分词器
default_tokenizer = ChineseAgriculturalTokenizer()

# 默认 BM25 检索器
default_bm25_retriever = BM25Retriever()
