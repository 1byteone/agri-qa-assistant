"""Contract tests for optional professional term annotations."""
from agri_terms import lookup_term


def test_known_term_has_source_backed_definition():
    item = lookup_term("稻飞虱")
    assert item is not None
    assert item["summary"]
    assert item["source_name"]
    assert item["source_url"].startswith("https://")


def test_unknown_term_is_not_invented():
    assert lookup_term("不存在的农业术语") is None


if __name__ == "__main__":
    test_known_term_has_source_backed_definition()
    test_unknown_term_is_not_invented()
    print("agri term tests passed")
