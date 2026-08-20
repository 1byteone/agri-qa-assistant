import os
import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta, timezone

import requests
import json
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger(__name__)


def _resource_query_terms(query: str) -> str:
    compact = re.sub(r"[^\w\u4e00-\u9fff ]+", " ", query)
    return " ".join(compact.split())[:120]


_AGRI_RESOURCE_ALIASES = {
    "稻飞虱": "brown planthopper Nilaparvata lugens rice",
    "褐飞虱": "brown planthopper Nilaparvata lugens rice",
    "白背飞虱": "white-backed planthopper Sogatella furcifera rice",
    "小麦锈病": "wheat rust Puccinia wheat",
    "玉米螟": "corn borer Ostrinia nubilalis maize",
    "蚜虫": "aphid crop plant pest",
    "水稻": "rice paddy",
    "小麦": "wheat field",
    "玉米": "maize corn field",
}

_CURATED_RESOURCE_IMAGES = {
    "稻飞虱": {
        "kind": "image",
        "title": "Brown planthopper（稻飞虱）",
        # Use the stable original file URL. Wikimedia may reject guessed thumb
        # widths; API-discovered resources still use the returned thumburl.
        "url": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg",
        "license": "CC BY 3.0 US",
    },
    "褐飞虱": {
        "kind": "image",
        "title": "Brown planthopper（褐飞虱）",
        "url": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg",
        "license": "CC BY 3.0 US",
    },
}


def _resource_search_query(query: str) -> str:
    terms = [_AGRI_RESOURCE_ALIASES[key] for key in _AGRI_RESOURCE_ALIASES if key in query]
    return terms[0] if terms else _resource_query_terms(query)


def _fetch_wikimedia_resources(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Free/open image search via Wikimedia Commons API."""
    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": _resource_search_query(query),
                "gsrnamespace": 6,
                "gsrlimit": max(1, min(limit, 5)),
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": 640,
                "format": "json",
                "origin": "*",
            },
            timeout=12,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        resources = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            metadata = info.get("extmetadata") or {}
            license_name = (metadata.get("LicenseShortName") or {}).get("value", "Wikimedia Commons")
            resources.append({
                "kind": "image",
                "title": page.get("title", "").replace("File:", ""),
                "url": info.get("thumburl") or info.get("url"),
                "source_url": info.get("descriptionurl"),
                "license": re.sub(r"<[^>]+>", "", license_name),
            })
        return [resource for resource in resources if resource.get("url") and resource.get("source_url")]
    except Exception as exc:
        logger.info("Wikimedia 资源检索失败: %s", exc)
        return []


def get_agri_resources(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Return free/open image and document entry points related to an agricultural question."""
    query_text = _resource_query_terms(query)
    resources = []
    for keyword, resource in _CURATED_RESOURCE_IMAGES.items():
        if keyword in query_text:
            resources.append(resource)
            break
    resources.extend(_fetch_wikimedia_resources(query_text, limit=limit))
    encoded = requests.utils.quote(query_text)
    resources.append({
        "kind": "document",
        "title": "FAO 农业知识门户检索",
        "url": f"https://www.fao.org/search/en/?q={encoded}",
        "source_url": "https://www.fao.org/",
        "license": "FAO 官方资料入口",
    })
    resources.append({
        "kind": "document",
        "title": "农业农村部政策与公开信息检索",
        "url": f"https://www.moa.gov.cn/was5/web/search?searchword={encoded}",
        "source_url": "https://www.moa.gov.cn/",
        "license": "农业农村部官方资料入口",
    })
    return resources[: max(1, min(limit + 2, 6))]


@tool
def search_agri_resources(query: str) -> str:
    """搜索免费开放的农业图片和官方资料入口，返回 JSON 资源列表。"""
    return json.dumps(get_agri_resources(query), ensure_ascii=False)


# ==================== 农业领域工具 ====================

class CropQueryInput(BaseModel):
    crop_name: str = Field(description="作物名称，如水稻、小麦、玉米")
    topic: str = Field(description="查询主题，如 planting / pest / fertilizer / irrigation")


@tool
def query_crop_knowledge(crop_name: str, topic: str) -> str:
    """查询作物种植知识库，获取特定作物的种植技术、病虫害防治、施肥灌溉等信息。
    
    参数:
        crop_name: 作物名称，如水稻、小麦、玉米、蔬菜等
        topic: 查询主题，如 planting(种植)、pest(病虫害)、fertilizer(施肥)、irrigation(灌溉)
    
    返回:
        相关知识要点总结
    """
    crop_name = (crop_name or "").strip()
    topic = (topic or "").strip()
    if not crop_name or not topic:
        return json.dumps({"ok": False, "error_code": "INVALID_QUERY", "message": "crop_name 和 topic 不能为空。"}, ensure_ascii=False)
    try:
        # Lazy import avoids coupling tool registration to Chroma initialization.
        from knowledge_base import knowledge_base
        results = knowledge_base.search(f"{crop_name} {topic}", top_k=5, strategy="hybrid")
    except Exception as exc:
        logger.warning("作物知识检索失败: %s", exc)
        return json.dumps({"ok": False, "error_code": "KNOWLEDGE_BASE_UNAVAILABLE", "message": "农业知识库暂时不可用。"}, ensure_ascii=False)
    if not results:
        return json.dumps({"ok": False, "error_code": "NO_KNOWLEDGE_MATCH", "crop": crop_name, "topic": topic, "results": [], "message": "知识库暂无该作物和主题的匹配依据。"}, ensure_ascii=False)
    return json.dumps({
        "ok": True,
        "crop": crop_name,
        "topic": topic,
        "source": "CropWise农业知识库",
        "results": [
            {
                "content": result.get("content", ""),
                "metadata": result.get("metadata") or {},
                "relevance": round(float(result.get("relevance", 0.0)), 4),
            }
            for result in results
        ],
    }, ensure_ascii=False)


@tool
def get_current_datetime(timezone: str = "Asia/Shanghai", reference_date: Optional[str] = None) -> str:
    """获取真实当前时间，或在用户明确给出日期时返回带标签的评估时间。

    reference_date 只接受 YYYY-MM-DD / YYYY年M月D日，不传时使用服务器系统时钟；
    传入后不得称为真实当前时间，必须在回答中说明这是用户指定的评估日期。
    """
    try:
        from zoneinfo import ZoneInfo
        zone = ZoneInfo(timezone)
    except Exception:
        return json.dumps({"ok": False, "error_code": "INVALID_TIMEZONE", "timezone": timezone}, ensure_ascii=False)

    now = datetime.now(zone)
    if reference_date:
        try:
            raw_reference = reference_date.strip()
            chinese_match = re.fullmatch(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", raw_reference)
            iso_match = re.fullmatch(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", raw_reference)
            parts = chinese_match or iso_match
            if not parts:
                raise ValueError
            reference = date(int(parts.group(1)), int(parts.group(2)), int(parts.group(3)))
        except ValueError:
            return json.dumps({"ok": False, "error_code": "INVALID_REFERENCE_DATE", "reference_date": reference_date, "expected": "YYYY-MM-DD"}, ensure_ascii=False)
        return json.dumps({
            "ok": True, "kind": "evaluation_datetime", "date": reference.isoformat(),
            "local_datetime": f"{reference.isoformat()}T12:00:00", "timezone": timezone,
            "source": "user_reference", "is_actual_now": False,
            "notice": "这是用户指定的评估日期，不代表服务器当前日期。",
        }, ensure_ascii=False)
    return json.dumps({
        "ok": True, "kind": "current_datetime", "date": now.date().isoformat(),
        "local_datetime": now.isoformat(timespec="seconds"), "timezone": timezone,
        "source": "server_system_clock", "is_actual_now": True,
    }, ensure_ascii=False)


@tool
def calculate_growing_period(crop_name: str, region: str = "江西", evaluation_date: Optional[str] = None) -> str:
    """计算作物生育期和农时安排。
    
    参数:
        crop_name: 作物名称
        region: 种植区域，如华北、华东、华南、东北
    
    返回:
        作物生育期和农时安排建议
    """
    region_aliases = {"南昌": "江西", "赣州": "江西", "九江": "江西", "上饶": "江西", "吉安": "江西", "宜春": "江西", "华东": "华东", "华北": "华北"}
    canonical_region = next((value for key, value in region_aliases.items() if key in region), region)
    crop_calendar = {
        "水稻": {"江西": "早稻通常3月下旬至4月上旬播种、4月下旬至5月移栽；晚稻需结合前茬收获和当地积温安排，不能用单一日期替代县域农时。", "华北": "4月上中旬育秧，5月中下旬插秧，9月下旬收获", "华东": "3月下旬育秧，4月中下旬插秧，9月上中旬收获"},
        "小麦": {"江西": "江西小麦种植需结合品种熟期、播期和冬季温度，通常秋播后越冬，返青至拔节期重点关注追肥和湿害。", "华北": "10月上旬播种，次年5月下旬收获", "华东": "10月中下旬播种，次年6月上旬收获"},
        "玉米": {"江西": "春玉米和夏玉米播期受前茬、温度和墒情影响，应结合县域农时与天气窗口安排。", "华北": "4月中旬播种，8月下旬收获", "华东": "3月下旬播种，7月下旬收获"},
    }
    
    if crop_name in crop_calendar:
        calendar = crop_calendar[crop_name].get(canonical_region, "请提供具体种植区域")
        result = {"ok": True, "crop": crop_name, "region": canonical_region, "calendar": calendar, "source": "CropWise农业知识库基础农时规则", "requires_local_validation": True}
        if evaluation_date:
            result["evaluation_date"] = evaluation_date
            result["date_semantics"] = "用户指定评估日期，不是服务器当前日期"
        return json.dumps(result, ensure_ascii=False)
    return json.dumps({"ok": False, "error_code": "CROP_REGION_NOT_FOUND", "crop": crop_name, "region": canonical_region, "message": "知识库暂无该作物在该区域的详细农时安排，请咨询当地农技站。"}, ensure_ascii=False)


@tool
def get_agri_weather(location: str = "南昌", days: int = 3) -> str:
    """通过无需密钥的 Open-Meteo 公共接口获取农业决策所需的天气摘要。

    location 支持江西城市名或英文地名；返回温度、降雨、风速和天气代码。
    这是 CropWise 内嵌的 MCP-compatible 公共数据适配器，不代表江西省官方实测数据。
    """
    location = (location or "").strip() or "南昌"
    try:
        days = int(days)
    except (TypeError, ValueError):
        return json.dumps({"ok": False, "error_code": "INVALID_DAYS", "message": "days 必须是 1-7 的整数。"}, ensure_ascii=False)
    if not 1 <= days <= 7:
        return json.dumps({"ok": False, "error_code": "INVALID_DAYS", "message": "days 必须是 1-7 的整数。"}, ensure_ascii=False)
    aliases = {"南昌": "Nanchang, Jiangxi", "赣州": "Ganzhou, Jiangxi", "九江": "Jiujiang, Jiangxi", "上饶": "Shangrao, Jiangxi", "吉安": "Ji'an, Jiangxi", "宜春": "Yichun, Jiangxi"}
    query = aliases.get(location, location)
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 1, "language": "zh", "format": "json"},
            timeout=8,
        )
        geo.raise_for_status()
        result = (geo.json().get("results") or [None])[0]
        if not result:
            return json.dumps({"ok": False, "error_code": "LOCATION_NOT_FOUND", "location": location}, ensure_ascii=False)
        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": result["latitude"], "longitude": result["longitude"],
                "timezone": settings.app_timezone, "forecast_days": days,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code",
            },
            timeout=8,
        )
        forecast.raise_for_status()
        payload = forecast.json()
        daily = payload.get("daily") or {}
        rows = []
        for index, day in enumerate(daily.get("time") or []):
            rows.append({
                "date": day,
                "temperature_max_c": (daily.get("temperature_2m_max") or [None])[index],
                "temperature_min_c": (daily.get("temperature_2m_min") or [None])[index],
                "precipitation_mm": (daily.get("precipitation_sum") or [None])[index],
                "wind_speed_max_kmh": (daily.get("wind_speed_10m_max") or [None])[index],
                "weather_code": (daily.get("weather_code") or [None])[index],
            })
        return json.dumps({
            "ok": True, "location": location, "resolved_name": result.get("name"),
            "timezone": payload.get("timezone", settings.app_timezone),
            "source": "open-meteo-public-api", "publisher": "Open-Meteo", "evidence_level": "B",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "valid_at": (daily.get("time") or [None])[0],
            "license": "CC BY 4.0 / Open-Meteo attribution", "is_official_local_station": False,
            "notice": "公共预报数据仅作农业决策参考，灾害预警以气象部门发布为准。", "daily": rows,
        }, ensure_ascii=False)
    except requests.exceptions.Timeout:
        return json.dumps({"ok": False, "error_code": "UPSTREAM_TIMEOUT", "source": "open-meteo-public-api", "message": "天气服务请求超时。"}, ensure_ascii=False)
    except requests.exceptions.RequestException as exc:
        logger.info("Open-Meteo 请求失败: %s", exc)
        return json.dumps({"ok": False, "error_code": "UPSTREAM_UNAVAILABLE", "source": "open-meteo-public-api", "message": "天气服务暂时不可用。"}, ensure_ascii=False)
    except Exception as exc:
        logger.warning("天气工具失败: %s", exc)
        return json.dumps({"ok": False, "error_code": "WEATHER_TOOL_ERROR", "message": "天气工具处理失败。"}, ensure_ascii=False)


# ==================== 网页内容抓取工具 ====================

class FetchWebContentInput(BaseModel):
    url: str = Field(description="要抓取的网页 URL，必须是完整 URL（以 http:// 或 https:// 开头）")


def _clean_html_to_markdown(html: str, url: str) -> str:
    """将 HTML 转为简洁的 Markdown 文本"""
    soup = BeautifulSoup(html, "html.parser")

    # 移除无关标签
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    # 提取 <title>
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    # 提取 meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_desc_text = meta_desc.get("content", "") if meta_desc else ""

    # 提取正文（优先 article/main/body）
    main = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|article|main|post", re.I)) or soup.body or soup

    lines = []
    if title_text:
        lines.append(f"# {title_text}\n")
    if meta_desc_text:
        lines.append(f"> {meta_desc_text}\n")

    for elem in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre", "td"]):
        text = elem.get_text(strip=True)
        if not text or len(text) < 5:
            continue
        tag = elem.name
        if tag.startswith("h"):
            level = int(tag[1])
            lines.append(f"{'#' * level} {text}")
        elif tag == "li":
            parent = elem.find_parent(["ul", "ol"])
            indent = "  " if parent and parent.name == "ol" else "- "
            lines.append(f"{indent}{text}")
        elif tag == "blockquote":
            lines.append(f"> {text}")
        elif tag == "pre":
            lines.append(f"```\n{text}\n```")
        elif tag == "td":
            # 表格行处理
            row_text = " | ".join(td.get_text(strip=True) for td in elem.find_parent("tr").find_all(["td", "th"]) if td.get_text(strip=True))
            lines.append(f"| {row_text} |")
        else:
            lines.append(text)
        lines.append("")

    # 提取链接文本
    links = []
    for a in soup.find_all("a", href=True)[:10]:
        href = a["href"]
        text = a.get_text(strip=True)
        if text and len(text) > 3:
            links.append(f"- [{text}]({href})")

    if links:
        lines.append("\n## 相关链接\n")
        lines.extend(links)

    result = "\n".join(lines).strip()
    # 截断过长内容
    if len(result) > 8000:
        result = result[:8000] + f"\n\n...（内容已截断，原文共 {len(result)} 字符）"
    return result


# ==================== URL 安全校验 ====================

import ipaddress
import hashlib
import time as _time
from urllib.parse import urlparse

# 禁止访问的私有/回环/元数据地址
_BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]",
    "169.254.169.254",  # AWS/GCP/Azure 元数据
    "metadata.google.internal",
    "100.100.100.200",  # 阿里云元数据
}
_BLOCKED_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                     "172.20.", "172.21.", "172.22.", "172.23.",
                     "172.24.", "172.25.", "172.26.", "172.27.",
                     "172.28.", "172.29.", "172.30.", "172.31.",
                     "192.168.",)


def _validate_url(url: str) -> Optional[str]:
    """校验 URL 是否安全可访问，返回错误信息或 None。"""
    if not url or not isinstance(url, str):
        return "URL 不能为空"
    if not url.startswith(("http://", "https://")):
        return "URL 必须以 http:// 或 https:// 开头"
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        # 检查禁止列表
        if hostname.lower() in _BLOCKED_HOSTS:
            return f"禁止访问内网地址: {hostname}"
        # 检查私有 IP 前缀
        for prefix in _BLOCKED_PREFIXES:
            if hostname.startswith(prefix):
                return f"禁止访问私有地址: {hostname}"
        # 尝试解析 IP（非必须，但检测到 IP 是私有/回环时拒绝）
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return f"禁止访问私有/回环/链路本地地址: {hostname}"
        except ValueError:
            pass  # 域名，不做 DNS 解析（避免阻塞）
        return None
    except Exception as exc:
        return f"URL 解析失败: {exc}"


# ==================== URL 哈希去重缓存（LRU） ====================

_fetch_cache: dict[str, tuple[float, str]] = {}
_FETCH_CACHE_MAX = 200  # 最多缓存 200 条
FETCH_CACHE_TTL = 3600 * 6  # 6 小时缓存


def _cache_evict_if_needed() -> None:
    """缓存条目超过上限时淘汰最旧条目。"""
    if len(_fetch_cache) >= _FETCH_CACHE_MAX:
        oldest = min(_fetch_cache.keys(), key=lambda k: _fetch_cache[k][0])
        del _fetch_cache[oldest]


def _fetch_web_content_impl(url: str, max_length: int = 8000) -> str:
    """fetch_web_content 的内部实现：URL 安全校验 + 哈希去重 + 6h TTL 缓存。"""
    # 1. URL 安全校验（防 SSRF）
    url_error = _validate_url(url)
    if url_error:
        return f"[URL 不合法] {url_error}"

    # 2. 缓存检查
    url_hash = hashlib.md5(url.encode()).hexdigest()
    now = _time.time()
    if url_hash in _fetch_cache:
        ts, cached = _fetch_cache[url_hash]
        if now - ts < FETCH_CACHE_TTL:
            return f"[缓存] {cached}"

    # 3. 执行抓取
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # 处理编码
        encoding = response.apparent_encoding or "utf-8"
        if response.status_code == 200 and len(response.content) > 50:
            try:
                html_text = response.content.decode("utf-8")
            except UnicodeDecodeError:
                html_text = response.content.decode(encoding, errors="replace")
        else:
            html_text = response.text

        markdown_content = _clean_html_to_markdown(html_text, url)

        # 截断过长内容
        if len(markdown_content) > max_length:
            markdown_content = markdown_content[:max_length] + f"\n\n...（内容已截断，原文共 {len(markdown_content)} 字符）"

        # 缓存写入前淘汰旧条目
        _cache_evict_if_needed()
        _fetch_cache[url_hash] = (now, markdown_content)
        return markdown_content

    except requests.exceptions.Timeout:
        return f"[抓取超时] 请求 {url} 超时（15秒），请检查网络或稍后重试。"
    except requests.exceptions.HTTPError as e:
        return f"[HTTP 错误] {e.response.status_code} {e.response.reason}，URL: {url}"
    except requests.exceptions.RequestException as e:
        return f"[请求失败] {str(e)}，URL: {url}"
    except Exception as e:
        return f"[抓取失败] {type(e).__name__}: {str(e)}，URL: {url}"


@tool
def fetch_web_content(url: str) -> str:
    """获取网页内容并转为 Markdown，用于查询最新农业新闻、作物信息、政策通知等。

    当需要查询江西农业大学官网最新动态、科研成果、会议通知等信息时使用此工具。

    参数:
        url: 目标网页的完整 URL（必须以 http:// 或 https:// 开头）

    返回:
        网页的 Markdown 格式内容摘要，包含标题、正文和链接。
        相同 URL 在 6 小时内会返回缓存内容（标记为 [缓存] 前缀）。
    """
    return _fetch_web_content_impl(url)


# ==================== MCP 工具集成 ====================

class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self):
        self.mcp_tools: Dict[str, BaseTool] = {}
        self._initialize_mcp_tools()
    
    def _initialize_mcp_tools(self):
        """初始化 MCP 工具"""
        if settings.mcp_fetch_enabled:
            logger.info("MCP Fetch 工具已启用（使用内嵌 requests+BeautifulSoup 实现）")
        if settings.mcp_time_enabled:
            logger.info("MCP Time 工具已启用（需要启动 mcp-server-time）")
    
    def get_tools(self) -> List[BaseTool]:
        """获取所有可用工具"""
        tools = [
            query_crop_knowledge,
            get_current_datetime,
            calculate_growing_period,
            get_agri_weather,
            fetch_web_content,
            search_agri_resources,
        ]
        return tools

    def status(self) -> Dict[str, Any]:
        """Expose truthful MCP capability metadata for diagnostics and UI."""
        tools = self.get_tools()
        return {
            "mode": "embedded-mcp-compatible",
            "external_process_connected": False,
            "notice": "当前工具以内嵌适配器运行；未宣称已连接外部 MCP Server。",
            "tools": [
                {"name": tool.name, "description": (tool.description or "农业工具").split("\n", 1)[0]}
                for tool in tools
            ],
        }


def get_all_tools() -> List[BaseTool]:
    """获取所有工具（供 Agent 使用）"""
    manager = MCPToolManager()
    return manager.get_tools()


def get_mcp_status() -> Dict[str, Any]:
    return MCPToolManager().status()
