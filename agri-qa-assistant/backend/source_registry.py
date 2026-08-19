"""Source governance for evidence packs and document ingestion."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    publisher: str
    evidence_level: str
    allowed_domains: tuple[str, ...]
    description: str


SOURCES = {
    "moa-official": SourceDefinition("moa-official", "中华人民共和国农业农村部", "A", ("moa.gov.cn",), "国家政策、登记与技术规范"),
    "jx-agri-official": SourceDefinition("jx-agri-official", "江西省农业农村厅及地方政府", "A", ("jiangxi.gov.cn", "nync.jiangxi.gov.cn", "ganzhou.gov.cn"), "江西生产规程、县域政策与农时"),
    "open-meteo-forecast": SourceDefinition("open-meteo-forecast", "Open-Meteo", "B", ("open-meteo.com",), "公共天气预报"),
    "cropwise-curated": SourceDefinition("cropwise-curated", "CropWise", "C", (), "待逐条核验的内部农业知识"),
}


class SourceValidationError(ValueError):
    pass


def list_sources() -> list[Dict[str, Any]]:
    return [{**asdict(source), "allowed_domains": list(source.allowed_domains)} for source in SOURCES.values()]


def _matches_allowed_domain(hostname: str, allowed_domains: tuple[str, ...]) -> bool:
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)


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
    source = SOURCES.get(resolved_id)
    if not source:
        raise SourceValidationError(f"未知 source_id：{resolved_id}")

    cleaned_url = (source_url or "").strip()
    if source.evidence_level == "A":
        if not cleaned_url:
            raise SourceValidationError("A 级官方证据必须提供 source_url")
        parsed = urlparse(cleaned_url)
        if parsed.scheme != "https" or not parsed.hostname or not _matches_allowed_domain(parsed.hostname.lower(), source.allowed_domains):
            raise SourceValidationError("A 级证据 URL 必须使用已登记的官方 HTTPS 域名")
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
    # Chroma metadata accepts scalar values, but rejects nulls.
    return {key: value for key, value in metadata.items() if value is not None}
