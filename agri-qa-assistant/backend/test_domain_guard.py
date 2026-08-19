"""Deterministic tests for the CropWise agriculture boundary."""
from domain_guard import classify_query


def test_out_of_scope_programming_and_math():
    assert not classify_query("99乘法表java实现")["allowed"]
    assert not classify_query("什么是递归？")["allowed"]
    assert not classify_query("请写一个 Java 程序计算水稻种植成本")["allowed"]


def test_agriculture_questions_are_allowed():
    allowed = [
        "水稻稻飞虱怎么防治？",
        "小麦返青期如何追肥？",
        "江西早稻什么时候播种？",
        "请给我稻飞虱相关图片和官方资料",
        "农业无人机喷洒时需要注意什么？",
        "How should I manage rice pests?",
    ]
    assert all(classify_query(item)["allowed"] for item in allowed)


def test_empty_and_ambiguous_are_blocked():
    assert not classify_query("")["allowed"]
    assert not classify_query("你好，帮我看看")["allowed"]


if __name__ == "__main__":
    test_out_of_scope_programming_and_math()
    test_agriculture_questions_are_allowed()
    test_empty_and_ambiguous_are_blocked()
    print("domain guard passed")
