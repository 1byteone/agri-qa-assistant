#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2023、2024 年种植业数据清洗、结构分析与纯 HTML 报告生成器。

运行方式：
    python analysis.py

输出：
    data/cleaned_2023.csv
    data/cleaned_2024.csv
    report_2023.html
    report_2024.html
    analysis_summary.json
"""

from __future__ import annotations

import html
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "data" / "2024年种植业数据.csv"
OUTPUT_DIR = BASE_DIR
CLEANED_DIR = BASE_DIR / "data"

CATEGORIES = ("粮食作物", "经济作物", "其他作物")
CATEGORY_COLORS = {
    "粮食作物": "#1f7a5a",
    "经济作物": "#e18b32",
    "其他作物": "#6b7c93",
}

# ── 省份简称 → 全称（ECharts 地图用） ────────────────────────────────
PROVINCE_FULL_NAMES = {
    "北京": "北京市", "天津": "天津市", "河北": "河北省", "山西": "山西省",
    "内蒙古": "内蒙古自治区", "辽宁": "辽宁省", "吉林": "吉林省", "黑龙江": "黑龙江省",
    "上海": "上海市", "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省",
    "福建": "福建省", "江西": "江西省", "山东": "山东省", "河南": "河南省",
    "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "广西": "广西壮族自治区",
    "海南": "海南省", "重庆": "重庆市", "四川": "四川省", "贵州": "贵州省",
    "云南": "云南省", "西藏": "西藏自治区", "陕西": "陕西省", "甘肃": "甘肃省",
    "青海": "青海省", "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "全国": "全国",
}

# ── 作物品类独立色（金 → 绿 → 蓝，按类别分组） ─────────────────────
CROP_COLORS = {
    # 粮食作物 — 金色/橙色系
    "粮食": "#f59e0b", "谷物": "#d97706", "稻谷": "#f97316",
    "早稻": "#fb923c", "中稻和一季晚稻": "#fbbf24", "双季晚稻": "#fcd34d",
    "小麦": "#eab308", "冬小麦": "#ca8a04", "春小麦": "#a16207",
    "玉米": "#f59e0b", "大豆": "#65a30d", "豆类": "#4d7c0f",
    "薯类": "#92400e", "马铃薯": "#78350f", "红小豆": "#dc2626",
    "绿豆": "#16a34a", "夏粮": "#fde047", "秋粮": "#fef08a",
    "其他谷物": "#a3e635", "谷子": "#84cc16", "高粱": "#b45309",
    "杂粮": "#fca5a5",
    # 经济作物 — 绿色/青色系
    "油料": "#10b981", "油菜籽": "#059669", "花生": "#34d399",
    "芝麻": "#6ee7b7", "胡麻籽": "#a7f3d0", "向日葵籽": "#fbbf24",
    "棉花": "#06b6d4", "糖料": "#0891b2", "甘蔗": "#0e7490",
    "甜菜": "#22d3ee", "蔬菜": "#10b981", "瓜果类": "#34d399",
    "甜瓜": "#6ee7b7", "西瓜": "#86efac", "草莓": "#ef4444",
    "果园": "#059669", "苹果": "#22c55e", "苹果园": "#16a34a",
    "梨": "#65a30d", "梨园": "#4d7c0f", "葡萄": "#a855f7",
    "葡萄园": "#7c3aed", "香蕉": "#eab308", "香蕉园": "#ca8a04",
    "柑桔": "#f97316", "柑桔园": "#fb923c", "柿子": "#f59e0b",
    "红枣": "#dc2626", "菠萝": "#fbbf24", "茶叶": "#059669",
    "其他茶": "#10b981", "青茶": "#34d399", "白茶": "#6ee7b7",
    "黄茶": "#a7f3d0", "黑茶": "#78350f", "茶园": "#047857",
    "烟叶": "#8b5cf6", "烤烟": "#7c3aed", "药材": "#a78bfa",
    "柞蚕茧": "#c084fc", "桑蚕茧": "#d8b4fe", "蚕茧": "#e9d5ff",
    "麻类": "#6366f1", "黄红麻": "#4f46e5", "苎麻": "#4338ca",
    "亚麻": "#3730a3", "大麻(线麻)": "#312e81",
    "蔬菜(含菜用瓜)": "#10b981",
    # 其他作物
    "青饲料": "#6b7c93", "绿肥": "#64748b",
}

# 按用户给出的农业统计口径补充常见品类。
STAPLE_CROPS = {
    "水稻", "稻谷", "小麦", "玉米", "大豆", "薯类", "马铃薯", "谷物", "谷子", "高粱", "豆类",
    "红小豆", "绿豆", "粮食", "夏粮", "秋粮", "早稻", "春小麦", "冬小麦",
    "中稻和一季晚稻", "双季晚稻", "杂粮", "其他谷物",
}
ECONOMIC_CROPS = {
    "油料", "油菜籽", "花生", "芝麻", "胡麻籽", "向日葵籽", "棉花", "糖料",
    "甘蔗", "甜菜", "蔬菜", "瓜果类", "甜瓜", "菠萝", "水果", "果园", "苹果", "梨", "梨园",
    "葡萄", "葡萄园", "香蕉", "香蕉园", "柑桔", "柑桔园", "柿子", "红枣", "茶叶", "其他茶", "茶园",
    "烟叶", "烤烟", "药材", "柞蚕茧", "桑蚕茧", "蚕茧", "麻类", "黄红麻",
}


def read_csv(path: Path) -> pd.DataFrame:
    """兼容常见中文 CSV 编码并校验必要字段。"""
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            frame = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError as error:
            last_error = error
    else:
        raise RuntimeError(f"无法读取 CSV 编码：{path}") from last_error

    required = {"年份", "品类", "指标", "省份", "数值", "单位"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"CSV 缺少必要字段：{sorted(missing)}")
    return frame


def clean_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """执行清洗并统一指标、产量和面积单位。"""
    data = frame.copy()
    data["数值"] = pd.to_numeric(data["数值"], errors="coerce")
    data["指标"] = data["指标"].astype("string").str.strip()
    data["品类"] = data["品类"].astype("string").str.strip()
    data["单位"] = data["单位"].astype("string").str.strip()
    data["省份"] = data["省份"].astype("string").str.strip()

    invalid_count = int(data["数值"].isna().sum())
    data = data.dropna(subset=["数值"]).copy()
    zero_mask = data["数值"].eq(0)
    zero_removed = int(zero_mask.sum())
    data = data.loc[~zero_mask].copy()

    per_capita_mask = data["品类"].str.contains("人均", na=False)
    per_capita_removed = int(per_capita_mask.sum())
    data = data.loc[~per_capita_mask].copy()

    # 数据中既有“播种面积”，也可能出现“播种面积/种植面积”。统一为用户要求的名称。
    indicator_map = {
        "播种面积": "种植面积",
        "播种面积/种植面积": "种植面积",
        "种植面积": "种植面积",
    }
    data["指标"] = data["指标"].replace(indicator_map)

    production_mask = data["指标"].eq("产量") & data["单位"].eq("万吨")
    production_converted = int(production_mask.sum())
    data.loc[production_mask, "数值"] *= 10000
    data.loc[production_mask, "单位"] = "吨"

    # 1 千公顷 = 1,000 公顷；1 公顷 = 15 亩，因此 1 千公顷 = 15,000 亩。
    area_mask = data["指标"].eq("种植面积") & data["单位"].eq("千公顷")
    area_converted = int(area_mask.sum())
    data.loc[area_mask, "数值"] *= 15000
    data.loc[area_mask, "单位"] = "亩"

    stats = {
        "raw_count": int(len(frame)),
        "invalid_removed": invalid_count,
        "zero_removed": zero_removed,
        "per_capita_removed": per_capita_removed,
        "production_converted": production_converted,
        "area_converted": area_converted,
        "cleaned_count": int(len(data)),
    }
    return data.reset_index(drop=True), stats


def classify_crop(crop_name: str) -> str:
    """按农业生产常识将品类划分为粮食、经济和其他作物。"""
    name = str(crop_name).strip()
    if name in STAPLE_CROPS:
        return "粮食作物"
    if name in ECONOMIC_CROPS:
        return "经济作物"

    # 对未在清单中出现但具有明显语义的新增品类进行稳健归类。
    if any(keyword in name for keyword in ("粮", "稻", "麦", "玉米", "豆", "薯")):
        return "粮食作物"
    if any(keyword in name for keyword in ("油", "棉", "糖", "菜", "果", "茶", "烟", "药材")):
        return "经济作物"
    return "其他作物"


def choose_reporting_rows(year_data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """消除全国、省份重复统计，形成用于结构分析的代表性记录。

    同一“品类+指标”若存在全国记录，优先采用全国记录；只有没有全国记录时，
    才将可用省份记录相加。这符合统计报表中“全国汇总优先”的实际场景。
    """
    records: list[dict[str, Any]] = []
    national_groups = 0
    province_sum_groups = 0

    group_columns = ["品类", "指标", "单位"]
    for keys, group in year_data.groupby(group_columns, dropna=False, sort=False):
        crop, indicator, unit = keys
        national = group[group["省份"].eq("全国")]
        if not national.empty:
            value = float(national["数值"].sum())
            scope = "全国汇总"
            national_groups += 1
        else:
            value = float(group["数值"].sum())
            scope = "省份加总（无全国汇总）"
            province_sum_groups += 1

        records.append({
            "品类": str(crop),
            "指标": str(indicator),
            "单位": str(unit),
            "数值": value,
            "统计口径": scope,
            "作物类别": classify_crop(str(crop)),
        })

    selected = pd.DataFrame(records)
    stats = {
        "national_groups": national_groups,
        "province_sum_groups": province_sum_groups,
    }
    return selected, stats


def summarize(year_data: pd.DataFrame) -> dict[str, Any]:
    """生成某一年度的作物类型和品类级汇总。"""
    reporting, scope_stats = choose_reporting_rows(year_data)
    production = reporting[reporting["指标"].eq("产量") & reporting["单位"].eq("吨")]
    area = reporting[reporting["指标"].eq("种植面积") & reporting["单位"].eq("亩")]

    category_rows = []
    for category in CATEGORIES:
        production_value = float(production.loc[production["作物类别"].eq(category), "数值"].sum())
        area_value = float(area.loc[area["作物类别"].eq(category), "数值"].sum())
        category_rows.append({
            "category": category,
            "production": production_value,
            "area": area_value,
        })

    production_by_crop = (
        production.groupby(["作物类别", "品类"], as_index=False)["数值"]
        .sum()
        .rename(columns={"数值": "value"})
    )
    area_by_crop = (
        area.groupby(["作物类别", "品类"], as_index=False)["数值"]
        .sum()
        .rename(columns={"数值": "value"})
    )

    return {
        "categories": category_rows,
        "production_by_crop": production_by_crop.to_dict("records"),
        "area_by_crop": area_by_crop.to_dict("records"),
        "scope": scope_stats,
    }


def number(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def percent(value: float, total: float) -> str:
    return f"{value / total * 100:.2f}%" if total else "0.00%"


def polar(cx: float, cy: float, radius: float, angle: float) -> tuple[float, float]:
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def pie_svg(category_data: list[dict[str, Any]], metric: str, unit: str) -> str:
    """生成不依赖外部 CDN 的 SVG 饼图，保证报告是纯 HTML。"""
    values = [(row["category"], float(row[metric])) for row in category_data]
    total = sum(value for _, value in values)
    cx, cy, radius = 180, 180, 145
    paths: list[str] = []
    angle = -math.pi / 2

    for category, value in values:
        if total <= 0 or value <= 0:
            continue
        sweep = value / total * math.tau
        start = polar(cx, cy, radius, angle)
        end = polar(cx, cy, radius, angle + sweep)
        large_arc = 1 if sweep > math.pi else 0
        path = (
            f"M {cx} {cy} L {start[0]:.2f} {start[1]:.2f} "
            f"A {radius} {radius} 0 {large_arc} 1 {end[0]:.2f} {end[1]:.2f} Z"
        )
        paths.append(
            f'<path d="{path}" fill="{CATEGORY_COLORS[category]}" '
            f' stroke="#ffffff" stroke-width="2"><title>{html.escape(category)}：'
            f'{number(value)} {html.escape(unit)}（{percent(value, total)}）</title></path>'
        )
        angle += sweep

    legend = "".join(
        f'<li><span class="legend-color" style="background:{CATEGORY_COLORS[category]}"></span>'
        f'{html.escape(category)}：{number(value)} {html.escape(unit)}（{percent(value, total)}）</li>'
        for category, value in values
    )
    return (
        '<div class="pie-wrap">'
        f'<svg class="pie" viewBox="0 0 360 360" role="img" aria-label="{html.escape(metric)}结构饼图">'
        + "".join(paths)
        + '</svg><ul class="legend">'
        + legend
        + "</ul></div>"
    )


def rows_html(rows: list[dict[str, Any]], metric: str, unit: str, total: float) -> str:
    sorted_rows = sorted(rows, key=lambda row: float(row["value"]), reverse=True)[:10]
    if not sorted_rows:
        return '<tr><td colspan="4">暂无可用数据</td></tr>'
    return "".join(
        f"<tr><td>{index}</td><td>{html.escape(str(row['作物类别']))}</td>"
        f"<td>{html.escape(str(row['品类']))}</td><td>{number(float(row['value']))} {html.escape(unit)}</td>"
        f"<td>{percent(float(row['value']), total)}</td></tr>"
        for index, row in enumerate(sorted_rows, 1)
    )


def interpretation(category_data: list[dict[str, Any]]) -> str:
    production_total = sum(float(row["production"]) for row in category_data)
    area_total = sum(float(row["area"]) for row in category_data)
    production_leader = max(category_data, key=lambda row: float(row["production"]))
    area_leader = max(category_data, key=lambda row: float(row["area"]))
    production_gap = max(
        category_data,
        key=lambda row: (float(row["production"]) / production_total if production_total else 0)
        - (float(row["area"]) / area_total if area_total else 0),
    )
    return (
        f"本年度结构中，{html.escape(production_leader['category'])}产量占比"
        f"{percent(float(production_leader['production']), production_total)}，"
        f"{html.escape(area_leader['category'])}种植面积占比"
        f"{percent(float(area_leader['area']), area_total)}。"
        f"从“产量占比−面积占比”观察，{html.escape(production_gap['category'])}的单位面积产出相对更有优势；"
        "该结论仅反映统计口径下的结构效率，不等同于经济收益率，因为数据未包含价格、成本和质量信息。"
    )


def generate_report(year: int, raw_count: int, clean_stats: dict[str, int], summary: dict[str, Any], output_path: Path) -> None:
    categories = summary["categories"]
    production_total = sum(float(row["production"]) for row in categories)
    area_total = sum(float(row["area"]) for row in categories)
    production_rows = summary["production_by_crop"]
    area_rows = summary["area_by_crop"]
    scope = summary["scope"]
    category_table = "".join(
        f"<tr><td>{row['category']}</td><td>{number(row['production'])} 吨</td>"
        f"<td>{percent(row['production'], production_total)}</td><td>{number(row['area'])} 亩</td>"
        f"<td>{percent(row['area'], area_total)}</td></tr>"
        for row in categories
    )
    production_table = rows_html(production_rows, "production", "吨", production_total)
    area_table = rows_html(area_rows, "area", "亩", area_total)
    production_chart = pie_svg(categories, "production", "吨")
    area_chart = pie_svg(categories, "area", "亩")
    safe_year = html.escape(str(year))

    document = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_year}年种植业数据分析报告</title>
<style>
:root {{ --ink:#1f2937; --muted:#64748b; --line:#e2e8f0; --bg:#f5f7fb; --brand:#155e75; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Microsoft YaHei",system-ui,sans-serif; line-height:1.7; }}
main {{ max-width:1240px; margin:0 auto; padding:28px 18px 56px; }} header {{ padding:36px; color:#fff; border-radius:18px; background:linear-gradient(120deg,#155e75,#0f766e); box-shadow:0 12px 30px #0f172a22; }}
h1 {{ margin:0 0 8px; font-size:clamp(26px,4vw,42px); }} header p {{ margin:0; opacity:.9; }} section {{ background:#fff; border-radius:16px; padding:26px; margin-top:22px; box-shadow:0 5px 18px #0f172a0c; }} h2 {{ margin:0 0 18px; color:var(--brand); }} h3 {{ color:#334155; margin:22px 0 10px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; }} .card {{ padding:18px; border:1px solid var(--line); border-radius:12px; background:#f8fafc; }} .card strong {{ display:block; font-size:25px; color:var(--brand); }} .card small {{ color:var(--muted); }}
.charts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:18px; }} .chart {{ border:1px solid var(--line); border-radius:14px; padding:16px; }} .pie-wrap {{ display:flex; align-items:center; justify-content:center; gap:12px; min-height:330px; }} .pie {{ width:min(56%,340px); min-width:220px; }} .legend {{ list-style:none; padding:0; margin:0; color:#475569; }} .legend li {{ margin:8px 0; white-space:nowrap; }} .legend-color {{ display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:7px; }}
table {{ width:100%; border-collapse:collapse; margin:10px 0; font-size:14px; }} th,td {{ border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; }} th {{ color:#475569; background:#f8fafc; }} .note {{ border-left:4px solid #e18b32; background:#fff7ed; padding:14px 16px; color:#7c2d12; }} .muted {{ color:var(--muted); font-size:14px; }} footer {{ text-align:center; color:var(--muted); margin-top:24px; font-size:13px; }}
@media (max-width:700px) {{ section,header {{ padding:20px; }} .pie-wrap {{ flex-direction:column; }} .pie {{ width:90%; }} table {{ display:block; overflow-x:auto; white-space:nowrap; }} }}
</style>
</head>
<body><main>
<header><h1>{safe_year}年种植业数据分析报告</h1><p>独立年度分析 · 数据清洗 · 农作物结构 · 统计口径说明</p></header>
<section><h2>一、执行摘要</h2><div class="cards">
<div class="card"><small>原始记录</small><strong>{raw_count:,}</strong><small>行</small></div>
<div class="card"><small>清洗后记录</small><strong>{clean_stats['cleaned_count']:,}</strong><small>行</small></div>
<div class="card"><small>产量总量</small><strong>{number(production_total, 0)}</strong><small>吨</small></div>
<div class="card"><small>面积总量</small><strong>{number(area_total, 0)}</strong><small>亩</small></div>
</div><p>{interpretation(categories)}</p></section>
<section><h2>二、数据清洗与统计口径</h2>
<table><thead><tr><th>处理项目</th><th>结果</th></tr></thead><tbody>
<tr><td>删除数值为 0</td><td>{clean_stats['zero_removed']:,} 行</td></tr>
<tr><td>删除“人均”品类</td><td>{clean_stats['per_capita_removed']:,} 行</td></tr>
<tr><td>无效数值</td><td>{clean_stats['invalid_removed']:,} 行</td></tr>
<tr><td>产量：万吨 → 吨</td><td>{clean_stats['production_converted']:,} 行，乘以 10,000</td></tr>
<tr><td>面积：千公顷 → 亩</td><td>{clean_stats['area_converted']:,} 行，乘以 15,000</td></tr>
<tr><td>指标名称</td><td>播种面积、播种面积/种植面积统一为种植面积</td></tr>
</tbody></table>
<div class="note">统计防重规则：同一品类和指标存在“全国”记录时，只采用全国汇总；没有全国记录时，才对省份记录加总。本年度采用全国汇总 {scope['national_groups']} 组，省份加总 {scope['province_sum_groups']} 组，避免全国与省份重复计算。</div>
</section>
<section><h2>三、农作物结构饼图</h2><div class="charts">
<div class="chart"><h3>产量结构</h3>{production_chart}</div>
<div class="chart"><h3>种植面积结构</h3>{area_chart}</div>
</div></section>
<section><h2>四、类别汇总</h2><table><thead><tr><th>作物类别</th><th>产量</th><th>产量占比</th><th>种植面积</th><th>面积占比</th></tr></thead><tbody>{category_table}</tbody></table></section>
<section><h2>五、品类排名与报告解读</h2><h3>产量排名前 10</h3><table><thead><tr><th>排名</th><th>作物类别</th><th>品类</th><th>产量</th><th>占全部产量</th></tr></thead><tbody>{production_table}</tbody></table>
<h3>种植面积排名前 10</h3><table><thead><tr><th>排名</th><th>作物类别</th><th>品类</th><th>种植面积</th><th>占全部面积</th></tr></thead><tbody>{area_table}</tbody></table>
<div class="note"><strong>解读：</strong>{interpretation(categories)} 建议在保持粮食作物安全底盘的同时，结合区域水土资源、市场价格和加工能力，发展具有比较优势的经济作物；后续若要评价经济效益，还应补充成本、价格、亩均收益和灌溉等数据。</div></section>
<footer>数据来源：2024年种植业数据.csv · 本报告由 analysis.py 生成 · 图表为内嵌 SVG，无外部网络依赖</footer>
</main></body></html>'''
    output_path.write_text(document, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════
#  3D Dashboard Data Generator
# ═══════════════════════════════════════════════════════════════════

def _aggregate_province(
    cleaned: pd.DataFrame, year: int
) -> list[dict[str, Any]]:
    """按省份聚合产量和面积（已清洗、全国优先规则已应用）。"""
    records: list[dict[str, Any]] = []
    for prov in sorted(cleaned["省份"].unique()):
        sub = cleaned[cleaned["省份"].eq(prov)]
        prod = float(
            sub.loc[
                sub["指标"].eq("产量") & sub["单位"].eq("吨"), "数值"
            ].sum()
        )
        area = float(
            sub.loc[
                sub["指标"].eq("种植面积") & sub["单位"].eq("亩"), "数值"
            ].sum()
        )
        records.append(
            {
                "year": year,
                "province": str(prov),
                "provinceFull": PROVINCE_FULL_NAMES.get(str(prov), str(prov)),
                "production": round(prod, 2),
                "area": round(area, 2),
            }
        )
    return records


def generate_dashboard_data(
    year_results: dict[str, dict[str, Any]],
    cleaned_data: dict[int, pd.DataFrame],
) -> dict[str, Any]:
    """组装前端 3D 大屏所需的全量数据包。"""
    # ── 年份级 KPI ──
    kpi: dict[str, dict[str, float]] = {}
    categories_data: dict[str, list[dict[str, Any]]] = {}
    production_by_crop: dict[str, list[dict[str, Any]]] = {}
    area_by_crop: dict[str, list[dict[str, Any]]] = {}
    province_data: list[dict[str, Any]] = []

    for year_str, result in year_results.items():
        year = int(year_str)
        cats = result["summary"]["categories"]
        prod_total = sum(float(c["production"]) for c in cats)
        area_total = sum(float(c["area"]) for c in cats)
        food_prod = next(
            (float(c["production"]) for c in cats if c["category"] == "粮食作物"), 0.0
        )
        food_area = next(
            (float(c["area"]) for c in cats if c["category"] == "粮食作物"), 0.0
        )
        econ_prod = next(
            (float(c["production"]) for c in cats if c["category"] == "经济作物"), 0.0
        )
        econ_area = next(
            (float(c["area"]) for c in cats if c["category"] == "经济作物"), 0.0
        )
        kpi[str(year)] = {
            "total_production": round(prod_total, 2),
            "total_area": round(area_total, 2),
            "food_production": round(food_prod, 2),
            "food_area": round(food_area, 2),
            "food_production_pct": round(food_prod / prod_total * 100, 2) if prod_total else 0,
            "food_area_pct": round(food_area / area_total * 100, 2) if area_total else 0,
            "economic_production": round(econ_prod, 2),
            "economic_area": round(econ_area, 2),
            "economic_production_pct": round(econ_prod / prod_total * 100, 2) if prod_total else 0,
            "economic_area_pct": round(econ_area / area_total * 100, 2) if area_total else 0,
        }
        categories_data[str(year)] = [
            {
                "name": c["category"],
                "production": round(float(c["production"]), 2),
                "area": round(float(c["area"]), 2),
                "color": CATEGORY_COLORS.get(c["category"], "#94a3b8"),
            }
            for c in cats
        ]
        production_by_crop[str(year)] = [
            {
                "category": r["作物类别"],
                "crop": r["品类"],
                "value": round(float(r["value"]), 2),
                "color": CROP_COLORS.get(r["品类"], "#94a3b8"),
            }
            for r in result["summary"]["production_by_crop"]
        ]
        area_by_crop[str(year)] = [
            {
                "category": r["作物类别"],
                "crop": r["品类"],
                "value": round(float(r["value"]), 2),
                "color": CROP_COLORS.get(r["品类"], "#94a3b8"),
            }
            for r in result["summary"]["area_by_crop"]
        ]
        if year in cleaned_data:
            province_data.extend(_aggregate_province(cleaned_data[year], year))

    # ── 同比变化 ──
    yoy: dict[str, Any] = {}
    years_list = sorted(year_results.keys())
    if len(years_list) >= 2:
        y1, y2 = years_list[0], years_list[1]
        k1, k2 = kpi[y1], kpi[y2]
        yoy = {
            "production_change_pct": round(
                (k2["total_production"] - k1["total_production"])
                / k1["total_production"]
                * 100,
                2,
            )
            if k1["total_production"]
            else 0,
            "area_change_pct": round(
                (k2["total_area"] - k1["total_area"]) / k1["total_area"] * 100, 2
            )
            if k1["total_area"]
            else 0,
            "food_production_change_pct": round(
                (k2["food_production"] - k1["food_production"])
                / k1["food_production"]
                * 100,
                2,
            )
            if k1["food_production"]
            else 0,
            "economic_production_change_pct": round(
                (k2["economic_production"] - k1["economic_production"])
                / k1["economic_production"]
                * 100,
                2,
            )
            if k1["economic_production"]
            else 0,
        }

    return {
        "version": "2.0",
        "kpi": kpi,
        "yoy": yoy,
        "categories": categories_data,
        "production_by_crop": production_by_crop,
        "area_by_crop": area_by_crop,
        "province": province_data,
        "meta": {
            "years": [int(y) for y in sorted(year_results.keys())],
            "categoryColors": CATEGORY_COLORS,
            "cropColors": {k: CROP_COLORS[k] for k in sorted(CROP_COLORS)},
        },
    }


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def run() -> None:
    raw = read_csv(INPUT_PATH)
    raw["年份"] = pd.to_numeric(raw["年份"], errors="coerce").astype("Int64")
    available_years = sorted(int(year) for year in raw["年份"].dropna().unique())
    target_years = [year for year in (2023, 2024) if year in available_years]
    if not target_years:
        raise ValueError("CSV 中没有找到 2023 或 2024 年数据")

    all_results: dict[str, Any] = {}
    cleaned_data: dict[int, pd.DataFrame] = {}
    for year in target_years:
        raw_year = raw[raw["年份"].eq(year)].copy()
        cleaned, clean_stats = clean_data(raw_year)
        cleaned["作物类别"] = cleaned["品类"].map(classify_crop)
        CLEANED_DIR.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(CLEANED_DIR / f"cleaned_{year}.csv", index=False, encoding="utf-8-sig")

        summary = summarize(cleaned)
        generate_report(year, len(raw_year), clean_stats, summary, OUTPUT_DIR / f"report_{year}.html")
        all_results[str(year)] = {"cleaning": clean_stats, "summary": summary}
        cleaned_data[year] = cleaned
        print(f"{year} 年：原始 {len(raw_year)} 行，清洗后 {len(cleaned)} 行，报告已生成。")

    (OUTPUT_DIR / "analysis_summary.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ── 3D Dashboard 数据 ──
    dashboard = generate_dashboard_data(all_results, cleaned_data)
    (OUTPUT_DIR / "dashboard_data.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("完成：已生成年度清洗数据、HTML报告、analysis_summary.json 和 dashboard_data.json。")

    # ── 复制 dashboard_3d.html（若存在，则确保目录一致） ──
    dashboard_html = OUTPUT_DIR / "dashboard_3d.html"
    if not dashboard_html.exists():
        print("[警告] dashboard_3d.html 不存在，请手动生成。")
    else:
        print(f"[OK] dashboard_3d.html 已就绪 ({dashboard_html.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    run()