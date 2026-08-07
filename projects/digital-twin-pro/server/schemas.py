# -*- coding: utf-8 -*-
"""Pydantic 模型（请求/响应 Schema，Pydantic v2）。"""

import math
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 数据质量约束（与前端保持一致，双保险）
YEAR_MIN, YEAR_MAX = 1990, 2099


class RecordBase(BaseModel):
    """新增/编辑记录时的公共字段（均为业务字段，维度按名称传值）。"""

    year: int = Field(..., ge=YEAR_MIN, le=YEAR_MAX, description="年份（1990-2099）")
    province: str = Field(..., min_length=1, description="省份")
    crop: str = Field(..., min_length=1, description="作物/品类")
    crop_category: str = Field("其他作物", description="作物分类")
    indicator: str = Field(..., description="指标名：产量/面积")
    unit: str = Field("", description="数值单位（可选，用于换算）")
    value: float = Field(..., ge=0, description="数值（非负，且必须是有限数）")
    source: str = Field("", description="数据来源")
    data_quality: str = Field("normal", description="数据质量标记")

    @field_validator("value")
    @classmethod
    def _value_must_be_finite(cls, v: float) -> float:
        """拒绝 NaN / Infinity（Pydantic 对 inf 也会解析成功，需显式拦截）。"""
        if v is None or not math.isfinite(v):
            raise ValueError("value 必须是有限数值（不允许 NaN/Infinity）")
        return v


class RecordCreate(RecordBase):
    """新增记录请求。"""


class RecordUpdate(RecordBase):
    """更新记录请求。"""


class RecordOut(BaseModel):
    """记录响应：附带维度表名称，便于管理页直接展示。"""

    model_config = ConfigDict(from_attributes=True)

    fact_id: int
    year: int
    province: str
    city: str = ""
    county: str = ""
    crop: str
    crop_category: str = ""
    indicator: str
    unit: str = ""
    value: float
    source: str = ""
    data_quality: str = ""
    updated_at: Optional[str] = None


class RecordPage(BaseModel):
    """记录分页响应。"""

    total: int
    page: int
    page_size: int
    items: list[RecordOut]


class ImportReport(BaseModel):
    """CSV 导入报告。"""

    filename: str
    total_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    failed_rows: int = 0
    warning_rows: int = 0
    skipped_rows: int = 0
    failed_details: list[str] = []
    warning_details: list[str] = []
    message: str = ""


class DimensionsMeta(BaseModel):
    """元数据：管理页下拉框数据源。"""

    years: list[int]
    regions: list[dict]
    crops: list[dict]
    indicators: list[dict]
    counts: dict = {}


class HealthOut(BaseModel):
    """健康检查响应。"""

    status: str
    db: str
    tables: dict
    version: str = "1.0.0"