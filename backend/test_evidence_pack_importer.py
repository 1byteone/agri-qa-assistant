from evidence_pack_importer import extract_official_article


def test_extracts_title_date_and_article_body():
    article = extract_official_article("""
    <html><head><meta name='ArticleTitle' content='农药管理条例'><meta name='PubDate' content='2023-12-05 17:13:00'></head>
    <body><div class='sj_arc_body'>第一条 为了加强农药管理。第二条 农药登记应依法进行。这是一段足够长的模拟官方正文，用于验证导入器可以提取正文内容并保留可审计的元数据。第三条 县级以上农业主管部门应当依法履行监督管理职责，生产经营者应当遵守标签、登记和安全使用要求。第四条 本段内容只用于测试解析边界，不构成实际农业生产建议。</div></body></html>
    """)
    assert article["title"] == "农药管理条例"
    assert article["published_at"] == "2023-12-05"
    assert "农药登记" in article["text"]


def test_rejects_garbled_text_that_cannot_meet_the_article_contract():
    try:
        extract_official_article("<html><body><div class='sj_arc_body'>åè¯ç®¡çæ¡ä¾</div></body></html>")
    except ValueError as exc:
        assert "正文" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("乱码正文不应通过导入器")


def test_extracts_ganzhou_government_article_container():
    article = extract_official_article("""
    <html><head><meta name='ArticleTitle' content='脐橙冻害风险预警'><meta name='PubDate' content='2026-01-20 09:08:08'></head>
    <body><div class='article-content-body'>脐橙留树果和幼树发生低温冻害风险较高。请关注当地天气预报，在低温来临前及时采摘、入库贮藏，并结合果园实际采取防冻措施。本段为足够长的政府页面结构模拟正文，用于验证赣州政府公开页面可以被导入器提取。风险预警应结合果园海拔、地形、树龄和当地实时预报执行，不能替代现场农技人员对灾害范围的核验。</div></body></html>
    """)
    assert article["title"] == "脐橙冻害风险预警"
    assert article["published_at"] == "2026-01-20"
    assert "低温冻害" in article["text"]
