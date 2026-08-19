import pytest

from source_registry import SourceValidationError, build_evidence_metadata


def test_a_level_source_requires_matching_official_url_and_date():
    with pytest.raises(SourceValidationError):
        build_evidence_metadata(filename="政策.pdf", content_hash="abc", content_type="application/pdf", source_id="moa-official")
    metadata = build_evidence_metadata(
        filename="政策.pdf", content_hash="abc", content_type="application/pdf", source_id="moa-official",
        source_url="https://www.moa.gov.cn/govpublic/", published_at="2026-08-10", pack_id="jiangxi-policy", pack_version="2026.08.1",
        evidence_scope="policy|technical_standard",
    )
    assert metadata["evidence_level"] == "A"
    assert metadata["evidence_id"].startswith("moa-official:")
    assert metadata["evidence_scope"] == "policy|technical_standard"


def test_internal_document_is_explicitly_c_level():
    metadata = build_evidence_metadata(filename="试验记录.md", content_hash="abc", content_type="text/markdown")
    assert metadata["source_id"] == "cropwise-curated"
    assert metadata["evidence_level"] == "C"


def test_jx_source_accepts_registered_ganzhou_government_https_url():
    metadata = build_evidence_metadata(
        filename="脐橙冻害风险预警.md", content_hash="ganzhou-risk", content_type="text/markdown",
        source_id="jx-agri-official",
        source_url="https://www.ganzhou.gov.cn/zfxxgk/nyncyjgl/202601/example.shtml",
        published_at="2026-01-20", pack_id="gannan-citrus", pack_version="2026.08.0",
        evidence_scope="citrus_weather_risk|citrus_frost_protection",
    )
    assert metadata["evidence_level"] == "A"
    assert metadata["source_id"] == "jx-agri-official"
