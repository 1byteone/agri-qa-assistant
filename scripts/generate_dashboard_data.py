#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 3D 仪表盘生成前端消费的完整 JSON 数据包。"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CLEANED_DIR = BASE_DIR / "data"

# 省份名称映射（ECharts 地图使用标准短名称）
PROVINCE_MAP = {
    "北京": "北京", "天津": "天津", "河北": "河北", "山西": "山西",
    "内蒙古": "内蒙古", "辽宁": "辽宁", "吉林": "吉林", "黑龙江": "黑龙江",
    "上海": "上海", "江苏": "江苏", "浙江": "浙江", "安徽": "安徽",
    "福建": "福建", "江西": "江西", "山东": "山东", "河南": "河南",
    "湖北": "湖北", "湖南": "湖南", "广东": "广东", "广西": "广西",
    "海南": "海南", "重庆": "重庆", "四川": "四川", "贵州": "贵州",
    "云南": "云南", "西藏": "西藏", "陕西": "陕西", "甘肃": "甘肃",
    "青海": "青海", "宁夏": "宁夏", "新疆": "新疆",
}

CATEGORY_COLORS = {
    "粮食作物": "#f59e0b",
    "经济作物": "#10b981",
    "其他作物": "#8b5cf6",
}

CATEGORY_ORDER = ["粮食作物", "经济作物", "其他作物"]


def load_cleaned(year: int) -> pd.DataFrame:
    path = CLEANED_DIR / f"cleaned_{year}.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["数值"] = pd.to_numeric(df["数值"], errors="coerce")
    return df


def build_province_data(df: pd.DataFrame) -> list[dict]:
    """每个省份的总产量和总面积"""
    rows = []
    for prov in df["省份"].unique():
        if prov == "全国":
            continue
        pdata = df[df["省份"] == prov]
        prod = float(pdata[pdata["指标"] == "产量"]["数值"].sum())
        area = float(pdata[pdata["指标"] == "种植面积"]["数值"].sum())
        echor = PROVINCE_MAP.get(prov, prov)
        if prod > 0 or area > 0:
            rows.append({"name": echor, "production": round(prod, 2), "area": round(area, 2)})
    return rows


def build_crop_data(df: pd.DataFrame) -> dict:
    """按作物类别分组，每组内列出品类详细数据"""
    result = {}
    for cat in CATEGORY_ORDER:
        cat_df = df[df["作物类别"] == cat]
        prod = cat_df[cat_df["指标"] == "产量"]
        area = cat_df[cat_df["指标"] == "种植面积"]
        crops = []
        for _, row in prod.drop_duplicates(subset=["品类"]).iterrows():
            crop_name = row["品类"]
            pval = float(prod[prod["品类"] == crop_name]["数值"].sum())
            aval = float(area[area["品类"] == crop_name]["数值"].sum()) if not area[area["品类"] == crop_name].empty else 0
            crops.append({"name": crop_name, "production": round(pval, 2), "area": round(aval, 2)})
        crops.sort(key=lambda x: x["production"], reverse=True)
        result[cat] = {
            "color": CATEGORY_COLORS[cat],
            "crops": crops,
            "total_production": round(sum(c["production"] for c in crops), 2),
            "total_area": round(sum(c["area"] for c in crops), 2),
        }
    return result


def build_kpi(df: pd.DataFrame) -> dict:
    prod_total = float(df[df["指标"] == "产量"]["数值"].sum())
    area_total = float(df[df["指标"] == "种植面积"]["数值"].sum())
    grain = df[df["作物类别"] == "粮食作物"]
    grain_prod = float(grain[grain["指标"] == "产量"]["数值"].sum())
    eco = df[df["作物类别"] == "经济作物"]
    eco_prod = float(eco[eco["指标"] == "产量"]["数值"].sum())
    return {
        "total_production": round(prod_total, 2),
        "total_area": round(area_total, 2),
        "grain_production": round(grain_prod, 2),
        "grain_ratio": round(grain_prod / prod_total * 100, 2) if prod_total else 0,
        "economic_production": round(eco_prod, 2),
        "economic_ratio": round(eco_prod / prod_total * 100, 2) if prod_total else 0,
    }


def run():
    dashboard = {"years": {}}
    for year in (2023, 2024):
        df = load_cleaned(year)
        dashboard["years"][str(year)] = {
            "kpi": build_kpi(df),
            "provinces": build_province_data(df),
            "categories": build_crop_data(df),
            "total_records": len(df),
        }

    out_path = BASE_DIR / "data" / "dashboard_data.json"
    out_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dashboard data written to {out_path}")


if __name__ == "__main__":
    run()