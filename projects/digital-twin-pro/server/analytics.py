# -*- coding: utf-8 -*-
"""分析型聚合查询：大屏 KPI / 排名 / 地图 / 结构 / 趋势。

口径说明：
- summary / structure：包含“全国”行（与旧大屏一致，总量口径）。
- ranking / geo：排除“全国”行，避免与各省汇总重复计算。
"""

from datetime import datetime

from sqlalchemy import func, select

from constants import CATEGORY_COLORS, CATEGORY_ORDER, PROVINCE_CODES
from models import (DimCrop, DimIndicator, DimRegion, DimYear, FactProduction)

# 汇总类作物（统计口径"小计/大类"行）：其数值≈若干具体作物之和，在省份×作物
# 明细中与具体作物重复计数，需排除。
# 判定依据（基于实际查库 dim_crop 确认）：crop_category 对汇总类与具体作物取值
# 完全相同（均为 粮食作物/经济作物/其他作物），无法仅凭 category 区分；
# 实际汇总行即下方清单（按 2023 fact 数据核对：粮食=谷物+豆类+薯类+…、
# 油料≈花生+油菜籽+芝麻+向日葵籽+胡麻籽、糖料=甘蔗+甜菜、麻类=黄红麻+…等）。
# 注：小麦/稻谷/烟叶 等与季节细分（冬小麦/中稻和一季晚稻/烤烟）数值近似，
# 但属统计年鉴常规作物条目，保留在明细中（见任务交付说明中的残余问题）。
AGGREGATE_CROP_NAMES = {
    # 粮食口径小计
    "粮食", "夏粮", "秋粮", "谷物", "豆类", "薯类",
    # 经济作物口径小计
    "油料", "糖料", "麻类", "蚕茧", "瓜果类",
}

# 简称 → 全称（含"自治区/特别行政区/直辖市"特殊后缀；其余省份默认 +"省"）
_PROVINCE_FULL_SPECIAL = {
    "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区", "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
    "香港": "香港特别行政区", "澳门": "澳门特别行政区",
}


def _province_full(short: str) -> str:
    """省份简称 → 全称（如 山东 → 山东省）。"""
    if short in _PROVINCE_FULL_SPECIAL:
        return _PROVINCE_FULL_SPECIAL[short]
    return short if short.endswith(("省", "市", "自治区")) else short + "省"


def _normalize_province(name: str) -> str:
    """省份全称 → 简称（如 山东省 → 山东），已简称则原样返回。"""
    name = (name or "").strip()
    for suffix in ("壮族自治区", "回族自治区", "维吾尔自治区", "特别行政区",
                   "自治区", "省", "市"):
        if name.endswith(suffix) and name[: -len(suffix)]:
            return name[: -len(suffix)]
    return name


def _find_region(db, name: str):
    """按 简称/全称 查找省份维度；不存在返回 None。先精确匹配，再按全称归一化匹配。"""
    q = select(DimRegion).where(DimRegion.province == name.strip())
    region = db.execute(q).scalars().first()
    if region is None:
        short = _normalize_province(name)
        if short != name.strip():
            region = db.execute(
                select(DimRegion).where(DimRegion.province == short)
            ).scalars().first()
    return region


def _fact_join():
    """事实表四表联查的基础查询。"""
    return (
        select(FactProduction)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
    )


def _sum_by(db, year, indicator: str, extra_filter=None) -> float:
    """按 年份+指标 求和（带可选分类过滤，注意必须 JOIN dim_crop）。"""
    q = (
        select(func.sum(FactProduction.value))
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
    )
    conds = [DimYear.year == year, DimIndicator.indicator_name == indicator]
    if extra_filter is not None:
        conds.append(extra_filter)
    return float(db.execute(q.where(*conds)).scalar() or 0.0)


def summary(db, year: int) -> dict:
    """大屏总览 KPI。"""
    prod_total = _sum_by(db, year, "产量")
    area_total = _sum_by(db, year, "面积")
    food = _sum_by(db, year, "产量", DimCrop.crop_category == "粮食作物")
    eco = _sum_by(db, year, "产量", DimCrop.crop_category == "经济作物")
    food_area = _sum_by(db, year, "面积", DimCrop.crop_category == "粮食作物")
    eco_area = _sum_by(db, year, "面积", DimCrop.crop_category == "经济作物")

    def pct(a, b):
        return round(a / b * 100, 2) if b else 0.0

    return {
        "year": year,
        "total_production": round(prod_total, 2),
        "total_area": round(area_total, 2),
        "food_production": round(food, 2),
        "food_area": round(food_area, 2),
        "food_production_pct": pct(food, prod_total),
        "food_area_pct": pct(food_area, area_total),
        "economic_production": round(eco, 2),
        "economic_area": round(eco_area, 2),
        "economic_production_pct": pct(eco, prod_total),
        "economic_area_pct": pct(eco_area, area_total),
    }


def yoy(db, current_year: int) -> dict:
    """同比变化（当前年 vs 上一年，仅当两年数据都存在时计算）。"""
    years = sorted(db.execute(select(DimYear.year)).scalars().all())
    if current_year not in years:
        return {}
    prev = max((y for y in years if y < current_year), default=None)
    if prev is None:
        return {}
    cur = summary(db, current_year)
    pre = summary(db, prev)

    def chg(a, b):
        return round((a - b) / b * 100, 2) if b else None

    return {
        "base_year": prev,
        "production_change_pct": chg(cur["total_production"], pre["total_production"]),
        "area_change_pct": chg(cur["total_area"], pre["total_area"]),
        "food_production_change_pct": chg(cur["food_production"], pre["food_production"]),
        "economic_production_change_pct": chg(cur["economic_production"],
                                              pre["economic_production"]),
    }


def ranking(db, year: int, by: str = "crop", limit: int = 20) -> list[dict]:
    """排名：by=crop 按作物汇总，by=region 按省份汇总（均排除全国）。

    一次 GROUP BY 完成产量/面积拆分，避免 N+1 查询。
    """
    if by == "region":
        group_col = DimRegion.province.label("name")
        extra_col = None
        rows = []
        q = (
            select(DimRegion.province, DimIndicator.indicator_name,
                   func.sum(FactProduction.value))
            .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
            .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
            .join(DimYear, FactProduction.year_id == DimYear.year_id)
            .where(DimYear.year == year, DimRegion.province != "全国")
            .group_by(DimRegion.province, DimIndicator.indicator_name)
        )
        agg = {}
        for prov, ind, val in db.execute(q).all():
            agg.setdefault(prov, {"name": prov, "production": 0.0, "area": 0.0})
            agg[prov][("production" if ind == "产量" else "area")] += float(val or 0.0)
        rows = [{"name": k, "production": round(v["production"], 2),
                 "area": round(v["area"], 2)} for k, v in agg.items()]
    else:
        q = (
            select(DimCrop.crop_name, DimCrop.crop_category,
                   DimIndicator.indicator_name, func.sum(FactProduction.value))
            .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
            .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
            .join(DimYear, FactProduction.year_id == DimYear.year_id)
            .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
            .where(DimYear.year == year, DimRegion.province != "全国")
            .group_by(DimCrop.crop_name, DimCrop.crop_category,
                      DimIndicator.indicator_name)
        )
        agg = {}
        for crop, cat, ind, val in db.execute(q).all():
            agg.setdefault(crop, {"name": crop, "category": cat,
                                  "production": 0.0, "area": 0.0})
            agg[crop][("production" if ind == "产量" else "area")] += float(val or 0.0)
        rows = [{"name": k, "category": v["category"],
                 "production": round(v["production"], 2),
                 "area": round(v["area"], 2)} for k, v in agg.items()]

    rows.sort(key=lambda x: x["production"], reverse=True)
    return rows[:limit]


def geo(db, year: int) -> list[dict]:
    """省级地图数据（排除全国，带行政区划编码）。"""
    q = (
        select(DimRegion.province, DimIndicator.indicator_name,
               func.sum(FactProduction.value))
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .where(DimYear.year == year, DimRegion.province != "全国")
        .group_by(DimRegion.province, DimIndicator.indicator_name)
    )
    agg = {}
    for prov, ind, val in db.execute(q).all():
        agg.setdefault(prov, {"name": prov, "production": 0.0, "area": 0.0})
        agg[prov][("production" if ind == "产量" else "area")] += float(val or 0.0)
    rows = []
    for prov, d in agg.items():
        if d["production"] <= 0 and d["area"] <= 0:
            continue
        rows.append({
            "name": prov,
            "code": PROVINCE_CODES.get(prov, ""),
            "production": round(d["production"], 2),
            "area": round(d["area"], 2),
        })
    rows.sort(key=lambda x: x["production"], reverse=True)
    return rows


def structure(db, year: int) -> list[dict]:
    """作物结构：按分类统计产量/面积占比。"""
    prod_total = _sum_by(db, year, "产量")
    area_total = _sum_by(db, year, "面积")

    def pct(a, b):
        return round(a / b * 100, 2) if b else 0.0

    result = []
    for cat in CATEGORY_ORDER:
        p = _sum_by(db, year, "产量", DimCrop.crop_category == cat)
        a = _sum_by(db, year, "面积", DimCrop.crop_category == cat)
        result.append({
            "name": cat,
            "production": round(p, 2),
            "area": round(a, 2),
            "production_pct": pct(p, prod_total),
            "area_pct": pct(a, area_total),
            "color": CATEGORY_COLORS.get(cat, "#6b7c93"),
        })
    return result


def trend(db, crop=None, region=None, start=None, end=None,
          indicator: str = "产量") -> list[dict]:
    """时间趋势：按年份聚合产量/面积。"""
    q = (
        select(DimYear.year, func.sum(FactProduction.value))
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .where(DimIndicator.indicator_name == indicator)
        .group_by(DimYear.year)
        .order_by(DimYear.year)
    )
    if crop:
        q = q.where(DimCrop.crop_name == crop)
    if region:
        q = q.where(DimRegion.province == region)
    if start:
        q = q.where(DimYear.year >= int(start))
    if end:
        q = q.where(DimYear.year <= int(end))
    return [{"year": y, "value": round(float(v or 0.0), 2)} for y, v in db.execute(q).all()]


def production_by_crop(db, year: int) -> list[dict]:
    """按作物列出产量/面积明细（大屏 ranking 列表结构，扁平数组）。

    每项同时提供 value（=production，兼容旧大屏 dashboard_3d）与
    production/area（兼容新大屏 digital_twin_pro）。
    """
    q = (
        select(DimCrop.crop_name, DimCrop.crop_category,
               DimIndicator.indicator_name, func.sum(FactProduction.value))
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .where(DimYear.year == year, DimRegion.province != "全国")
        .group_by(DimCrop.crop_name, DimCrop.crop_category,
                  DimIndicator.indicator_name)
    )
    agg = {}
    for crop, cat, ind, val in db.execute(q).all():
        agg.setdefault(crop, {"name": crop, "category": cat,
                              "production": 0.0, "area": 0.0})
        agg[crop][("production" if ind == "产量" else "area")] += float(val or 0.0)

    rows = []
    for crop, d in agg.items():
        color = CATEGORY_COLORS.get(d["category"], "#6b7c93")
        rows.append({
            "crop": crop,
            "name": crop,  # 兼容 digital_twin_pro.html 排名渲染（item.name）
            "category": d["category"],
            "production": round(d["production"], 2),
            "area": round(d["area"], 2),
            "value": round(d["production"], 2),
            "color": color,
        })
    rows.sort(key=lambda x: x["production"], reverse=True)
    return rows


def _province_top_crops(db, year: int) -> dict:
    """{省份: 主产作物 crop_name}，一次 GROUP BY 完成。

    供 /api/dashboard 的 province 数组 top_crop 与 mapData mainCrop 字段
    （大屏柱状图图标/tooltip 映射）。
    优先取"具体作物"中产量最高者（排除汇总类，避免 粮食/谷物 等小计行误判）；
    若该省该年只有汇总行（如 2024 黑龙江仅"粮食"一行，明细数据缺失），
    退回产量最高的汇总作物名（如"粮食"），保证 tooltip 不出现空值。
    """
    q = (
        select(DimRegion.province, DimCrop.crop_name,
               func.sum(FactProduction.value))
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .where(DimYear.year == year, DimRegion.province != "全国",
               DimIndicator.indicator_name == "产量")
        .group_by(DimRegion.province, DimCrop.crop_name)
    )
    # prov -> (value, crop, 是否具体作物)
    best: dict[str, tuple[float, str, bool]] = {}
    for prov, crop, val in db.execute(q).all():
        v = float(val or 0.0)
        is_specific = crop not in AGGREGATE_CROP_NAMES
        cur = best.get(prov)
        if cur is None:
            best[prov] = (v, crop, is_specific)
        else:
            cv, ccrop, cspec = cur
            # 具体作物优先于汇总行；同级别取产量高者
            if (is_specific and not cspec) or (is_specific == cspec and v > cv):
                best[prov] = (v, crop, is_specific)
    return {p: c for p, (v, c, _s) in best.items()}


# 分类简称映射：数据库 dim_crop 存"粮食作物/经济作物/其他作物"，
# 省份×作物明细契约要求 category 为 粮食/经济作物/其他（大屏按短名匹配）。
_CATEGORY_SHORT = {
    "粮食作物": "粮食",
    "经济作物": "经济作物",
    "其他作物": "其他",
}


def province_crop_detail(db, name: str, year: int):
    """省份×作物明细（/api/analytics/province/{name}，供大屏 3D 柱状图详情面板）。

    契约字段：province/year/total_production/total_area/main_crop/crop_count/crops[]，
    crops 项为 name/category/production/area/production_pct/unit_production，
    按 production 降序。分类输出短名（粮食/经济作物/其他）。

    口径：
    - 排除汇总类作物（AGGREGATE_CROP_NAMES：粮食/谷物/豆类/薯类/油料等小计行），
      避免与具体作物重复计数；total_* 为"排除汇总后明细作物"合计，与
      /api/dashboard province 全量口径数值不同（原因见 AGGREGATE_CROP_NAMES 注释）。
    - 一次 GROUP BY 查询完成全部 fact 聚合，避免 N+1。
    - 省份不存在返回 None（路由层转 404）；省份存在但该年无数据返回
      200 + crops 空数组 + main_crop=null（前端可直接渲染空态，无需错误处理）。
    - "全国"级省份在路由层拦截返回 400（本函数不处理）。
    """
    region = _find_region(db, name)
    if region is None:
        return None
    short = region.province

    q = (
        select(DimCrop.crop_name, DimCrop.crop_category,
               DimIndicator.indicator_name, func.sum(FactProduction.value))
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .where(DimYear.year == year, DimRegion.province == short,
               DimCrop.crop_name.notin_(AGGREGATE_CROP_NAMES))
        .group_by(DimCrop.crop_name, DimCrop.crop_category,
                  DimIndicator.indicator_name)
    )
    agg = {}
    for crop, cat, ind, val in db.execute(q).all():
        agg.setdefault(crop, {"category": cat, "production": 0.0, "area": 0.0})
        agg[crop][("production" if ind == "产量" else "area")] += float(val or 0.0)

    crops = []
    for crop, d in agg.items():
        if d["production"] <= 0 and d["area"] <= 0:
            continue
        crops.append({
            "name": crop,
            "category": _CATEGORY_SHORT.get(d["category"], d["category"]),
            "production": round(d["production"], 1),
            "area": round(d["area"], 1),
        })
    crops.sort(key=lambda x: x["production"], reverse=True)

    total_production = round(sum(c["production"] for c in crops), 1)
    total_area = round(sum(c["area"] for c in crops), 1)
    for c in crops:
        c["production_pct"] = (
            round(c["production"] / total_production * 100, 1)
            if total_production else 0.0
        )
        c["unit_production"] = (
            round(c["production"] / c["area"], 2) if c["area"] else 0.0
        )

    return {
        "province": short,
        "year": year,
        "total_production": total_production,
        "total_area": total_area,
        "main_crop": crops[0]["name"] if crops else None,
        "crop_count": len(crops),
        "crops": crops,
    }


def dashboard_payload(db) -> dict:
    """大屏聚合端点：返回与 dashboard_data.json 完全兼容的多年度数据包。

    结构对齐 digital_twin_pro.html 的读取方式：
    kpi[year] / categories[year] / production_by_crop[year] / area_by_crop[year] /
    province[]（含 year 字段）/ yoy。
    """
    years = sorted(db.execute(select(DimYear.year)).scalars().all())
    kpi, categories, prod_by_crop, area_by_crop, provinces = {}, {}, {}, {}, []
    for year in years:
        kpi[str(year)] = summary(db, year)
        categories[str(year)] = structure(db, year)
        prod = production_by_crop(db, year)
        prod_by_crop[str(year)] = prod
        area = sorted([dict(r, value=r["area"]) for r in prod],
                      key=lambda x: x["area"], reverse=True)
        area_by_crop[str(year)] = area
        top_crops = _province_top_crops(db, year)
        for g in geo(db, year):
            provinces.append({
                "year": year,
                "province": g["name"],
                "provinceFull": g["name"],
                "production": g["production"],
                "area": g["area"],
                "top_crop": top_crops.get(g["name"]),
            })
    # last 取"实际有省级数据"的最后一年，而非 dim_year 最大年份：
    # 当前库中 2025 为无数据空年，直接用 years[-1] 会使 mapData/rankings 为空、
    # yoy 出现 -100% 假同比（既有缺陷，本次一并修复）。
    # provinces 由上方 geo() 非空年份构建，天然只含真实数据年。
    last = max((p["year"] for p in provinces), default=None)
    # mapData 主产作物注入（任务2）：仅追加 mainCrop 字段，不动既有字段（向后兼容）。
    # 方案理由：大屏 bar3D 柱子 tooltip 只需当前年各省主产作物，直接在 dashboard
    # 现有 mapData 每项加 mainCrop，一次请求拿到全部信息，无需新增端点/第二次请求；
    # 且与 province[].top_crop（历史年数组）互补：mapData 只有最后一年，正是地图所需。
    # 注意 geo() 每次调用新建 dict，就地追加字段安全。
    map_data = []
    if last:
        top_crops_last = _province_top_crops(db, last)
        for g in geo(db, last):
            g["mainCrop"] = top_crops_last.get(g["name"])
            map_data.append(g)
    return {
        "version": "2.0",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "years": years,
        "kpi": kpi,
        "yoy": yoy(db, last) if last else {},
        "categories": categories,
        "production_by_crop": prod_by_crop,
        "area_by_crop": area_by_crop,
        "province": provinces,
        "rankings": {
            "by_crop": ranking(db, last, by="crop") if last else [],
            "by_region": ranking(db, last, by="region") if last else [],
        },
        "mapData": map_data,
        "trend": {"production": trend(db, indicator="产量"),
                  "area": trend(db, indicator="面积")},
    }