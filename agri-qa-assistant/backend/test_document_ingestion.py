"""Deterministic unit tests for document preflight before RAG ingestion."""
from document_ingestion import (
    DocumentIngestionError,
    MAX_UPLOAD_BYTES,
    analyse_agriculture_document,
    parse_document,
    public_analysis,
)


AGRI_TEXT = (
    "江西早稻分蘖期田间管理：水稻应保持浅水层，依据测土结果合理施肥，"
    "并监测稻飞虱发生。遇到病虫害扩散应联系当地农技部门复核。"
)


def test_markdown_parse_and_public_analysis():
    parsed = parse_document("rice.md", "text/markdown", AGRI_TEXT.encode("utf-8"))
    assert parsed["eligible"] is True
    assert parsed["estimated_chunks"] == 1
    assert parsed["content_hash"]
    assert "text" not in public_analysis(parsed)


def test_gb18030_text_is_decoded():
    parsed = parse_document("rice.txt", "text/plain", AGRI_TEXT.encode("gb18030"))
    assert parsed["eligible"] is True
    assert "水稻" in parsed["text"]


def test_non_agriculture_and_mixed_code_are_rejected():
    assert analyse_agriculture_document("这是 Java 程序开发文档，不包含农业知识，也不讨论作物。")["eligible"] is False
    assert analyse_agriculture_document("请用 Java 代码实现水稻成本计算")["eligible"] is False


def test_unsupported_empty_short_and_oversized_files_are_rejected():
    for filename, data in [("payload.exe", b"x"), ("empty.md", b""), ("short.md", "水稻".encode())]:
        try:
            parse_document(filename, "application/octet-stream", data)
        except DocumentIngestionError:
            pass
        else:
            raise AssertionError(f"{filename} should be rejected")
    try:
        parse_document("large.md", "text/markdown", b"a" * (MAX_UPLOAD_BYTES + 1))
    except DocumentIngestionError:
        pass
    else:
        raise AssertionError("oversized upload should be rejected")


def test_html_and_json_extract_text():
    html = "<html><body><h1>水稻病虫害</h1><p>稻飞虱需要田间监测，结合分蘖期水肥管理、天敌保护和安全间隔开展综合防治。</p></body></html>"
    assert parse_document("guide.html", "text/html", html.encode())["eligible"] is True
    payload = '{"topic":"水稻施肥","content":"分蘖期保持浅水层，依据测土结果合理施肥并监测稻飞虱发生。"}'.encode()
    assert parse_document("guide.json", "application/json", payload)["eligible"] is True


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_"):
            value()
    print("document ingestion tests passed")
