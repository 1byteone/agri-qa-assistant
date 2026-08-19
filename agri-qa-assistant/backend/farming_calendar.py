# -*- coding: utf-8 -*-
"""
江西农事日历模块 — 提供详细的作物种植日历和关键农时节点。

数据来源：
- 江西省农业厅种植业管理处公开发布的农时安排
- 国家水稻、油菜、柑橘产业技术体系的区域推荐
- Open-Meteo 公共气象数据
"""
from __future__ import annotations
import json
import logging
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── 江西作物种植日历 ─────────────────────────────────────────

# 每个作物的关键农时节点（月份:日, 表示该月第几天）
# 格式: { "节点名": (起始月, 起始日, 结束月, 结束日, 描述, 关键操作) }

JIANGXI_RICE_CALENDAR = {
    "早稻": {
        "品种选择": (1, 1, 2, 28, "选择适合江西的早稻品种", "挑选高产、抗病、生育期适中的品种"),
        "种子处理": (2, 15, 3, 15, "晒种、浸种催芽", "晴天晒种2-3天，浸种48小时，催芽至破胸露白"),
        "播种育秧": (3, 1, 3, 25, "播种和育秧管理", "秧田播种量40-50kg/亩，秧龄25-30天"),
        "秧田管理": (3, 10, 4, 5, "秧苗期水肥管理", "保持浅水层，适时施用断奶肥"),
        "移栽": (3, 25, 4, 20, "移栽定植", "栽插密度2万穴/亩，每穴3-4苗"),
        "分蘖期": (4, 20, 5, 30, "分蘖管理", "浅水促分蘖，够苗晒田控制无效分蘖"),
        "孕穗期": (6, 1, 6, 20, "孕穗管理", "保持水层，防治稻瘟病和纹枯病"),
        "抽穗扬花": (6, 15, 6, 30, "抽穗扬花期管理", "保持水层，叶面喷施磷酸二氢钾"),
        "灌浆成熟": (7, 1, 7, 15, "灌浆和收获", "干湿交替灌溉，七成熟时收割"),
    },
    "晚稻": {
        "品种选择": (4, 1, 5, 15, "选择适合江西的晚稻品种", "生育期120-130天的品种"),
        "播种育秧": (6, 15, 6, 30, "播种和育秧", "秧龄20-25天，防止秧苗老化"),
        "移栽": (7, 1, 7, 20, "移栽定植", "栽插密度2万穴/亩，抢时移栽"),
        "分蘖期": (7, 20, 8, 20, "分蘖管理", "浅水促分蘖，适时晒田"),
        "孕穗期": (8, 20, 9, 10, "孕穗管理", "防治稻飞虱和稻纵卷叶螟"),
        "抽穗扬花": (9, 5, 9, 20, "抽穗扬花期", "保持水层，防止寒露风危害"),
        "灌浆成熟": (9, 20, 10, 25, "灌浆和收获", "干湿交替，适时收获避免穗上发芽"),
    },
    "中稻": {
        "品种选择": (2, 1, 3, 15, "选择中稻品种", "生育期130-150天的品种"),
        "播种育秧": (4, 1, 4, 20, "播种育秧", "秧龄30-35天"),
        "移栽": (5, 1, 5, 25, "移栽定植", "栽插密度1.8万穴/亩"),
        "分蘖期": (5, 25, 7, 5, "分蘖管理", "浅水促分蘖，够苗晒田"),
        "孕穗期": (7, 5, 7, 25, "孕穗管理", "防治稻瘟病"),
        "抽穗扬花": (7, 20, 8, 10, "抽穗扬花", "保持水层，防止高温热害"),
        "灌浆成熟": (8, 10, 9, 15, "灌浆和收获", "干湿交替灌溉"),
    },
}

JIANGXI_RAPESEED_CALENDAR = {
    "油菜": {
        "品种选择": (8, 15, 9, 10, "选择适合江西的油菜品种", "选用双低油菜品种"),
        "播种育苗": (9, 15, 10, 5, "播种和育苗", "苗床播种量0.5-0.8kg/亩"),
        "移栽": (10, 5, 11, 10, "移栽定植", "栽插密度6000-8000株/亩"),
        "苗期管理": (10, 15, 12, 15, "苗期水肥管理", "追施提苗肥，中耕除草"),
        "越冬期": (12, 15, 2, 15, "越冬管理", "培土壅根防冻，清沟排渍"),
        "返青期": (2, 15, 3, 15, "返青管理", "追施返青肥，防治蚜虫"),
        "蕾薹期": (3, 1, 3, 30, "蕾薹期管理", "重施蕾薹肥，防治菌核病"),
        "开花期": (3, 20, 4, 15, "开花期管理", "叶面喷施硼肥，防治菌核病"),
        "角果期": (4, 10, 5, 10, "角果发育期", "保持适宜水分，防止裂角"),
        "收获": (5, 5, 5, 25, "收获", "八成熟时割晒，后熟5-7天脱粒"),
    },
}

JIANGXI_CITRUS_CALENDAR = {
    "柑橘": {
        "春季管理": (2, 15, 3, 15, "春季管理", "施春肥（氮为主），修剪枯枝病枝"),
        "萌芽期": (3, 1, 3, 20, "萌芽管理", "喷施石硫合剂清园，防治红蜘蛛"),
        "花期": (4, 1, 4, 20, "花期管理", "保花保果，喷施赤霉素"),
        "生理落果期": (4, 20, 5, 30, "落果管理", "喷施2,4-D保果，控制夏梢"),
        "果实膨大期": (6, 1, 8, 31, "膨大期管理", "追施壮果肥（钾为主），灌溉防旱"),
        "秋梢期": (7, 15, 8, 31, "秋梢管理", "放秋梢，防治潜叶蛾"),
        "果实转色期": (9, 1, 10, 31, "转色管理", "喷施叶面钾肥，促进着色"),
        "采收期": (11, 1, 12, 15, "采收", "赣南脐橙11月中旬开始采收"),
        "冬季管理": (12, 15, 2, 15, "冬季清园", "施冬肥（有机肥为主），涂白防冻"),
    },
}

# 赣南脐橙特有日历（更详细）
JIANGXI_GANNAN_CALENDAR = {
    "赣南脐橙": {
        "冬季清园": (12, 20, 2, 10, "冬季清园管理", "喷施石硫合剂，清除病枝落叶"),
        "春季施肥": (2, 10, 3, 5, "春季施肥", "施用速效氮肥，促进萌芽"),
        "萌芽抽梢": (3, 1, 3, 25, "萌芽抽梢期", "防治红蜘蛛、蚜虫"),
        "花期管理": (4, 5, 4, 25, "花期管理", "保花保果，喷施硼肥"),
        "第一次生理落果": (4, 25, 5, 15, "第一次落果", "喷施2,4-D保果"),
        "第二次生理落果": (5, 15, 6, 10, "第二次落果", "控制夏梢，减少落果"),
        "果实膨大期": (6, 1, 8, 31, "果实膨大期", "追施壮果肥，灌溉防旱"),
        "秋梢管理": (7, 20, 8, 31, "秋梢管理", "统一放梢，防治潜叶蛾"),
        "果实着色": (9, 15, 11, 5, "着色期", "喷施钾肥，促进着色"),
        "采收期": (11, 10, 12, 10, "采收期", "赣南脐橙11月中旬开始采收"),
        "采后管理": (12, 10, 12, 31, "采后管理", "施采后肥，修剪整形"),
    },
}

# 合并所有日历
ALL_CALENDARS = {
    **JIANGXI_RICE_CALENDAR,
    **JIANGXI_RAPESEED_CALENDAR,
    **JIANGXI_CITRUS_CALENDAR,
    **JIANGXI_GANNAN_CALENDAR,
}

# 作物别名映射
CROP_ALIASES = {
    "水稻": "水稻",
    "稻": "水稻",
    "早稻": "早稻",
    "晚稻": "晚稻",
    "中稻": "中稻",
    "油菜": "油菜",
    "菜籽": "油菜",
    "柑橘": "柑橘",
    "橘子": "柑橘",
    "脐橙": "柑橘",
    "赣南脐橙": "赣南脐橙",
    "脐橙": "赣南脐橙",
}


# ── 农事日历查询 ─────────────────────────────────────────────

class FarmingCalendar:
    """江西农事日历查询接口。"""

    def __init__(self, reference_date: Optional[date] = None):
        self.reference_date = reference_date or date.today()

    def get_current_activities(self, crop: str) -> List[Dict[str, Any]]:
        """获取指定作物当前（今天）应进行的农事活动。

        Parameters
        ----------
        crop : str
            作物名称。

        Returns
        -------
        list of dict
            当前应进行的活动列表，每个活动包含节点名、描述、关键操作。
        """
        crop_key = CROP_ALIASES.get(crop, crop)
        if crop_key not in ALL_CALENDARS:
            return []

        activities = []
        today = self.reference_date
        calendar = ALL_CALENDARS[crop_key]

        for stage_name, (start_month, start_day, end_month, end_day, desc, key_ops) in calendar.items():
            start = date(today.year, start_month, start_day)
            end = date(today.year, end_month, end_day)

            # 处理跨年的情况（如越冬期）
            if start > end:
                # 当前日期在年内
                if today >= start or today <= end:
                    activities.append({
                        "stage": stage_name,
                        "description": desc,
                        "key_operations": key_ops,
                        "period": f"{start_month}月{start_day}日 - {end_month}月{end_day}日",
                    })
            else:
                if start <= today <= end:
                    activities.append({
                        "stage": stage_name,
                        "description": desc,
                        "key_operations": key_ops,
                        "period": f"{start_month}月{start_day}日 - {end_month}月{end_day}日",
                    })

        return activities

    def get_upcoming_activities(self, crop: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取指定作物未来 N 天的农事活动。

        Parameters
        ----------
        crop : str
            作物名称。
        days : int
            未来天数。

        Returns
        -------
        list of dict
            未来活动列表。
        """
        crop_key = CROP_ALIASES.get(crop, crop)
        if crop_key not in ALL_CALENDARS:
            return []

        activities = []
        today = self.reference_date
        future = today + timedelta(days=days)
        calendar = ALL_CALENDARS[crop_key]

        for stage_name, (start_month, start_day, end_month, end_day, desc, key_ops) in calendar.items():
            start = date(today.year, start_month, start_day)
            end = date(today.year, end_month, end_day)

            # 处理跨年的情况
            if start > end:
                # 检查未来区间是否与活动区间重叠
                if not (future < start and future < end):
                    activities.append({
                        "stage": stage_name,
                        "description": desc,
                        "key_operations": key_ops,
                        "period": f"{start_month}月{start_day}日 - {end_month}月{end_day}日",
                    })
            else:
                # 检查未来区间是否与活动区间重叠
                if start <= future and end >= today:
                    activities.append({
                        "stage": stage_name,
                        "description": desc,
                        "key_operations": key_ops,
                        "period": f"{start_month}月{start_day}日 - {end_month}月{end_day}日",
                    })

        return activities

    def get_crop_calendar(self, crop: str) -> Dict[str, Any]:
        """获取指定作物的完整种植日历。

        Returns
        -------
        dict
            包含作物名称、日历节点列表的字典。
        """
        crop_key = CROP_ALIASES.get(crop, crop)
        if crop_key not in ALL_CALENDARS:
            return {"ok": False, "crop": crop, "message": "暂无该作物的详细日历"}

        calendar = ALL_CALENDARS[crop_key]
        stages = []
        for stage_name, (start_month, start_day, end_month, end_day, desc, key_ops) in calendar.items():
            stages.append({
                "stage": stage_name,
                "period": f"{start_month}月{start_day}日 - {end_month}月{end_day}日",
                "description": desc,
                "key_operations": key_ops,
            })

        return {"ok": True, "crop": crop_key, "region": "江西", "stages": stages}

    def check_weather_risk(self, crop: str, weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据天气预报检查农事风险。

        Parameters
        ----------
        crop : str
            作物名称。
        weather_data : dict
            Open-Meteo 天气预报数据（daily 格式）。

        Returns
        -------
        list of dict
            风险警告列表。
        """
        risks = []
        daily = weather_data.get("daily", [])
        crop_key = CROP_ALIASES.get(crop, crop)
        activities = self.get_current_activities(crop_key)

        if not activities:
            return risks

        for day_data in daily:
            date_str = day_data.get("date", "")
            temp_max = day_data.get("temperature_max_c")
            temp_min = day_data.get("temperature_min_c")
            precipitation = day_data.get("precipitation_mm", 0)
            weather_code = day_data.get("weather_code", 0)

            # 高温风险（水稻抽穗扬花期）
            if temp_max and temp_max >= 35:
                for act in activities:
                    if any(k in act["stage"] for k in ["抽穗", "扬花", "开花", "孕穗"]):
                        risks.append({
                            "date": date_str,
                            "risk_type": "high_temperature",
                            "severity": "critical" if temp_max >= 37 else "elevated",
                            "message": f"高温天气（{temp_max}°C）可能影响{crop}的{act['stage']}，建议采取灌溉降温措施。",
                            "mitigation": "傍晚灌溉降温，叶面喷施磷酸二氢钾",
                        })

            # 低温/霜冻风险
            if temp_min and temp_min <= 4:
                for act in activities:
                    if any(k in act["stage"] for k in ["苗期", "越冬", "返青", "萌芽", "花期", "播种", "育秧", "种子处理"]):
                        risks.append({
                            "date": date_str,
                            "risk_type": "frost",
                            "severity": "critical" if temp_min <= 0 else "elevated",
                            "message": f"低温天气（{temp_min}°C）可能对{crop}的{act['stage']}造成冻害。",
                            "mitigation": "覆盖保温，灌水防冻，熏烟防霜",
                        })

            # 暴雨风险
            if precipitation and precipitation >= 50:
                risks.append({
                    "date": date_str,
                    "risk_type": "heavy_rain",
                    "severity": "elevated",
                    "message": f"暴雨天气（{precipitation}mm）可能造成{crop}田间积水。",
                    "mitigation": "及时排水，疏通沟渠，防止渍害",
                })

            # 连续降雨风险（通过天气代码判断）
            if weather_code in (61, 63, 65, 71, 73, 75, 80, 81, 82):  # 各类降雨
                for act in activities:
                    if any(k in act["stage"] for k in ["收获", "采收", "脱粒"]):
                        risks.append({
                            "date": date_str,
                            "risk_type": "harvest_rain",
                            "severity": "normal",
                            "message": f"降雨天气可能影响{crop}的{act['stage']}，建议抢晴收获。",
                            "mitigation": "密切关注天气，抢晴收获，做好晾晒准备",
                        })

        return risks


# ── 天气预警注入 ─────────────────────────────────────────────

def build_weather_alert_context(
    crop: str,
    weather_data: Dict[str, Any],
    reference_date: Optional[date] = None,
) -> str:
    """根据天气预报和当前农事活动生成天气预警上下文，注入对话。

    Parameters
    ----------
    crop : str
        作物名称。
    weather_data : dict
        Open-Meteo 天气预报数据。
    reference_date : date, optional
        参考日期。

    Returns
    -------
    str
        格式化的天气预警上下文文本。
    """
    calendar = FarmingCalendar(reference_date)
    activities = calendar.get_current_activities(crop)
    risks = calendar.check_weather_risk(crop, weather_data)

    if not activities and not risks:
        return ""

    lines = ["## 天气与农事预警\n"]

    if activities:
        lines.append("当前农事活动：")
        for act in activities:
            lines.append(f"- **{act['stage']}**（{act['period']}）：{act['description']}")
            lines.append(f"  关键操作：{act['key_operations']}")
        lines.append("")

    if risks:
        lines.append("⚠️ 天气风险预警：")
        for risk in risks:
            severity_icon = "🔴" if risk["severity"] == "critical" else "🟡"
            lines.append(f"- {severity_icon} {risk['message']}")
            lines.append(f"  应对措施：{risk['mitigation']}")
    else:
        lines.append("当前天气条件总体适宜农事活动。")

    return "\n".join(lines)


# ── 全局实例 ─────────────────────────────────────────────────

farming_calendar = FarmingCalendar()
