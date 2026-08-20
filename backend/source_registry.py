"""Source governance for evidence packs and document ingestion.

提供数据源注册、版本管理、许可证追溯功能。
参考：中国农科院农业智能知识服务平台的数据治理体系。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path


@dataclass(frozen=True)
class SourceDefinition:
    """数据源定义"""
    source_id: str
    publisher: str
    evidence_level: str  # A/B/C/D
    allowed_domains: tuple[str, ...]
    description: str
    # 扩展字段
    api_endpoint: str = ""
    auth_type: str = ""  # none / api_key / oauth
    update_frequency: str = ""  # daily / weekly / monthly / yearly
    license: str = "公开资料"
    spatial_granularity: str = ""  # national / province / county
    temporal_granularity: str = ""  # realtime / daily / monthly / yearly
    contact: str = ""


class SourceValidationError(ValueError):
    """数据源验证错误"""
    pass


# ============================================================
# 数据源注册表
# ============================================================

SOURCES: Dict[str, SourceDefinition] = {
    # ---- A 级：官方来源 ----
    "moa-official": SourceDefinition(
        source_id="moa-official",
        publisher="中华人民共和国农业农村部",
        evidence_level="A",
        allowed_domains=("moa.gov.cn",),
        description="国家政策、登记与技术规范",
        api_endpoint="https://www.moa.gov.cn/",
        update_frequency="daily",
        license="政府公开信息",
        spatial_granularity="national",
    ),
    "jx-agri-official": SourceDefinition(
        source_id="jx-agri-official",
        publisher="江西省农业农村厅及地方政府",
        evidence_level="A",
        allowed_domains=("jiangxi.gov.cn", "nync.jiangxi.gov.cn", "ganzhou.gov.cn"),
        description="江西生产规程、县域政策与农时",
        api_endpoint="https://nync.jiangxi.gov.cn/",
        update_frequency="weekly",
        license="政府公开信息",
        spatial_granularity="province",
    ),
    "caas-research": SourceDefinition(
        source_id="caas-research",
        publisher="中国农业科学院农业信息研究所",
        evidence_level="A",
        allowed_domains=("caas.cn", "iaastd.org.cn"),
        description="农业科研成果、技术标准、知识图谱",
        api_endpoint="https://aii.caas.cn/",
        update_frequency="monthly",
        license="科研公开",
        spatial_granularity="national",
    ),
    "national-pest-control": SourceDefinition(
        source_id="national-pest-control",
        publisher="全国农业技术推广服务中心",
        evidence_level="A",
        allowed_domains=("natesc.org.cn",),
        description="全国病虫害防治技术方案",
        update_frequency="yearly",
        license="技术推广",
        spatial_granularity="national",
    ),

    # ---- B 级：科研/数据来源 ----
    "open-meteo-forecast": SourceDefinition(
        source_id="open-meteo-forecast",
        publisher="Open-Meteo",
        evidence_level="B",
        allowed_domains=("open-meteo.com",),
        description="公共天气预报",
        api_endpoint="https://api.open-meteo.com/v1/forecast",
        auth_type="none",
        update_frequency="daily",
        license="CC BY 4.0",
        spatial_granularity="province",
        temporal_granularity="daily",
    ),
    "cma-weather": SourceDefinition(
        source_id="cma-weather",
        publisher="中国气象局",
        evidence_level="B",
        allowed_domains=("data.cma.cn", "weather.com.cn"),
        description="气象数据、灾害预警",
        api_endpoint="https://data.cma.cn/",
        auth_type="api_key",
        update_frequency="daily",
        license="气象数据",
        spatial_granularity="county",
        temporal_granularity="daily",
    ),
    "faostat": SourceDefinition(
        source_id="faostat",
        publisher="联合国粮农组织",
        evidence_level="B",
        allowed_domains=("fao.org",),
        description="农业统计、国际对比",
        api_endpoint="https://www.fao.org/faostat/",
        update_frequency="yearly",
        license="CC BY 4.0",
        spatial_granularity="national",
        temporal_granularity="yearly",
    ),
    "geodata-cn": SourceDefinition(
        source_id="geodata-cn",
        publisher="国家地球系统科学数据中心",
        evidence_level="B",
        allowed_domains=("geodata.cn",),
        description="土地利用、遥感、气候、土壤",
        api_endpoint="https://www.geodata.cn/",
        auth_type="api_key",
        update_frequency="yearly",
        license="科研公开",
        spatial_granularity="province",
    ),

    # ---- C 级：补充来源 ----
    "cropwise-curated": SourceDefinition(
        source_id="cropwise-curated",
        publisher="CropWise",
        evidence_level="C",
        allowed_domains=(),
        description="待逐条核验的内部农业知识",
        license="MIT",
    ),
    "agri-encyclopedia": SourceDefinition(
        source_id="agri-encyclopedia",
        publisher="农业百科/公开资料",
        evidence_level="C",
        allowed_domains=(),
        description="农业百科知识、公开资料",
        license="公开资料",
    ),

    # ---- D 级：线索来源（默认不进入证据） ----
    "web-search": SourceDefinition(
        source_id="web-search",
        publisher="通用搜索",
        evidence_level="D",
        allowed_domains=(),
        description="通用搜索结果，需人工审核",
        license="待审核",
    ),
}


# ============================================================
# 注册表管理
# ============================================================

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "docs" / "data-source-registry.json"


class SourceRegistry:
    """数据源注册表管理器"""

    def __init__(self):
        self._sources = dict(SOURCES)
        self._custom_sources: Dict[str, SourceDefinition] = {}
        self._load_custom()

    def _load_custom(self):
        """加载自定义数据源"""
        if REGISTRY_PATH.exists():
            try:
                data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
                for item in data.get("sources", []):
                    source = SourceDefinition(
                        source_id=item["source_id"],
                        publisher=item.get("publisher", ""),
                        evidence_level=item.get("evidence_level", "C"),
                        allowed_domains=tuple(item.get("allowed_domains", [])),
                        description=item.get("description", ""),
                        api_endpoint=item.get("api_endpoint", ""),
                        auth_type=item.get("auth_type", ""),
                        update_frequency=item.get("update_frequency", ""),
                        license=item.get("license", ""),
                        spatial_granularity=item.get("spatial_granularity", ""),
                        temporal_granularity=item.get("temporal_granularity", ""),
                        contact=item.get("contact", ""),
                    )
                    self._custom_sources[source.source_id] = source
            except Exception:
                pass

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        """获取数据源"""
        return self._custom_sources.get(source_id) or self._sources.get(source_id)

    def list_sources(
        self,
        evidence_level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列出所有数据源"""
        all_sources = {**self._sources, **self._custom_sources}
        sources = list(all_sources.values())
        if evidence_level:
            sources = [s for s in sources if s.evidence_level == evidence_level]
        return [{**asdict(s), "allowed_domains": list(s.allowed_domains)} for s in sources]

    def register_source(self, source: SourceDefinition) -> bool:
        """注册自定义数据源"""
        if source.source_id in self._sources:
            return False  # 不允许覆盖内置来源
        self._custom_sources[source.source_id] = source
        self._save_custom()
        return True

    def validate_url(self, source_id: str, url: str) -> Tuple[bool, str]:
        """验证 URL 是否属于已登记的数据源"""
        source = self.get_source(source_id)
        if not source:
            return False, f"未知数据源: {source_id}"

        if not source.allowed_domains:
            return True, "无域名限制"

        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False, "A 级证据必须使用 HTTPS"
        if not parsed.hostname:
            return False, "无效 URL"

        hostname = parsed.hostname.lower()
        for domain in source.allowed_domains:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True, "域名匹配"

        return False, f"域名不在白名单中: {hostname}"

    def get_evidence_level_label(self, level: str) -> str:
        """获取证据等级标签"""
        labels = {
            "A": "A 级 - 官方来源（政策/登记/技术规范）",
            "B": "B 级 - 科研/数据来源（气象/统计/科研）",
            "C": "C 级 - 补充来源（百科/图片/公开资料）",
            "D": "D 级 - 线索来源（需人工审核）",
        }
        return labels.get(level, f"未知等级: {level}")

    def _save_custom(self):
        """保存自定义数据源"""
        try:
            REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "sources": [
                    {**asdict(s), "allowed_domains": list(s.allowed_domains)}
                    for s in self._custom_sources.values()
                ],
            }
            REGISTRY_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_sources = {**self._sources, **self._custom_sources}
        level_counts = {}
        for s in all_sources.values():
            level_counts[s.evidence_level] = level_counts.get(s.evidence_level, 0) + 1
        return {
            "total_sources": len(all_sources),
            "builtin_sources": len(self._sources),
            "custom_sources": len(self._custom_sources),
            "by_level": level_counts,
        }


# ============================================================
# 全局实例
# ============================================================

source_registry = SourceRegistry()


# ============================================================
# 便捷函数（保持向后兼容）
# ============================================================

def list_sources() -> List[Dict[str, Any]]:
    """列出所有数据源"""
    return source_registry.list_sources()


def build_evidence_metadata(
    *,
    filename: str,
    content_hash: str,
    content_type: str,
    source_id: Optional[str] = None,
    source_url: Optional[str] = None,
    published_at: Optional[str] = None,
    region: Optional[str] = None,
    pack_id: Optional[str] = None,
    pack_version: Optional[str] = None,
    evidence_scope: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_id = (source_id or "cropwise-curated").strip()
    source = source_registry.get_source(resolved_id)
    if not source:
        raise SourceValidationError(f"未知 source_id：{resolved_id}")

    cleaned_url = (source_url or "").strip()
    if source.evidence_level == "A":
        if not cleaned_url:
            raise SourceValidationError("A 级官方证据必须提供 source_url")
        valid, msg = source_registry.validate_url(resolved_id, cleaned_url)
        if not valid:
            raise SourceValidationError(msg)
        if not (published_at or "").strip():
            raise SourceValidationError("A 级官方证据必须提供 published_at")

    evidence_id = f"{resolved_id}:{hashlib.sha256(content_hash.encode('utf-8')).hexdigest()[:16]}"
    metadata = {
        "category": "uploaded_agriculture",
        "topic": "user_document",
        "title": filename,
        "source": filename,
        "source_id": source.source_id,
        "publisher": source.publisher,
        "evidence_level": source.evidence_level,
        "source_url": cleaned_url or None,
        "published_at": (published_at or "").strip() or None,
        "region": (region or "").strip() or None,
        "pack_id": (pack_id or "").strip() or None,
        "pack_version": (pack_version or "").strip() or None,
        "evidence_scope": (evidence_scope or "").strip() or None,
        "evidence_id": evidence_id,
        "content_hash": content_hash,
        "content_type": content_type,
    }
    return {key: value for key, value in metadata.items() if value is not None}
