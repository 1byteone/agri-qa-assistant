# -*- coding: utf-8 -*-
"""CSV 导入 / 导出 / 事实记录查询逻辑。

导入流程：解析 CSV（兼容原始 万吨/千公顷 与清洗后 吨/亩 两种格式）
→ 单位归一化 → 维度表 get-or-create → 事实表幂等 upsert（UNIQUE 四维键）。
"""

import csv
import io
import math
from datetime import datetime

from sqlalchemy import select

from constants import (AREA_LIMIT_MU, NATIONAL_AREA_LIMIT_MU,
                       NATIONAL_PRODUCTION_LIMIT_TONS, PRODUCTION_LIMIT_TONS,
                       is_national_level, normalize_indicator, normalize_unit)
from models import (DimCrop, DimIndicator, DimRegion, DimYear, FactProduction,
                    RawImport)

# 表头别名：同一业务列允许多种写法
HEADER_ALIASES = {
    "year": ["年份", "年", "year"],
    "province": ["省份", "省", "地区", "区域", "省市", "province", "region"],
    "crop": ["品类", "作物", "作物名称", "农作物", "crop"],
    "indicator": ["指标", "indicator"],
    "value": ["数值", "值", "value"],
    "unit": ["单位", "unit"],
    "category": ["作物类别", "类别", "分类", "category"],
    "source": ["来源", "数据来源", "source"],
}

# 标准指标名列表（用于校验）
VALID_INDICATORS = {"产量", "面积", "单产"}


def _map_header(row: dict) -> dict:
    """把任意表头映射到标准字段名，未识别的列忽略。"""
    norm = {}
    for key, value in row.items():
        k = (key or "").strip()
        for std, aliases in HEADER_ALIASES.items():
            if k in aliases:
                norm[std] = (value or "").strip()
                break
    return norm


def get_or_create_year(db, year: int) -> DimYear:
    """按年份获取维度，不存在则创建。"""
    obj = db.execute(select(DimYear).where(DimYear.year == year)).scalar_one_or_none()
    if obj is None:
        obj = DimYear(year=year)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_region(db, province: str, city: str = "", county: str = "") -> DimRegion:
    """按 (省,市,县) 获取维度，不存在则创建。"""
    province = (province or "").strip()
    city = (city or "").strip()
    county = (county or "").strip()
    obj = db.execute(
        select(DimRegion).where(
            DimRegion.province == province,
            DimRegion.city == city,
            DimRegion.county == county,
        )
    ).scalar_one_or_none()
    if obj is None:
        obj = DimRegion(province=province, city=city, county=county)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_crop(db, crop_name: str, category: str = "其他作物") -> DimCrop:
    """按作物名获取维度，不存在则创建。"""
    crop_name = (crop_name or "").strip()
    obj = db.execute(select(DimCrop).where(DimCrop.crop_name == crop_name)).scalar_one_or_none()
    if obj is None:
        obj = DimCrop(crop_name=crop_name, crop_category=category or "其他作物")
        db.add(obj)
        db.flush()
    else:
        # 若已有记录分类为空，则补全
        if not obj.crop_category and category:
            obj.crop_category = category
            db.flush()
    return obj


def get_or_create_indicator(db, indicator_name: str, unit: str = "") -> DimIndicator:
    """按指标名获取维度，不存在则创建。"""
    obj = db.execute(
        select(DimIndicator).where(DimIndicator.indicator_name == indicator_name)
    ).scalar_one_or_none()
    if obj is None:
        obj = DimIndicator(indicator_name=indicator_name, unit=unit)
        db.add(obj)
        db.flush()
    else:
        if not obj.unit and unit:
            obj.unit = unit
            db.flush()
    return obj


def parse_csv_bytes(data: bytes) -> list[dict]:
    """解析上传/本地 CSV 字节内容为标准化行字典列表。"""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = [_map_header(r) for r in reader]
    return [r for r in rows if r.get("value") is not None or r.get("province")]


def _upsert_fact(db, year_obj, region_obj, crop_obj, ind_obj, value, source, quality) -> bool:
    """幂等写入事实表：返回 True=新增，False=更新（先查后写，计数精确）。"""
    fact = db.execute(
        select(FactProduction).where(
            FactProduction.year_id == year_obj.year_id,
            FactProduction.region_id == region_obj.region_id,
            FactProduction.crop_id == crop_obj.crop_id,
            FactProduction.indicator_id == ind_obj.indicator_id,
        )
    ).scalar_one_or_none()
    if fact is None:
        db.add(FactProduction(
            year_id=year_obj.year_id,
            region_id=region_obj.region_id,
            crop_id=crop_obj.crop_id,
            indicator_id=ind_obj.indicator_id,
            value=value,
            source=source or "",
            data_quality=quality or "normal",
            updated_at=datetime.utcnow(),
        ))
        db.flush()
        return True
    # 已存在：更新数值/来源/质量（幂等防重，保持四维唯一键）
    fact.value = value
    fact.source = source or ""
    fact.data_quality = quality or "normal"
    fact.updated_at = datetime.utcnow()
    db.flush()
    return False


def import_rows(db, rows: list[dict], filename: str = "", source: str = "") -> dict:
    """批量导入规范化行，返回统计报告 dict。"""
    report = {
        "filename": filename,
        "total_rows": len(rows),
        "inserted_rows": 0,
        "updated_rows": 0,
        "failed_rows": 0,
        "warning_rows": 0,
        "skipped_rows": 0,
        "failed_details": [],
        "warning_details": [],
    }
    for idx, row in enumerate(rows, start=2):  # 从第2行（含表头）计行号
        line_no = idx
        try:
            year = int(row.get("year"))
            province = row.get("province") or ""
            crop_name = row.get("crop") or ""
            indicator_raw = row.get("indicator") or ""
            value_raw = row.get("value") or ""
            unit_raw = row.get("unit") or ""
            category = row.get("category") or "其他作物"

            if not province or not crop_name or not indicator_raw:
                report["failed_rows"] += 1
                report["failed_details"].append(f"第{line_no}行：省份/作物/指标不能为空")
                continue

            # 单位归一化：万吨→吨，千公顷→亩
            indicator_name, unit, factor = normalize_unit(unit_raw)
            indicator_name = normalize_indicator(indicator_raw) or indicator_name
            if indicator_name not in VALID_INDICATORS:
                # 指标名无法归一时按原始名入库（不拦截）
                pass
            try:
                value = float(value_raw) * factor
            except (TypeError, ValueError):
                report["failed_rows"] += 1
                report["failed_details"].append(f"第{line_no}行：数值不是合法数字 ({value_raw})")
                continue

            # 数据质量行级校验：负值 / 非有限数 → 计入 failed 并返回行号；
            # 数值超出量级阈值（省级 50000吨/500000亩，全国级 1e10吨/1e8亩）
            # → 不阻断导入，降级为 warning（仍入库，data_quality 标记为 warning）
            if not math.isfinite(value) or value < 0:
                report["failed_rows"] += 1
                report["failed_details"].append(
                    f"第{line_no}行：数值必须为正有限数（实际 {value_raw}）")
                continue

            quality = "normal"
            if is_national_level(province):
                prod_limit = NATIONAL_PRODUCTION_LIMIT_TONS
                area_limit = NATIONAL_AREA_LIMIT_MU
            else:
                prod_limit = PRODUCTION_LIMIT_TONS
                area_limit = AREA_LIMIT_MU

            warning = None
            if indicator_name == "产量" and value >= prod_limit:
                warning = (f"第{line_no}行：产量超出常见量级"
                           f"（≥{prod_limit:g} 吨，实际 {value:g} 吨），"
                           f"已入库并标记 data_quality=warning，请确认")
            elif indicator_name == "面积" and value >= area_limit:
                warning = (f"第{line_no}行：面积超出常见量级"
                           f"（≥{area_limit:g} 亩，实际 {value:g} 亩），"
                           f"已入库并标记 data_quality=warning，请确认")
            if warning:
                report["warning_rows"] += 1
                report["warning_details"].append(warning)
                quality = "warning"

            year_obj = get_or_create_year(db, year)
            region_obj = get_or_create_region(db, province)
            crop_obj = get_or_create_crop(db, crop_name, category)
            ind_obj = get_or_create_indicator(db, indicator_name, unit)

            is_new = _upsert_fact(db, year_obj, region_obj, crop_obj, ind_obj,
                                  value, source or filename, quality)
            if is_new:
                report["inserted_rows"] += 1
            else:
                report["updated_rows"] += 1
        except Exception as exc:  # noqa: BLE001 单行错误不影响整体导入
            report["failed_rows"] += 1
            report["failed_details"].append(f"第{line_no}行：{exc}")

    report["skipped_rows"] = report["total_rows"] - report["inserted_rows"] \
        - report["updated_rows"] - report["failed_rows"]
    if len(report["failed_details"]) > 20:  # 只保留前20条错误明细
        report["failed_details"] = report["failed_details"][:20]
    if len(report["warning_details"]) > 20:  # 只保留前20条警告明细
        report["warning_details"] = report["warning_details"][:20]
    return report


def import_csv(db, filename: str, data: bytes, source: str = "") -> dict:
    """CSV 导入入口：解析 → 入库 → 记录 raw_imports 元信息。"""
    rows = parse_csv_bytes(data)
    report = import_rows(db, rows, filename=filename, source=source)
    warn_txt = f"，警告 {report['warning_rows']} 行" if report["warning_rows"] else ""
    report["message"] = (
        f"共 {report['total_rows']} 行：新增 {report['inserted_rows']} 行，"
        f"更新 {report['updated_rows']} 行，失败 {report['failed_rows']} 行"
        f"{warn_txt}"
    )
    # 记录导入元信息
    db.add(RawImport(
        filename=filename,
        total_rows=report["total_rows"],
        inserted_rows=report["inserted_rows"],
        updated_rows=report["updated_rows"],
        failed_rows=report["failed_rows"],
        skipped_rows=report["skipped_rows"],
        message=report["message"],
    ))
    db.commit()
    return report


# ---------------------------------------------------------------
# 记录查询（/api/records 与 /api/export/csv 共用）
# ---------------------------------------------------------------
def build_record_query(year=None, region=None, crop=None, indicator=None,
                       keyword=None):
    """构造事实表查询，返回 (query, filters)。"""
    filters = []
    if year:
        filters.append(DimYear.year == int(year))
    if region:
        filters.append(DimRegion.province == region)
    if crop:
        filters.append(DimCrop.crop_name == crop)
    if indicator:
        filters.append(DimIndicator.indicator_name == indicator)
    if keyword:
        like = f"%{keyword}%"
        filters.append(
            (DimRegion.province.like(like)) | (DimCrop.crop_name.like(like))
        )
    query = (
        select(FactProduction)
        .join(DimYear, FactProduction.year_id == DimYear.year_id)
        .join(DimRegion, FactProduction.region_id == DimRegion.region_id)
        .join(DimCrop, FactProduction.crop_id == DimCrop.crop_id)
        .join(DimIndicator, FactProduction.indicator_id == DimIndicator.indicator_id)
    )
    return query, filters


def fact_to_dict(fact: FactProduction) -> dict:
    """事实行 → 字典（附带维度名称）。"""
    return {
        "fact_id": fact.fact_id,
        "year": fact.year_dim.year,
        "province": fact.region_dim.province,
        "city": fact.region_dim.city,
        "county": fact.region_dim.county,
        "crop": fact.crop_dim.crop_name,
        "crop_category": fact.crop_dim.crop_category,
        "indicator": fact.indicator_dim.indicator_name,
        "unit": fact.indicator_dim.unit,
        "value": fact.value,
        "source": fact.source or "",
        "data_quality": fact.data_quality or "",
        "updated_at": fact.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if fact.updated_at else "",
    }


def export_csv_text(db, year=None, region=None, crop=None, indicator=None,
                    keyword=None) -> str:
    """按筛选条件导出 CSV 文本（表头与导入格式兼容）。"""
    query, filters = build_record_query(year, region, crop, indicator, keyword)
    facts = db.execute(query.where(*filters).order_by(
        DimYear.year, DimRegion.province, DimCrop.crop_name)).scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["年份", "省份", "品类", "指标", "数值", "单位", "作物类别", "数据来源"])
    for fact in facts:
        writer.writerow([
            fact.year_dim.year,
            fact.region_dim.province,
            fact.crop_dim.crop_name,
            fact.indicator_dim.indicator_name,
            fact.value,
            fact.indicator_dim.unit,
            fact.crop_dim.crop_category,
            fact.source or "",
        ])
    return buf.getvalue()