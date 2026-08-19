# -*- coding: utf-8 -*-
"""
答案后处理：决策卡提取、证据策略执行、文本清理。
从 agent.py 提取，降低主模块复杂度。
"""
from __future__ import annotations
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ── 工具标记清理 ─────────────────────────────────────────────

_TEXT_TOOL_CALL_RE = re.compile(
    r"<tool_calls?\b[^>]*>(.*?)</tool_calls?>", re.IGNORECASE | re.DOTALL
)


def extract_text_tool_queries(text: str) -> List[str]:
    """恢复以文本形式输出的工具调用查询。"""
    return [m.strip() for m in _TEXT_TOOL_CALL_RE.findall(text) if m.strip()]


def requests_related_resources(message: str) -> bool:
    """检测用户是否请求图片、文档、链接或来源。"""
    return bool(re.search(r"图片|图像|示意图|照片|资料链接|官方资料|文档|来源|出处", message))


def clean_tool_markers(text: str) -> str:
    """清除内部工具协议标签，使其不显示为助手正文。"""
    cleaned = _TEXT_TOOL_CALL_RE.sub("", text)
    cleaned = re.sub(r"</?tool_call(?:s)?\b[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"^\s*(?:我来为您|我将为您|我会为您|我将调用工具|我会调用工具)(?:搜索|查找|检索)[^\n]*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    cleaned = re.sub(
        r"^\s*\*{0,2}图片资源查找\*{0,2}\s*[:：]?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    cleaned = re.sub(
        r"^\s*(?:正在调用|已调用|已完成)\s*[:：]?\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather)(?:\s*[,、]\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather))*\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    cleaned = re.sub(r"(?m)^[ \t]*\*([^*\r\n]+)\*\*(?=[ \t]*(?:[:：。！？]|$))", r"**\1**", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*]\s*$\n?", "", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


# ── 决策卡提取 ──────────────────────────────────────────────

_DECISION_HEADING_RE = re.compile(
    r"^\s*(?:#{1,4}\s*)?(?:(?:\d+|[一二三四五六七八九十]+)[\.、]\s*)?\**"
    r"(结论|核心建议|判断结论|现场摘要|问题概况|情况摘要|田间调查|优先判断|问题诊断|可能原因|诊断分析|现在做什么|处理方案|处理建议|田间措施|风险边界|注意事项|预防措施|安全提示|复查节点|效果跟踪|监测预警|复查与跟踪)\**\s*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

_DECISION_HEADING_ALIASES = {
    "核心建议": "结论",
    "判断结论": "结论",
    "问题概况": "现场摘要",
    "情况摘要": "现场摘要",
    "问题诊断": "优先判断",
    "可能原因": "优先判断",
    "诊断分析": "优先判断",
    "处理方案": "现在做什么",
    "处理建议": "现在做什么",
    "田间措施": "现在做什么",
    "注意事项": "风险边界",
    "预防措施": "风险边界",
    "安全提示": "风险边界",
    "效果跟踪": "复查节点",
    "监测预警": "复查节点",
    "复查与跟踪": "复查节点",
}


def _section_items(value: str, fallback: str) -> List[str]:
    lines = []
    for line in value.splitlines():
        if re.fullmatch(r"\s*(?:[-*_]\s*){3,}\s*", line):
            continue
        item = re.sub(r"^\s*(?:[-•]|\*(?=\s+)|\d+[\.、])\s*", "", line).strip()
        if item:
            lines.append(item)
    if not lines and value.strip():
        lines = [re.sub(r"\s+", " ", value.strip())]
    return lines[:5] or [fallback]


def _decision_defaults(question: str) -> Dict[str, str]:
    """根据农业任务选择缺失字段的默认提示。"""
    text = question.lower()
    if re.search(r"种子|浸种|催芽|晒种|包衣|播种前", text):
        return {
            "现场摘要": f"当前问题：{question.strip()}；建议补充作物品种、计划播期、种子来源/批次及是否已包衣。",
            "优先判断": "播种前先完成选种和种子状态检查，再按作物规程选择晒种、浸种催芽或包衣；具体药剂与时长需按登记标签核验。",
            "现在做什么": "先检查纯度、发芽率、含水状况和霉变；记录种子批次后，按当地规程进行晒种及必要的浸种催芽或包衣。",
            "风险边界": "已包衣种子不要重复浸药；浸种温度或时长不当会降低发芽率；药剂、浓度和安全间隔期必须以登记标签为准。",
            "复查节点": "催芽后检查发芽整齐度，播种后 3-7 天观察出苗率和苗情；异常时保留样品并联系当地农技人员复核。",
        }
    if re.search(r"土壤|红壤|酸性|盐碱|黏重|沙质|改良|ph", text):
        return {
            "现场摘要": f"当前问题：{question.strip()}；建议补充土壤 pH、质地、有机质及速效氮磷钾检测结果和目标作物。",
            "优先判断": "土壤改良应以测土结果为依据，先判断酸碱度、盐分和质地限制，再组合石灰、有机肥、排水或深翻措施。",
            "现在做什么": "先按规范取土检测 pH、有机质、速效氮磷钾和交换性铝/盐分；根据目标产量制定改良和施肥方案。",
            "风险边界": "石灰、肥料或掺沙用量不能脱离检测结果；过量会造成 pH 失衡、盐分累积或养分拮抗，具体剂量需官方核验。",
            "复查节点": "改良后 30 天复测 pH 或盐分，生育期观察长势，每年播种前复测并更新地块档案。",
        }
    if re.search(r"施肥|灌溉|水肥|追肥|底肥", text):
        return {
            "现场摘要": f"当前问题：{question.strip()}；建议补充作物、品种、生育期、目标产量、测土结果和近期灌溉量。",
            "优先判断": "施肥灌溉方案应由作物生育期和测土结果共同决定，先核算目标产量的养分需求，再安排基肥与追肥。",
            "现在做什么": "先确认地块和生育期并取土检测；按目标产量扣除土壤供肥量，分次安排基肥、追肥和灌水。",
            "风险边界": "未有测土结果时不提供精确施肥量；避免大水漫灌和一次性过量施肥，具体配方以当地农技部门建议为准。",
            "复查节点": "施肥后 7-14 天观察叶色和长势，关键生育期复测墒情或叶片养分，收获后复盘产量与投入。",
        }
    return {
        "现场摘要": (
            f"当前问题：{question.strip()}；建议补充地区、作物品种、生育期、现场症状和影响范围。"
            if question.strip()
            else "待补充作物、地区、生育期、现场症状和影响范围。"
        ),
        "优先判断": "当前信息不足，不能据此做出单一诊断。",
        "现在做什么": "先记录症状变化，补充现场照片或关键环境信息。",
        "风险边界": "涉及农药、肥料或严重扩散时，请以产品说明书和当地农技部门指导为准。",
        "复查节点": "补充信息后再复核，或在采取措施后观察 24-48 小时变化。",
    }


def extract_decision_card(answer: str, question: str = "") -> Dict[str, Any]:
    """从回答文本中提取五段式决策卡，不捏造缺失字段。"""
    matches = list(_DECISION_HEADING_RE.finditer(answer or ""))
    sections: Dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(answer)
        heading = match.group(1)
        canonical = _DECISION_HEADING_ALIASES.get(heading, heading)
        sections[canonical] = answer[match.end() : end].strip()

    defaults = _decision_defaults(question)
    summary = "\n".join(
        line
        for line in sections.get("现场摘要", "").splitlines()
        if not re.fullmatch(r"\s*(?:[-*_]\s*){3,}\s*", line)
    ).strip()
    missing_field_marker = bool(re.search(r"待补充|建议补充|信息不足|无法确认|不能据此", summary))
    complete = (
        all(name in sections and sections[name].strip() for name in defaults)
        and bool(summary)
        and not missing_field_marker
    )
    judgments = _section_items(sections.get("优先判断", ""), defaults["优先判断"])
    conclusion_items = _section_items(sections.get("结论", ""), "") if sections.get("结论", "").strip() else []
    conclusion = (
        conclusion_items[0]
        if conclusion_items
        else (judgments[0] if judgments and judgments[0] != defaults["优先判断"] else "先补充关键现场信息，再确定具体措施。")
    )
    return {
        "conclusion": conclusion,
        "summary": summary or defaults["现场摘要"],
        "judgments": judgments,
        "actions": _section_items(sections.get("现在做什么", ""), defaults["现在做什么"]),
        "risks": _section_items(sections.get("风险边界", ""), defaults["风险边界"]),
        "followup": _section_items(sections.get("复查节点", ""), defaults["复查节点"]),
        "complete": complete,
    }


# ── 证据过程清理 ─────────────────────────────────────────────

def strip_evidence_process(answer: str) -> str:
    """保留用户答案焦点；证据保留在结构化 UI 事件中。"""
    lines = []
    hiding_evidence = False
    evidence_heading = re.compile(
        r"^\s*(?:#{1,4}\s*)?\*{0,2}(?:知识库依据|参考来源|本次回答参考的知识上下文|本次回答参考|检索结果|检索过程|工具调用|调用工具)\*{0,2}\s*(?::|：)?[^\n]*$",
        re.IGNORECASE,
    )
    heading = re.compile(r"^\s*#{1,4}\s+\S+")
    for line in (answer or "").splitlines():
        if evidence_heading.match(line):
            hiding_evidence = True
            continue
        if hiding_evidence and heading.match(line):
            hiding_evidence = False
        if not hiding_evidence:
            lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\s*[（(]\s*(?:知识库依据|匹配度|相关性)\s*[^）)]*[）)]", "", cleaned)
    cleaned = re.sub(r"\s*(?:知识库依据|参考来源)\s*\[[A-Z]?\d+\]", "", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


# ── 简要回答压缩 ─────────────────────────────────────────────

def compact_answer(answer: str, question: str = "") -> str:
    """服务端强制简要回答上限，即使模型忽略指令。"""
    clean = clean_tool_markers(answer or "")
    if not clean:
        return clean
    card = extract_decision_card(clean, question)
    if card["complete"] or any(
        marker in clean
        for marker in ("现场摘要", "优先判断", "现在做什么", "风险边界", "复查节点")
    ):
        return "\n".join(
            [
                f"判断：{card['judgments'][0]}",
                f"建议：{card['actions'][0]}",
                f"注意：{card['risks'][0]}",
            ]
        )[:600]
    lines = [re.sub(r"^\s*(?:[-•]|\*(?=\s+)|\d+[.)、])\s*", "", line).strip() for line in clean.splitlines()]
    lines = [line for line in lines if line]
    compact = "\n".join(lines[:4])
    return compact[:600]


# ── 证据策略执行 ─────────────────────────────────────────────

EVIDENCE_SCOPE_LABELS = {
    "pesticide_label": "该作物和产品的官方登记标签/使用说明",
    "pesticide_registration": "农药登记制度的官方材料",
    "pesticide_governance": "农药管理的官方法规或规程",
    "fertilizer_recommendation": "适用地区和作物的官方施肥技术规程",
    "policy": "当前有效的官方政策原文",
    "technical_standard": "现行官方技术标准或规范",
    "animal_health_regulation": "动物健康监管的官方材料",
}


def build_evidence_gap_answer(question: str, required_scope: str, answer_mode: str) -> str:
    """当缺少 A 级官方依据时生成安全回答。"""
    required = EVIDENCE_SCOPE_LABELS.get(required_scope, "适用的 A 级官方依据")
    if answer_mode == "brief":
        return (
            f"当前未检索到{required}，不能给出具体处方或结论。"
            "请核对官方原文、产品登记标签和当地农技部门意见后再处理。"
        )
    return "\n".join(
        [
            "## 现场摘要",
            f"当前问题：{question.strip()}；待补充地区、作物、生育期及现场条件。",
            "## 优先判断",
            f"本次未检索到可支撑该问题的{required}。",
            "## 现在做什么",
            "先核对官方原文或登记标签，记录作物、地区、生育期和已采取措施；必要时咨询当地农技部门。",
            "## 风险边界",
            "在获得适用的 A 级官方依据前，系统不提供具体剂量、浓度、用药、施肥处方或政策资格结论。",
            "## 复查节点",
            "补充官方材料或现场信息后重新核验；病虫害扩散、人员或动物健康风险时及时转交专业人员。",
        ]
    )


def enforce_evidence_policy(
    answer: str,
    question: str,
    citations: List[Dict[str, Any]],
    requires_official_evidence_fn=None,
) -> str:
    """当缺少 A 级官方依据时，移除不支持的高风险处方。

    Parameters
    ----------
    requires_official_evidence_fn : callable, optional
        传入 agriir_pipeline.requires_official_evidence 以避免循环导入。
    """
    answer_has_high_risk = bool(
        re.search(
            r"农药|药剂|用药|剂量|安全间隔|肥料|施肥|追肥|石灰|有机肥|掺沙|施用|用量|浓度|公斤|kg|毫升|ml",
            answer or "",
            re.IGNORECASE,
        )
    )
    needs_official = True
    if requires_official_evidence_fn:
        needs_official = requires_official_evidence_fn(question)
    if not needs_official and not answer_has_high_risk:
        return answer
    has_official = any(
        item.get("eligible") and item.get("evidence_level") == "A" for item in citations
    )
    if has_official:
        return answer
    dosage_pattern = re.compile(
        r"\d+(?:\.\d+)?\s*(?:[-~至]\s*\d+(?:\.\d+)?)?\s*\*{0,2}\s*(?:公斤|千克|kg|克|g|毫升|ml|升|L|立方米|m³|%)\s*(?:/\s*(?:亩|公顷|株))?",
        re.IGNORECASE,
    )
    lines: List[str] = []
    replaced = False
    for line in (answer or "").splitlines():
        if dosage_pattern.search(line):
            if not replaced:
                lines.append(
                    "具体剂量、浓度或用量待官方核验，当前仅提供原则性建议：严格按产品登记标签、当地农技部门指导和安全间隔执行。"
                )
                replaced = True
            continue
        lines.append(line)
    sanitized = "\n".join(lines).strip() if replaced else answer
    if not re.search(r"待官方核验|官方核验|登记标签|农技站", sanitized):
        sanitized = (
            sanitized.rstrip()
            + "\n\n**证据边界**：当前缺少 A 级官方依据，具体剂量、登记和安全间隔待官方核验。"
        )
    return sanitized
