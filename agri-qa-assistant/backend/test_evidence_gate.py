from agent import _build_evidence_gap_answer


def test_evidence_gap_answer_does_not_offer_a_specific_prescription():
    answer = _build_evidence_gap_answer("水稻每亩施多少肥", "fertilizer_recommendation", "professional")
    assert "官方施肥技术规程" in answer
    assert "不提供具体剂量" in answer
    assert "现场摘要" in answer


def test_brief_evidence_gap_answer_remains_actionable():
    answer = _build_evidence_gap_answer("水稻农药每亩用量", "pesticide_label", "brief")
    assert "登记标签" in answer
    assert len(answer) < 200
