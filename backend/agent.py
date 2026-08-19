# -*- coding: utf-8 -*-
"""
修复版 AgricultureAgent：
- 工具调用循环：LLM 返回 tool_calls 时执行工具，结果再次调用 LLM
- 知识库检索结果注入 system prompt
- 直接返回有意义的文本回答
"""
from __future__ import annotations
import os
import logging
import asyncio
import json
import re
from typing import AsyncIterator, Dict, List, Optional, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from config import settings
from tools import get_all_tools
from memory import conversation_memory, extract_candidate_memories, propose_active_memory_questions
from knowledge_base import knowledge_base
from domain_guard import build_domain_rejection, classify_query
from agriir_pipeline import agriir_pipeline

logger = logging.getLogger(__name__)

# 预载所有工具并建立名称索引
_ALL_TOOLS = get_all_tools()
_TOOL_MAP = {t.name: t for t in _ALL_TOOLS if hasattr(t, "name")}

# 系统提示词
AGRICULTURE_SYSTEM_PROMPT = """\
你是 CropWise，江西农业大学官方农业智能问答助手。

## 知识范围
作物种植（水稻、小麦、玉米、油菜等）、病虫害防治、施肥灌溉、土壤管理、农机具使用、农业政策。特别熟悉江西农业大学科研成果与动态。

## 江西农业大学特色知识域
以农为优势、以生物技术为特色，优先关注以下经过来源核验的领域：
- 水稻、双季稻与南方粮油作物的育种、栽培和病虫害；
- 家猪遗传育种、动物营养与畜禽疫病风险；
- 生物多样性、鄱阳湖流域农业资源与生态、森林资源保护；
- 果蔬采后保鲜与质量安全、赣南脐橙等江西特色产业；
- 农业资源与环境、红壤与水资源、现代农业装备和植保作业。
当问题命中上述领域时，优先检索对应江农专题知识包和官方来源；没有来源时必须说明“知识库暂无江农专项依据”，不能把学校名称当作证据。

## 回答规则
1. **领域硬约束**：只能回答农业知识、农业生产决策、农时、农业气象、农业政策，以及农业图片/官方资料问题。非农业问题必须明确拒绝，不能借题发挥。
2. **禁止越界**：不得回答数学、编程、Java/Python/SQL、网页开发、通用写作、娱乐或其他非农业问题；即使问题中出现作物名称，也不得生成代码。
3. **多轮对话记忆**：记住用户提到的作物、地区等上下文，但不能把历史中的农业词语当作当前问题的授权。
4. **知识库优先**：知识库没有的，明确说“知识库暂无此信息”，再给一般性建议，不得伪造知识库来源。
5. **时间/生育期**：用 get_current_datetime / calculate_growing_period 工具
6. **诚实回答**：不确定的知识明确告知
7. **农药/化肥**：只有 A 级官方来源（农业农村部门、正式登记/标准或已核验官方技术文件）才能支撑具体剂量、登记和安全间隔；否则只能给原则性建议并明确“待官方核验”。
8. **严重病虫害**：建议咨询当地农技站
9. **关联资源**：用户要求图片、病虫害示意图、官方文档或资料链接时，必须调用 search_agri_resources；不要编造 URL。图片仅作识别参考，不作为确诊依据。

## 可用工具
- query_crop_knowledge：作物种植知识（crop_name + topic）
- get_current_datetime：当前日期时间
- calculate_growing_period：作物生育期与农时
- get_agri_weather：无密钥公共农业气象预报（仅作参考）
- fetch_web_content：抓取网页内容（url）
- search_agri_resources：搜索免费开放的农业图片和官方资料入口

## 高风险来源闸门
涉及农药、肥料、兽药、疫病、政策、补贴、标准、规范或登记时，只能引用 evidence_level=A 的官方证据。普通知识库片段可以帮助解释背景，但不得作为具体处方或政策结论的依据。

## 回答格式
- 分点说明（1. 2. 3.）
- 关键词加粗
- 农业数据具体（品种名、时期）；涉及剂量时遵守高风险来源闸门
- **直接给答案，不要说"我正在查询"**
- 先用 1-2 句给出用户可以立即理解的结论，再展开行动建议；不要把检索、匹配度、工具调用或知识库片段写成回答正文。

## 决策卡协议
农业生产类问题先给一个“结论”段，再使用以下五个 Markdown 标题；无法从问题或知识库确认的内容写“待补充”，不得猜测：
0. 结论
1. 现场摘要
2. 优先判断
3. 现在做什么
4. 风险边界
5. 复查节点
现场摘要说明已知的作物、地区、生育期、症状和影响范围；优先判断列出最多 3 个可能方向及依据；现在做什么给出今天/48 小时内可执行的步骤；风险边界说明农药、肥料、天气和需要农技人员复核的情况；复查节点说明观察指标和复查时间。
"""

TOOL_DESCRIPTIONS = {
    "query_crop_knowledge": "作物种植知识（crop_name + topic）",
    "get_current_datetime": "当前日期时间",
    "calculate_growing_period": "作物生育期与农时",
    "get_agri_weather": "公共农业气象预报",
    "fetch_web_content": "抓取网页内容（url）",
    "search_agri_resources": "搜索农业相关图片和官方资料",
}

ANSWER_MODES = {"professional", "brief"}
ANSWER_MODE_PROMPTS = {
    "professional": """
## 回答模式：专业回答
使用完整的农业决策卡：现场摘要、优先判断、现在做什么、风险边界、复查节点。给出知识库依据、条件假设和必要的核验动作；可以较详细，但不要重复工具过程。
""",
    "brief": """
## 回答模式：简要回答
先给结论，再给最多 3 条可执行建议和 1 条风险提醒。控制在约 120-260 个中文字符，不输出五段式决策卡、不复述知识库全文、不描述工具调用过程；若信息不足，明确指出最关键的一个待补充条件。涉及农药、灾害或诊断不确定时，必须保留安全边界。
""",
}


def _normalize_answer_mode(answer_mode: Optional[str]) -> str:
    return answer_mode if answer_mode in ANSWER_MODES else "professional"

_EXPLICIT_DATE_RE = re.compile(r"(?P<year>20\d{2})\s*(?:年|[-/.])\s*(?P<month>\d{1,2})\s*(?:月|[-/.])\s*(?P<day>\d{1,2})\s*日?")
_TIME_QUERY_RE = re.compile(r"当前日期|今天|现在|当前时间|今日|明天|后天|本周|近期|最近|播种|播期|农时|生育期|积温|天气|降雨|霜冻|寒潮|高温|气象|current date|today|weather|sowing|growing season", re.IGNORECASE)


def _extract_explicit_date(message: str) -> Optional[str]:
    """Extract only a fully-qualified date; never infer the year from server time."""
    match = _EXPLICIT_DATE_RE.search(message or "")
    if not match:
        return None
    try:
        from datetime import date
        return date(int(match.group("year")), int(match.group("month")), int(match.group("day"))).isoformat()
    except ValueError:
        return None


def _extract_date_literal(message: str) -> Optional[str]:
    match = _EXPLICIT_DATE_RE.search(message or "")
    return match.group(0).strip() if match else None


def _needs_time_preflight(message: str) -> bool:
    return bool(_extract_explicit_date(message) or _TIME_QUERY_RE.search(message or ""))


def _safe_tool_args(args: Any) -> Dict[str, Any]:
    if not isinstance(args, dict):
        return {}
    safe: Dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[str(key)] = str(value)[:300] if isinstance(value, str) else value
        else:
            safe[str(key)] = str(value)[:300]
    return safe


def _run_tool(name, args):
    """同步执行单个工具，返回字符串结果"""
    return _run_tool_audited(name, args)["result"]


def _run_tool_audited(name: str, args: Any) -> Dict[str, Any]:
    """Invoke a tool and return a stable audit record for SSE and API clients."""
    import time
    started = time.perf_counter()
    safe_args = _safe_tool_args(args)
    tool = _TOOL_MAP.get(name)
    if not tool:
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": False, "error_code": "TOOL_NOT_FOUND", "duration_ms": 0, "result": f"[工具 {name} 不存在]"}
    try:
        result = tool.invoke(args if isinstance(args, dict) else {})
        result_text = str(result) if result else ""
        ok = True
        error_code = None
        try:
            parsed = json.loads(result_text)
            if isinstance(parsed, dict) and parsed.get("ok") is False:
                ok = False
                error_code = parsed.get("error_code") or "TOOL_REPORTED_ERROR"
        except (TypeError, ValueError):
            if result_text.startswith("[") and "失败" in result_text:
                ok = False
                error_code = "TOOL_EXECUTION_ERROR"
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": ok, "error_code": error_code, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "result": result_text}
    except Exception as exc:
        logger.warning("工具 %s 执行失败: %s", name, exc)
        return {"name": name, "args": safe_args, "source": "internal-mcp", "ok": False, "error_code": "TOOL_EXECUTION_ERROR", "duration_ms": round((time.perf_counter() - started) * 1000, 2), "result": f"[工具 {name} 执行失败]"}


def _chunk_text(content: Any) -> str:
    """Normalise provider-specific streamed content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


_TEXT_TOOL_CALL_RE = re.compile(r"<tool_calls?\b[^>]*>(.*?)</tool_calls?>", re.IGNORECASE | re.DOTALL)


def _extract_text_tool_queries(text: str) -> List[str]:
    """Recover resource requests emitted as text by providers that miss tool-call metadata."""
    return [match.strip() for match in _TEXT_TOOL_CALL_RE.findall(text) if match.strip()]


def _requests_related_resources(message: str) -> bool:
    """Detect an explicit user request for images, documents, links, or sources."""
    return bool(re.search(r"图片|图像|示意图|照片|资料链接|官方资料|文档|来源|出处", message))


def _clean_tool_markers(text: str) -> str:
    """Never persist or display internal tool protocol tags as assistant prose."""
    cleaned = _TEXT_TOOL_CALL_RE.sub("", text)
    cleaned = re.sub(r"</?tool_call(?:s)?\b[^>]*>", "", cleaned, flags=re.IGNORECASE)
    # Providers sometimes turn tool orchestration into assistant prose. The
    # UI already receives structured tool/resource events, so these lines are
    # redundant and expose internal function names to the user.
    cleaned = re.sub(r"^\s*(?:我来为您|我将为您|我会为您|我将调用工具|我会调用工具)(?:搜索|查找|检索)[^\n]*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"^\s*\*{0,2}图片资源查找\*{0,2}\s*[:：]?\s*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(
        r"^\s*(?:正在调用|已调用|已完成)\s*[:：]?\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather)(?:\s*[,、]\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather))*\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    # Normalize common provider markdown typos before persistence and rendering.
    cleaned = re.sub(r"(?m)^[ \t]*\*([^*\r\n]+)\*\*(?=[ \t]*(?:[:：。！？]|$))", r"**\1**", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*]\s*$\n?", "", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


_DECISION_HEADING_RE = re.compile(
    r"^\s*(?:#{1,4}\s*)?(?:(?:\d+|[一二三四五六七八九十]+)[\.、]\s*)?\**"
    r"(结论|核心建议|判断结论|现场摘要|问题概况|情况摘要|田间调查|优先判断|问题诊断|可能原因|诊断分析|现在做什么|处理方案|处理建议|田间措施|风险边界|注意事项|预防措施|安全提示|复查节点|效果跟踪|监测预警|复查与跟踪)\**\s*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

_DECISION_HEADING_ALIASES = {
    "核心建议": "结论", "判断结论": "结论",
    "问题概况": "现场摘要", "情况摘要": "现场摘要",
    "问题诊断": "优先判断", "可能原因": "优先判断", "诊断分析": "优先判断",
    "处理方案": "现在做什么", "处理建议": "现在做什么", "田间措施": "现在做什么",
    "注意事项": "风险边界", "预防措施": "风险边界", "安全提示": "风险边界",
    "效果跟踪": "复查节点", "监测预警": "复查节点", "复查与跟踪": "复查节点",
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
    """Choose missing-field prompts that match the user's agricultural task."""
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
        "现场摘要": f"当前问题：{question.strip()}；建议补充地区、作物品种、生育期、现场症状和影响范围。" if question.strip() else "待补充作物、地区、生育期、现场症状和影响范围。",
        "优先判断": "当前信息不足，不能据此做出单一诊断。",
        "现在做什么": "先记录症状变化，补充现场照片或关键环境信息。",
        "风险边界": "涉及农药、肥料或严重扩散时，请以产品说明书和当地农技部门指导为准。",
        "复查节点": "补充信息后再复核，或在采取措施后观察 24-48 小时变化。",
    }


def _extract_decision_card(answer: str, question: str = "") -> Dict[str, Any]:
    """Extract the five decision sections without inventing missing facts."""
    matches = list(_DECISION_HEADING_RE.finditer(answer or ""))
    sections: Dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(answer)
        heading = match.group(1)
        canonical = _DECISION_HEADING_ALIASES.get(heading, heading)
        sections[canonical] = answer[match.end():end].strip()

    defaults = _decision_defaults(question)
    summary = "\n".join(
        line for line in sections.get("现场摘要", "").splitlines()
        if not re.fullmatch(r"\s*(?:[-*_]\s*){3,}\s*", line)
    ).strip()
    # A model may emit all five headings while still explicitly saying that
    # the field data is missing. That is a pending card, not a complete one.
    missing_field_marker = bool(re.search(r"待补充|建议补充|信息不足|无法确认|不能据此", summary))
    complete = all(name in sections and sections[name].strip() for name in defaults) and bool(summary) and not missing_field_marker
    judgments = _section_items(sections.get("优先判断", ""), defaults["优先判断"])
    conclusion_items = _section_items(sections.get("结论", ""), "") if sections.get("结论", "").strip() else []
    conclusion = conclusion_items[0] if conclusion_items else (
        judgments[0] if judgments and judgments[0] != defaults["优先判断"] else "先补充关键现场信息，再确定具体措施。"
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


def _strip_evidence_process(answer: str) -> str:
    """Keep the user answer focused; evidence remains in structured UI events."""
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


def _compact_answer(answer: str, question: str = "") -> str:
    """Apply a server-side ceiling so brief mode remains brief even if a model ignores style instructions."""
    clean = _clean_tool_markers(answer or "")
    if not clean:
        return clean
    card = _extract_decision_card(clean, question)
    if card["complete"] or any(marker in clean for marker in ("现场摘要", "优先判断", "现在做什么", "风险边界", "复查节点")):
        return "\n".join([
            f"判断：{card['judgments'][0]}",
            f"建议：{card['actions'][0]}",
            f"注意：{card['risks'][0]}",
        ])[:600]
    lines = [re.sub(r"^\s*(?:[-•]|\*(?=\s+)|\d+[.)、])\s*", "", line).strip() for line in clean.splitlines()]
    lines = [line for line in lines if line]
    compact = "\n".join(lines[:4])
    return compact[:600]


def _enforce_evidence_policy(answer: str, question: str, citations: List[Dict[str, Any]]) -> str:
    """Remove unsupported high-risk prescriptions from model prose.

    The model may see low-confidence background snippets, but concrete doses
    are only safe when an eligible A-level official citation is present.
    Without one, retain a useful principle and make the verification boundary
    explicit instead of silently presenting a numeric recipe.
    """
    answer_has_high_risk = bool(re.search(r"农药|药剂|用药|剂量|安全间隔|肥料|施肥|追肥|石灰|有机肥|掺沙|施用|用量|浓度|公斤|kg|毫升|ml", answer or "", re.IGNORECASE))
    if not agriir_pipeline.requires_official_evidence(question) and not answer_has_high_risk:
        return answer
    has_official = any(item.get("eligible") and item.get("evidence_level") == "A" for item in citations)
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
                lines.append("具体剂量、浓度或用量待官方核验，当前仅提供原则性建议：严格按产品登记标签、当地农技部门指导和安全间隔执行。")
                replaced = True
            continue
        lines.append(line)
    sanitized = "\n".join(lines).strip() if replaced else answer
    if not re.search(r"待官方核验|官方核验|登记标签|农技站", sanitized):
        sanitized = sanitized.rstrip() + "\n\n**证据边界**：当前缺少 A 级官方依据，具体剂量、登记和安全间隔待官方核验。"
    return sanitized


_EVIDENCE_SCOPE_LABELS = {
    "pesticide_label": "该作物和产品的官方登记标签/使用说明",
    "pesticide_registration": "农药登记制度的官方材料",
    "pesticide_governance": "农药管理的官方法规或规程",
    "fertilizer_recommendation": "适用地区和作物的官方施肥技术规程",
    "policy": "当前有效的官方政策原文",
    "technical_standard": "现行官方技术标准或规范",
    "animal_health_regulation": "动物健康监管的官方材料",
}


def _build_evidence_gap_answer(question: str, required_scope: str, answer_mode: str) -> str:
    required = _EVIDENCE_SCOPE_LABELS.get(required_scope, "适用的 A 级官方依据")
    if answer_mode == "brief":
        return f"当前未检索到{required}，不能给出具体处方或结论。请核对官方原文、产品登记标签和当地农技部门意见后再处理。"
    return "\n".join([
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
    ])


class AgricultureAgent:
    """农业智能问答 Agent（修复版）"""

    def __init__(self):
        proxy = (os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
                 os.environ.get("https_proxy") or os.environ.get("http_proxy") or "")

        print("[DEBUG] agnes_base_url :", settings.agnes_base_url)
        print("[DEBUG] agnes_chat_model:", settings.agnes_chat_model)
        print("[DEBUG] tools registered:", list(_TOOL_MAP.keys()))
        print("[DEBUG] proxy:", proxy)

        self.llm = ChatOpenAI(
            base_url=settings.agnes_base_url,
            openai_api_key=settings.agnes_api_key,
            model=settings.agnes_chat_model,
            temperature=0.3,
            openai_proxy=proxy or None,
        ).bind_tools(_ALL_TOOLS)

        # 内存会话历史（仅本进程有效）
        self._hist: Dict[str, List] = {}

    async def stream_chat(self, message: str, thread_id: str, user_id=None, answer_mode: str = "professional", scenario_context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """Yield a transport-neutral event stream while preserving the existing tool loop."""
        answer_mode = _normalize_answer_mode(answer_mode)
        # Domain policy is deliberately before status events, retrieval, memory,
        # tools, and the model. This prevents out-of-scope prompts from reaching
        # any expensive or general-purpose capability.
        decision = classify_query(message)
        if not decision["allowed"]:
            rejection = build_domain_rejection(decision)
            yield {
                "type": "guard",
                "guarded": True,
                "category": decision["category"],
                "reason": decision["reason"],
                "scope": "农业知识、农业生产决策、农时、农业气象、农业政策及农业资料",
                "recommendations": ["水稻稻飞虱怎么防治？", "小麦返青期如何追肥？", "江西早稻什么时候播种？"],
            }
            yield {"type": "delta", "text": rejection}
            yield {
                "type": "done",
                "thread_id": thread_id,
                "message": rejection,
                "tool_calls": [],
                "guarded": True,
                "guard_reason": decision["reason"],
                "completion_status": "guarded",
            }
            return

        yield {"type": "mode", "mode": answer_mode}
        yield {"type": "status", "message": "正在匹配农业知识库"}
        tool_calls_out: List[Dict[str, Any]] = []
        time_context: Optional[Dict[str, Any]] = None
        # Deterministic temporal preflight prevents the model from silently
        # using a stale training date or treating a user example date as now.
        if _needs_time_preflight(message):
            reference_date = _extract_explicit_date(message)
            date_literal = _extract_date_literal(message)
            time_args = {"timezone": settings.app_timezone}
            if date_literal:
                # Preserve invalid user dates as input so the tool can return
                # INVALID_REFERENCE_DATE instead of silently using server now.
                time_args["reference_date"] = reference_date or date_literal
            yield {"type": "tool", "name": "get_current_datetime", "status": "running", "args": _safe_tool_args(time_args), "source": "internal-mcp"}
            time_audit = await asyncio.to_thread(_run_tool_audited, "get_current_datetime", time_args)
            time_context = None
            try:
                parsed_time = json.loads(time_audit["result"])
                if isinstance(parsed_time, dict):
                    time_context = parsed_time
            except (TypeError, ValueError):
                pass
            tool_calls_out.append({key: value for key, value in time_audit.items() if key != "result"})
            yield {"type": "tool", "name": "get_current_datetime", "status": "complete", "args": time_audit["args"], "source": time_audit["source"], "ok": time_audit["ok"], "error_code": time_audit.get("error_code"), "duration_ms": time_audit["duration_ms"]}
            if time_context:
                yield {"type": "time-context", "context": time_context}
        # Memory is a separate evidence channel: candidates are explicit task
        # facts, while retrieval decides what is relevant to this turn.
        candidates = extract_candidate_memories(message, thread_id, user_id)
        for candidate in candidates:
            stored = await conversation_memory.upsert_memory(candidate)
            yield {
                "type": "memory-candidate",
                "memory": {"id": stored.get("id"), "type": stored.get("memory_type"), "content": stored.get("content"), "status": "待确认"},
            }
        active_questions = propose_active_memory_questions(message, candidates)
        if active_questions:
            yield {"type": "memory-action", "mode": "active", "questions": active_questions, "reason": "当前农业决策缺少关键现场条件"}
        organization = await conversation_memory.organize_if_needed(thread_id, user_id)
        if organization.get("triggered"):
            yield {"type": "memory-organized", "reason": organization.get("reason"), "conflicts": organization.get("conflicts", []), "archived": organization.get("archived", 0)}
        memory_selection = await conversation_memory.relevant_memories(message, thread_id, user_id, max_items=6)
        used_memories = memory_selection.get("used", [])
        skipped_memories = memory_selection.get("skipped", [])
        if used_memories or skipped_memories:
            yield {"type": "memory", "used": [
                {"id": item.get("id"), "content": item.get("content"), "relevance": item.get("relevance")}
                for item in used_memories
            ], "skipped": [
                {"id": item.get("id"), "content": item.get("content"), "relevance": item.get("relevance"), "reason": "相似但未达到当前任务相关性门槛"}
                for item in skipped_memories
            ]}
        retrieval_trace = agriir_pipeline.retrieve(message, knowledge_base, scenario_context)
        retrieval_strategy = retrieval_trace["strategy"]
        kb_results = retrieval_trace["results"]
        citations = retrieval_trace["citations"]
        yield {"type": "trace", "stage": "retrieval", "query": retrieval_trace["query"], "refined_query": retrieval_trace["refined_query"], "subqueries": retrieval_trace["subqueries"], "strategy": retrieval_strategy, "citation_count": len(citations)}

        kb_ctx = ""
        if kb_results:
            kb_ctx = "\n\n## 知识库检索结果：\n" + "\n".join(
                f"- [{citations[index]['label']}] {result.get('content', '')}" for index, result in enumerate(kb_results[:3])
            )
            kb_ctx += "\n\n## 可引用证据：\n" + agriir_pipeline.citation_context(citations)
            items = []
            for result in kb_results[:3]:
                content = str(result.get("content", "")).strip().replace("\n", " ")
                metadata = result.get("metadata") or {}
                citation = citations[len(items)] if len(items) < len(citations) else {}
                items.append({
                    "title": str(metadata.get("title") or metadata.get("source") or "农业知识库"),
                    "excerpt": content[:120],
                    "relevance": round(float(result.get("relevance", 0.0)), 3),
                    "eligible": bool(citation.get("eligible", False)),
                    "evidence_level": str(citation.get("evidence_level", "C")),
                    "eligibility_reason": citation.get("eligibility_reason", "similarity-threshold"),
                })
            yield {"type": "ui", "component": "knowledge-context", "props": {"items": items, "strategy": retrieval_strategy}}
            yield {"type": "sources", "items": citations}

        required_evidence_scope = agriir_pipeline.required_evidence_scope(message)
        has_eligible_evidence = any(item.get("eligible") and item.get("evidence_level") == "A" for item in citations)
        if required_evidence_scope and not has_eligible_evidence:
            answer = _build_evidence_gap_answer(message, required_evidence_scope, answer_mode)
            yield {"type": "status", "message": "缺少适用的官方依据，已启用安全回答"}
            yield {"type": "delta", "text": answer}
            if answer_mode == "professional":
                yield {"type": "ui", "component": "decision-card", "props": _extract_decision_card(answer, message)}
            await conversation_memory.add_message(thread_id, "user", message)
            await conversation_memory.add_message(thread_id, "assistant", answer)
            self._hist.setdefault(thread_id, []).extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": answer},
            ])
            yield {"type": "done", "thread_id": thread_id, "message": answer, "tool_calls": tool_calls_out, "answer_mode": answer_mode, "completion_status": "guarded", "evidence_guarded": True, "required_evidence_scope": required_evidence_scope}
            return

        memory_ctx = ""
        if used_memories:
            memory_ctx = "\n\n## 当前任务相关记忆（仅供参考，不是知识库证据）：\n" + "\n".join(
                f"- {item.get('content')}（相关性 {item.get('relevance', 0):.0%}）" for item in used_memories
            )
        time_ctx = ""
        if time_context:
            time_ctx = "\n\n## 时间上下文（服务端确定性预检，必须遵守）:\n" + json.dumps(time_context, ensure_ascii=False)
        scenario_ctx = ""
        if scenario_context:
            scenario_ctx = "\n\n## 结构化场景上下文（服务端字段，缺失处不得猜测）：\n" + json.dumps(scenario_context, ensure_ascii=False)
        system_prompt = AGRICULTURE_SYSTEM_PROMPT + ANSWER_MODE_PROMPTS[answer_mode] + time_ctx + memory_ctx + scenario_ctx + kb_ctx
        history = self._hist.get(thread_id)
        if history is None:
            stored_history = await conversation_memory.get_history(thread_id, limit=8)
            history = [
                {"role": item["role"], "content": item["content"]}
                for item in stored_history
                if item["role"] in {"user", "assistant"}
            ]
            self._hist[thread_id] = history
        messages = [SystemMessage(content=system_prompt)]
        for item in history:
            messages.append(HumanMessage(content=item["content"]) if item["role"] == "user" else AIMessage(content=item["content"]))
        messages.append(HumanMessage(content=message))

        answer_parts: List[str] = []
        generation_failed = False
        failure_detail = ""

        for loop_index in range(3):
            try:
                yield {"type": "status", "message": "正在生成农技建议"}
                combined_chunk = None
                async for chunk in self.llm.astream(messages):
                    combined_chunk = chunk if combined_chunk is None else combined_chunk + chunk
                    text = _chunk_text(getattr(chunk, "content", ""))
                    if text:
                        answer_parts.append(text)
                        yield {"type": "delta", "text": text}

                if answer_parts:
                    break

                tool_calls = getattr(combined_chunk, "tool_calls", None) or []
                if not tool_calls:
                    break

                messages.append(combined_chunk)
                for tool_call in tool_calls:
                    name = tool_call.get("name", "")
                    args = tool_call.get("args", {})
                    yield {"type": "tool", "name": name, "status": "running", "args": _safe_tool_args(args), "source": "internal-mcp"}
                    audit = await asyncio.to_thread(_run_tool_audited, name, args)
                    tool_calls_out.append({key: value for key, value in audit.items() if key != "result"})
                    result = audit["result"]
                    yield {"type": "tool", "name": name, "status": "complete", "args": audit["args"], "source": audit["source"], "ok": audit["ok"], "error_code": audit.get("error_code"), "duration_ms": audit["duration_ms"]}
                    if name == "search_agri_resources":
                        try:
                            resources = json.loads(result)
                            if isinstance(resources, list):
                                yield {"type": "resources", "items": resources[:6]}
                        except (TypeError, ValueError):
                            logger.info("资源工具返回了不可解析的数据")
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call.get("id", "")))
            except asyncio.CancelledError:
                logger.info("流式对话已被客户端取消: %s", thread_id)
                raise
            except Exception as exc:
                logger.error("LLM astream 失败 (_loop %d): %s", loop_index, exc)
                generation_failed = True
                failure_detail = str(exc)
                break

        raw_answer = "".join(answer_parts).strip()
        text_tool_queries = _extract_text_tool_queries(raw_answer)
        if not any(call.get("name") == "search_agri_resources" for call in tool_calls_out) and _requests_related_resources(message):
            # Some providers fall back to plain text and skip the structured
            # tool-call field. Honor the user's explicit resource request on
            # the server so the UI still receives real resource cards.
            text_tool_queries.append(message)
        answer = _strip_evidence_process(_clean_tool_markers(raw_answer))

        # Some OpenAI-compatible providers occasionally serialize a function
        # call as XML-like text instead of populating `tool_calls`. Recover the
        # resource request so the UI still receives a real resource event.
        if text_tool_queries and not any(call.get("name") == "search_agri_resources" for call in tool_calls_out):
            for query in text_tool_queries[:2]:
                yield {"type": "tool", "name": "search_agri_resources", "status": "running", "args": {"query": query}, "source": "internal-mcp"}
                audit = await asyncio.to_thread(_run_tool_audited, "search_agri_resources", {"query": query})
                tool_calls_out.append({key: value for key, value in audit.items() if key != "result"})
                result = audit["result"]
                yield {"type": "tool", "name": "search_agri_resources", "status": "complete", "args": audit["args"], "source": audit["source"], "ok": audit["ok"], "error_code": audit.get("error_code"), "duration_ms": audit["duration_ms"]}
                try:
                    resources = json.loads(result)
                    if isinstance(resources, list):
                        yield {"type": "resources", "items": resources[:6]}
                except (TypeError, ValueError):
                    logger.info("文本工具调用返回了不可解析的资源数据")

        if text_tool_queries and not answer:
            answer = "已根据你的请求整理相关农业图片与资料，请查看下方资源卡片。"

        completion_status = "fallback" if generation_failed else "complete"
        if not answer:
            try:
                yield {"type": "status", "message": "正在使用备用回答通道"}
                fallback_llm = ChatOpenAI(
                    base_url=settings.agnes_base_url,
                    openai_api_key=settings.agnes_api_key,
                    model=settings.agnes_chat_model,
                    temperature=0.1,
                    openai_proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
                )
                fallback = await fallback_llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=message)])
                answer = _chunk_text(getattr(fallback, "content", "")).strip()
                if answer:
                    completion_status = "fallback"
                    yield {"type": "delta", "text": answer}
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("LLM fallback 失败: %s", exc)
                failure_detail = str(exc)

        if not answer:
            answer = "抱歉，我现在无法回答这个问题，请稍后重试。"
            yield {"type": "delta", "text": answer}
            completion_status = "error"
            yield {"type": "error", "message": "模型生成未完成，请检查服务后重试。", "error_code": "MODEL_GENERATION_FAILED"}

        answer = _strip_evidence_process(_clean_tool_markers(answer))
        policy_answer = _enforce_evidence_policy(answer, message, citations)
        if policy_answer != answer:
            answer = policy_answer
            yield {"type": "answer-replace", "text": answer, "mode": answer_mode, "reason": "evidence-policy"}

        # Build the decision card before appending the traceable citation block;
        # citations belong to the collapsed evidence layer, not the action card.
        decision_card = _extract_decision_card(answer, message) if answer_mode != "brief" else None

        # Sources are delivered as a separate structured event and rendered in
        # the collapsed evidence layer. Keep retrieval/citation prose out of
        # primary and persisted answer content.

        if answer_mode == "brief":
            compact = _compact_answer(answer, message)
            if compact != answer:
                answer = compact
                # Replace the streamed answer in the persisted/API result. The
                # model text may already have been displayed, so emit a mode
                # correction event for clients that reconcile the final value.
                yield {"type": "answer-replace", "text": answer, "mode": answer_mode}
        if answer_mode != "brief":
            yield {"type": "ui", "component": "decision-card", "props": decision_card}

        await conversation_memory.add_message(thread_id, "user", message)
        await conversation_memory.add_message(
            thread_id,
            "assistant",
            answer,
            extra={
                "answer_mode": answer_mode,
                "completion_status": completion_status,
                "decision_card": decision_card,
                "runtime_details": {
                    "persisted": True,
                    "tool_count": len(tool_calls_out),
                    "knowledge_count": len(kb_results[:3]) if isinstance(kb_results, list) else 0,
                    "citation_count": len(citations),
                    "memory_used_count": len(used_memories),
                    "memory_skipped_count": len(skipped_memories),
                    "has_time_context": bool(time_context),
                },
            },
        )
        self._hist.setdefault(thread_id, []).extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ])
        yield {"type": "done", "thread_id": thread_id, "message": answer, "tool_calls": tool_calls_out, "answer_mode": answer_mode, "completion_status": completion_status}

    async def chat(self, message: str, thread_id: str, user_id=None, answer_mode: str = "professional", scenario_context: Optional[Dict[str, Any]] = None):
        """Backwards-compatible non-streaming adapter for existing API consumers."""
        answer = ""
        tool_calls = []
        sources = []
        completion_status = "complete"
        async for event in self.stream_chat(message, thread_id, user_id, answer_mode, scenario_context):
            if event["type"] == "done":
                answer = event["message"]
                tool_calls = event["tool_calls"]
                completion_status = event.get("completion_status", "complete")
            elif event["type"] == "sources" and isinstance(event.get("items"), list):
                sources = event["items"]
        return {"message": answer, "sources": sources, "tool_calls": tool_calls, "thread_id": thread_id, "answer_mode": _normalize_answer_mode(answer_mode), "completion_status": completion_status}

    async def get_history(self, thread_id, limit=20):
        history = await conversation_memory.get_history(thread_id, limit)
        enriched = []
        for item in history:
            current = dict(item)
            if current.get("role") == "assistant":
                current["content"] = _strip_evidence_process(_clean_tool_markers(str(current.get("content") or "")))
                extra = dict(current.get("extra") or {})
                if extra.get("answer_mode") not in ANSWER_MODES:
                    extra["answer_mode"] = "professional" if "现场摘要" in current["content"] else "brief"
                if extra.get("answer_mode") == "professional" and not isinstance(extra.get("decision_card"), dict):
                    extra["decision_card"] = _extract_decision_card(current["content"])
                current["extra"] = extra
            enriched.append(current)
        return enriched

    async def clear_history(self, thread_id):
        await conversation_memory.clear_thread(thread_id)
        self._hist.pop(thread_id, None)


agri_agent = AgricultureAgent()
