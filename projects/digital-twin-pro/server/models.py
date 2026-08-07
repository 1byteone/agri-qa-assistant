# -*- coding: utf-8 -*-
"""星型模型：维度表 + 长表事实表（SQLAlchemy 2.0 风格）。"""

from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class DimYear(Base):
    """年份维度表。"""

    __tablename__ = "dim_year"

    year_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    year = Column(Integer, unique=True, nullable=False, comment="年份，如 2023")

    facts = relationship("FactProduction", back_populates="year_dim")


class DimRegion(Base):
    """地区维度表（省/市/县三级，本数据仅用到省级）。"""

    __tablename__ = "dim_region"
    __table_args__ = (UniqueConstraint("province", "city", "county",
                                       name="uq_region_pcc"),)

    region_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    province = Column(String(64), nullable=False, default="", comment="省份")
    city = Column(String(64), nullable=False, default="", comment="地市")
    county = Column(String(64), nullable=False, default="", comment="区县")
    region_code = Column(String(16), default="", comment="行政区划编码")

    facts = relationship("FactProduction", back_populates="region_dim")


class DimCrop(Base):
    """作物维度表。"""

    __tablename__ = "dim_crop"

    crop_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    crop_name = Column(String(128), unique=True, nullable=False, comment="作物/品类名称")
    crop_category = Column(String(32), default="其他作物", comment="分类：粮食作物/经济作物/其他作物")

    facts = relationship("FactProduction", back_populates="crop_dim")


class DimIndicator(Base):
    """指标维度表（产量/面积/单产），含单位。"""

    __tablename__ = "dim_indicator"

    indicator_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    indicator_name = Column(String(64), unique=True, nullable=False, comment="指标名：产量/面积/单产")
    unit = Column(String(16), default="", comment="标准单位：吨/亩")

    facts = relationship("FactProduction", back_populates="indicator_dim")


class FactProduction(Base):
    """事实表：单条 年份×地区×作物×指标 记录。"""

    __tablename__ = "fact_production"
    __table_args__ = (
        UniqueConstraint("year_id", "region_id", "crop_id", "indicator_id",
                         name="uq_fact_4d"),  # 幂等防重
    )

    fact_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    year_id = Column(Integer, ForeignKey("dim_year.year_id"), nullable=False, comment="年份外键")
    region_id = Column(Integer, ForeignKey("dim_region.region_id"), nullable=False, comment="地区外键")
    crop_id = Column(Integer, ForeignKey("dim_crop.crop_id"), nullable=False, comment="作物外键")
    indicator_id = Column(Integer, ForeignKey("dim_indicator.indicator_id"),
                          nullable=False, comment="指标外键")
    value = Column(Float, nullable=False, comment="数值（标准单位：吨/亩）")
    source = Column(String(128), default="", comment="数据来源")
    data_quality = Column(String(32), default="normal", comment="数据质量标记")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                        comment="更新时间")

    year_dim = relationship("DimYear", back_populates="facts")
    region_dim = relationship("DimRegion", back_populates="facts")
    crop_dim = relationship("DimCrop", back_populates="facts")
    indicator_dim = relationship("DimIndicator", back_populates="facts")


class RawImport(Base):
    """CSV 导入元信息表：记录每次导入的文件名/时间/行数/校验结果。"""

    __tablename__ = "raw_imports"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    filename = Column(String(256), default="", comment="导入文件名")
    import_time = Column(DateTime, default=datetime.utcnow, comment="导入时间")
    total_rows = Column(Integer, default=0, comment="CSV 总行数")
    inserted_rows = Column(Integer, default=0, comment="新增行数")
    updated_rows = Column(Integer, default=0, comment="更新行数")
    failed_rows = Column(Integer, default=0, comment="失败行数")
    skipped_rows = Column(Integer, default=0, comment="跳过行数")
    message = Column(Text, default="", comment="校验/导入结果描述")


# ===============================================================
# v2 新增：IoT 设备 / 传感器读数 / 告警 / 地块
# ===============================================================

class Device(Base):
    """IoT 设备（土壤传感器/气象站/灌溉控制器/摄像头）。"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(64), unique=True, nullable=False, comment="设备编号")
    name = Column(String(128), nullable=False, comment="设备名称")
    type = Column(String(32), nullable=False, comment="类型：soil/weather/irrigation/camera")
    province = Column(String(64), default="", comment="所在省份")
    status = Column(String(16), default="online", comment="状态：online/offline/fault")
    online_rate = Column(Float, default=100.0, comment="在线率（%）")
    last_seen = Column(DateTime, default=datetime.utcnow, comment="最后数据时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class SensorReading(Base):
    """传感器读数（每 3 秒一批，模拟引擎写入；同时保留内存队列）。"""

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备外键")
    type = Column(String(32), nullable=False, comment="读数类型：temp/humidity/ph/light/moisture")
    value = Column(Float, nullable=False, comment="数值")
    unit = Column(String(16), default="", comment="单位")
    ts = Column(DateTime, default=datetime.utcnow, index=True, comment="采集时间")


class Alert(Base):
    """阈值告警（未确认 ack=0）。"""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, comment="设备外键")
    type = Column(String(32), default="", comment="告警类型：高温/干旱/酸碱异常等")
    level = Column(String(16), default="warning", comment="级别：warning/critical")
    message = Column(String(255), default="", comment="告警内容")
    ts = Column(DateTime, default=datetime.utcnow, index=True, comment="触发时间")
    ack = Column(Integer, default=0, comment="是否确认：0 未确认 / 1 已确认")


class Field(Base):
    """农田地块（示范数据，省份与种植业数据省份一致）。"""

    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(128), nullable=False, comment="地块名称")
    province = Column(String(64), default="", comment="所属省份")
    area = Column(Float, default=0.0, comment="面积（亩）")
    main_crop = Column(String(64), default="", comment="主栽作物")
    health = Column(String(16), default="良", comment="健康状态：优/良/差")
    owner = Column(String(64), default="", comment="负责人")


class User(Base):
    """系统用户（账号密码登录，v2.1）。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    username = Column(String(64), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(256), nullable=False, comment="密码加盐哈希（sha256:salt:hash）")
    role = Column(String(32), default="admin", comment="角色")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")