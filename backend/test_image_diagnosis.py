# -*- coding: utf-8 -*-
"""图像诊断测试。"""
import pytest
import io
from image_diagnosis import ImageDiagnosisEngine, ImageDiagnosis


@pytest.fixture
def engine():
    return ImageDiagnosisEngine()


def _make_jpeg_bytes() -> bytes:
    """制造一个最小的有效 JPEG 文件。"""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x11\x04\x12!1\x06\x13Q\xa1\x07\"q\x142\x81\x91\xa2\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd9\x8f\xe1\xb0\x04\xa0\x00\x00\x00\x00\xff\xd9"


class TestImageDiagnosis:
    """图像诊断测试。"""

    def test_validate_jpeg_passes(self, engine):
        jpeg = _make_jpeg_bytes()
        assert engine.validate_image(jpeg, "image/jpeg") is None

    def test_validate_unsupported_type(self, engine):
        jpeg = _make_jpeg_bytes()
        error = engine.validate_image(jpeg, "image/gif")
        assert error is not None
        assert "不支持的图片格式" in error

    def test_validate_empty(self, engine):
        error = engine.validate_image(b"", "image/jpeg")
        assert error is not None

    def test_validate_too_large(self, engine):
        from image_diagnosis import MAX_IMAGE_BYTES
        large = b"\x00" * (MAX_IMAGE_BYTES + 1)
        error = engine.validate_image(large, "image/jpeg")
        assert error is not None
        assert "大小限制" in error

    def test_rule_analysis_leaf_spot(self, engine):
        result = engine._analyze_with_rules(b"", "叶片出现褐色斑点", "水稻")
        assert len(result.possible_causes) >= 1
        assert "斑" in str(result.possible_causes)
        assert result.requires_human_review is True
        assert result.mode == "rule"

    def test_rule_analysis_yellowing(self, engine):
        result = engine._analyze_with_rules(b"", "叶片发黄", "水稻")
        assert len(result.possible_causes) >= 1
        assert result.confidence >= 0.3

    def test_rule_analysis_empty_description(self, engine):
        result = engine._analyze_with_rules(b"", "", "")
        assert result.confidence <= 0.3
        assert "信息不足" in str(result.possible_causes)

    def test_rule_analysis_pest(self, engine):
        result = engine._analyze_with_rules(b"", "有虫子吃叶子", "水稻")
        assert any("虫" in c for c in result.possible_causes)

    def test_rule_analysis_always_disclaimer(self, engine):
        """所有诊断结果必须包含免责声明。"""
        result = engine._analyze_with_rules(b"", "叶片发黄", "水稻")
        assert "本结果为 AI 辅助识别" in result.disclaimer
        assert "不能作为确诊依据" in result.disclaimer

    def test_full_analyze_pipeline(self, engine):
        """完整分析流程：校验 → 分析 → 返回结果。"""
        jpeg = _make_jpeg_bytes()
        error = engine.validate_image(jpeg, "image/jpeg")
        assert error is None
        result = engine.analyze(jpeg, "image/jpeg", "叶片出现褐色斑点", "水稻")
        assert isinstance(result, ImageDiagnosis)
        assert result.requires_human_review is True
        assert "AI 辅助识别" in result.disclaimer