# -*- coding: utf-8 -*-
"""FastAPI 入口：REST API + 静态管理页托管。

启动：cd server && uvicorn main:app --host 127.0.0.1 --port 8001
"""

import io
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (FileResponse, JSONResponse, PlainTextResponse,
                               RedirectResponse)
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import analytics
import auth
import import_export as ie
from constants import is_national_level
from database import SessionLocal, db_counts, get_db, init_db
from models import (DimCrop, DimIndicator, DimRegion, DimYear, FactProduction,
                    Field, RawImport, User)
from routers import alerts, devices, fields, mqtt, sensors
from schemas import (DimensionsMeta, HealthOut, ImportReport, RecordCreate,
                     RecordOut, RecordPage, RecordUpdate)
from simulator import engine as simulator_engine

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """启动时自动建表 + 播种示范地块 + 播种默认管理员 + 启动 IoT 模拟引擎。"""
    init_db()
    _seed_fields()
    _seed_admin()
    simulator_engine.start()
    yield
    simulator_engine.stop()


# 示范地块：省份取自种植业数据已有省份，覆盖 优/良/差 三档健康状态
_FIELD_SEED = [
    ("鲁西北玉米示范区", "山东", 1200.0, "玉米", "优", "王建国"),
    ("河南冬小麦高产田", "河南", 980.0, "冬小麦", "优", "李志强"),
    ("黑龙江水稻种植区", "黑龙江", 1500.0, "水稻", "良", "赵大伟"),
    ("成都平原油菜基地", "四川", 760.0, "油菜", "良", "陈晓明"),
    ("河北棉田一号", "河北", 640.0, "棉花", "差", "刘德华"),
    ("苏北稻麦轮作区", "江苏", 1100.0, "水稻", "优", "孙建国"),
    ("安徽大豆示范区", "安徽", 520.0, "大豆", "良", "周文斌"),
    ("湖南柑橘果园", "湖南", 430.0, "柑橘", "优", "吴国华"),
    ("广东蔬菜基地", "广东", 350.0, "蔬菜", "良", "郑海生"),
    ("湖北油菜轮作田", "湖北", 610.0, "油菜", "差", "冯志远"),
    ("江西水稻良种田", "江西", 470.0, "水稻", "良", "何晓峰"),
    ("辽宁大豆试验田", "辽宁", 290.0, "大豆", "差", "罗建华"),
]


def _seed_fields() -> None:
    """fields 表为空时写入示范地块（幂等）。"""
    db = SessionLocal()
    try:
        if db.query(Field).count() > 0:
            return
        for name, province, area, crop, health, owner in _FIELD_SEED:
            db.add(Field(name=name, province=province, area=area, main_crop=crop,
                         health=health, owner=owner))
        db.commit()
        print(f"[v2] 已播种 {len(_FIELD_SEED)} 块示范地块")
    finally:
        db.close()


# 默认管理员（users 表为空时创建；密码可用环境变量 AGRI_ADMIN_PASSWORD 覆盖）
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def _seed_admin() -> None:
    """users 表为空则创建默认管理员 admin/admin123（幂等）。"""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        password = os.environ.get("AGRI_ADMIN_PASSWORD", "").strip() or DEFAULT_ADMIN_PASSWORD
        db.add(User(username=DEFAULT_ADMIN_USERNAME,
                    password_hash=auth.hash_password(password),
                    role="admin"))
        db.commit()
        print(f"默认管理员账号: {DEFAULT_ADMIN_USERNAME}，密码: {password}"
              f"（可用环境变量 AGRI_ADMIN_PASSWORD 覆盖）")
    finally:
        db.close()


app = FastAPI(
    title="种植业数据管理系统 API",
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """把校验错误中的非有限浮点（如客户端发送 NaN/Infinity）清洗为字符串，
    避免 json.dumps 序列化失败导致 500（正常浏览器 JSON.stringify 不会产生 NaN）。"""
    import math

    def _sanitize(v):
        if isinstance(v, float) and not math.isfinite(v):
            return "NaN" if v != v else ("Infinity" if v > 0 else "-Infinity")
        if isinstance(v, dict):
            return {k: _sanitize(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [_sanitize(x) for x in v]
        return v

    errors = jsonable_encoder(exc.errors())
    errors = _sanitize(errors)
    return JSONResponse(status_code=422, content={"detail": errors})


_openapi_orig = app.openapi  # 保存原始实现，避免替换后递归调用


def _custom_openapi():
    """在 OpenAPI 中注入 Bearer securityScheme，让 Swagger 显示 Authorize 按钮。"""
    if app.openapi_schema:
        return app.openapi_schema
    schema = _openapi_orig()
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["AdminToken"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "token",
        "description": "管理 Token（写接口必需）。启动时自动生成于 server/auth_token.txt，"
                       "或通过环境变量 AGRI_ADMIN_TOKEN 指定。",
    }
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi

# CORS：允许大屏(8000/其他端口)跨域读取 /api/*
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源挂载：管理页 + 本地 vendor（无外网依赖）
app.mount("/vendor", StaticFiles(directory=str(PROJECT_DIR / "vendor")), name="vendor")
app.mount("/admin", StaticFiles(directory=str(PROJECT_DIR / "admin"), html=True),
          name="admin")

# v2.2 数字孪生大屏接入：/screen/digital_twin_pro.html + 相对资源（vendor/ 复用，不暴露仓库其他文件）
app.mount("/screen/vendor", StaticFiles(directory=str(PROJECT_DIR / "vendor")),
          name="screen_vendor")


@app.get("/screen/digital_twin_pro.html", include_in_schema=False)
def screen_pro():
    """数字孪生大屏（仓库根目录 digital_twin_pro.html）。"""
    return FileResponse(PROJECT_DIR / "digital_twin_pro.html")

# v2 新增：IoT 设备 / 传感器 / 告警 / 地块 / MQTT 路由
app.include_router(devices.router)
app.include_router(sensors.router)
app.include_router(alerts.router)
app.include_router(fields.router)
app.include_router(mqtt.router)


@app.get("/", include_in_schema=False)
def index():
    """根路径重定向到管理页。"""
    return RedirectResponse(url="/admin/")


# ---------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------
@app.get("/api/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    """健康检查：服务与数据库状态 + 各表行数。"""
    db.execute(select(func.count()).select_from(DimYear))
    return HealthOut(status="ok", db="ok", tables=db_counts(), version=APP_VERSION)


# ---------------------------------------------------------------
# 鉴权状态（管理页登录用）
# ---------------------------------------------------------------
@app.get("/api/auth/status")
def auth_status():
    """返回是否需要登录（写接口必须带管理 Token）。"""
    return {"auth_required": True, "message": "写接口需 Bearer Token；读接口公开"}


@app.post("/api/auth/verify")
def auth_verify(credentials: HTTPAuthorizationCredentials = Depends(auth.bearer_scheme)):
    """校验 Token 有效性，返回 {valid: true/false}。"""
    return {"valid": auth.verify_token(credentials.credentials)}


# ---------------------------------------------------------------
# 账号密码登录（v2.1）：成功返回现有静态 token，兼容全部写接口鉴权
# ---------------------------------------------------------------
class _LoginIn(BaseModel):
    username: str
    password: str


# 简单防暴力：{username: {"fails": int, "lock_until": float}}，5 次失败锁定 60 秒
_LOGIN_FAILS: dict = {}
_LOGIN_MAX_FAILS = 5
_LOGIN_LOCK_SECONDS = 60


@app.post("/api/auth/login")
def auth_login(payload: _LoginIn, db: Session = Depends(get_db)):
    """账号密码登录。成功返回 {token, username, role}（token 即现有管理令牌）。"""
    username = (payload.username or "").strip()
    now = time.time()
    rec = _LOGIN_FAILS.get(username)
    if rec and rec["lock_until"] and now < rec["lock_until"]:
        raise HTTPException(status_code=429,
                            detail="尝试次数过多，请 1 分钟后再试")

    user = db.execute(
        select(User).where(User.username == username)
    ).scalars().first()
    if user is None or not auth.verify_password(payload.password or "", user.password_hash):
        rec = _LOGIN_FAILS.setdefault(username, {"fails": 0, "lock_until": 0})
        rec["fails"] += 1
        if rec["fails"] >= _LOGIN_MAX_FAILS:
            rec["lock_until"] = now + _LOGIN_LOCK_SECONDS
            rec["fails"] = 0
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    _LOGIN_FAILS.pop(username, None)
    return {"token": auth.ADMIN_TOKEN, "username": user.username, "role": user.role}


# ---------------------------------------------------------------
# 元数据
# ---------------------------------------------------------------
@app.get("/api/meta/dimensions", response_model=DimensionsMeta)
def meta_dimensions(db: Session = Depends(get_db)):
    """作物/地区/指标/年份元数据 + 统计卡片计数（管理页下拉与统计用）。"""
    years = sorted(db.execute(select(DimYear.year)).scalars().all())
    regions = db.execute(
        select(DimRegion.province, DimRegion.city, DimRegion.county)
        .order_by(DimRegion.province)
    ).all()
    crops = db.execute(select(DimCrop.crop_name, DimCrop.crop_category)
                       .order_by(DimCrop.crop_name)).all()
    indicators = db.execute(select(DimIndicator.indicator_name, DimIndicator.unit)
                            .order_by(DimIndicator.indicator_id)).all()
    return DimensionsMeta(
        years=years,
        regions=[{"province": p, "city": c, "county": ct} for p, c, ct in regions],
        crops=[{"name": n, "category": cat} for n, cat in crops],
        indicators=[{"name": n, "unit": u} for n, u in indicators],
        counts=db_counts(),
    )


# ---------------------------------------------------------------
# 记录 CRUD
# ---------------------------------------------------------------
def _resolve_dimensions(db: Session, payload: RecordCreate | RecordUpdate):
    """把业务字段解析为维度对象。"""
    year_obj = ie.get_or_create_year(db, payload.year)
    region_obj = ie.get_or_create_region(db, payload.province)
    crop_obj = ie.get_or_create_crop(db, payload.crop, payload.crop_category)
    ind_name = payload.indicator
    unit = payload.unit
    if unit and unit not in ("吨", "亩"):
        # 传入原始单位时做归一化
        ind_name, unit, _factor = ie.normalize_unit(unit)
        ind_name = ie.normalize_indicator(payload.indicator) or ind_name
    ind_obj = ie.get_or_create_indicator(db, ind_name, unit)
    return year_obj, region_obj, crop_obj, ind_obj


@app.get("/api/records", response_model=RecordPage)
def list_records(
    year: int | None = Query(None, description="年份筛选"),
    region: str | None = Query(None, description="省份筛选"),
    crop: str | None = Query(None, description="作物筛选"),
    indicator: str | None = Query(None, description="指标筛选"),
    keyword: str | None = Query(None, description="模糊搜索（省份/作物）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort: str = Query("year", description="排序字段"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """记录列表：分页 + 筛选 + 排序。"""
    query, filters = ie.build_record_query(year, region, crop, indicator, keyword)

    # 排序白名单（防止 SQL 注入）
    sort_cols = {
        "year": DimYear.year, "province": DimRegion.province,
        "crop": DimCrop.crop_name, "indicator": DimIndicator.indicator_name,
        "value": FactProduction.value, "fact_id": FactProduction.fact_id,
        "updated_at": FactProduction.updated_at,
    }
    order_col = sort_cols.get(sort, DimYear.year)
    order_by = order_col.desc() if order == "desc" else order_col.asc()

    total = db.execute(query.with_only_columns(func.count())
                       .where(*filters)).scalar()
    facts = db.execute(
        query.where(*filters).order_by(order_by)
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return RecordPage(total=total or 0, page=page, page_size=page_size,
                      items=[RecordOut(**ie.fact_to_dict(f)) for f in facts])


@app.get("/api/records/{fact_id}", response_model=RecordOut)
def get_record(fact_id: int, db: Session = Depends(get_db)):
    """查询单条记录（管理页编辑弹窗用）。"""
    fact = db.get(FactProduction, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecordOut(**ie.fact_to_dict(fact))


@app.post("/api/records", response_model=RecordOut, status_code=201)
def create_record(payload: RecordCreate, db: Session = Depends(get_db),
                  _auth: None = Depends(auth.require_token)):
    """手工新增记录（维度自动创建，四维键重复时返回 409）。需管理 Token。"""
    year_obj, region_obj, crop_obj, ind_obj = _resolve_dimensions(db, payload)
    exists = db.execute(
        select(FactProduction.fact_id).where(
            FactProduction.year_id == year_obj.year_id,
            FactProduction.region_id == region_obj.region_id,
            FactProduction.crop_id == crop_obj.crop_id,
            FactProduction.indicator_id == ind_obj.indicator_id,
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409,
                            detail="该 年份×省份×作物×指标 记录已存在，请改用编辑")
    fact = FactProduction(
        year_id=year_obj.year_id, region_id=region_obj.region_id,
        crop_id=crop_obj.crop_id, indicator_id=ind_obj.indicator_id,
        value=payload.value, source=payload.source,
        data_quality=payload.data_quality,
    )
    db.add(fact)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="记录已存在（唯一键冲突）")
    db.refresh(fact)
    return RecordOut(**ie.fact_to_dict(fact))


@app.put("/api/records/{fact_id}", response_model=RecordOut)
def update_record(fact_id: int, payload: RecordUpdate, db: Session = Depends(get_db),
                  _auth: None = Depends(auth.require_token)):
    """编辑记录：更新维度引用与数值。需管理 Token。"""
    fact = db.get(FactProduction, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    year_obj, region_obj, crop_obj, ind_obj = _resolve_dimensions(db, payload)
    fact.year_id = year_obj.year_id
    fact.region_id = region_obj.region_id
    fact.crop_id = crop_obj.crop_id
    fact.indicator_id = ind_obj.indicator_id
    fact.value = payload.value
    fact.source = payload.source
    fact.data_quality = payload.data_quality
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="更新后与其他记录唯一键冲突")
    db.refresh(fact)
    return RecordOut(**ie.fact_to_dict(fact))


@app.delete("/api/records/{fact_id}", status_code=200)
def delete_record(fact_id: int, db: Session = Depends(get_db),
                  _auth: None = Depends(auth.require_token)):
    """删除记录。需管理 Token。"""
    fact = db.get(FactProduction, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(fact)
    db.commit()
    return {"deleted": fact_id, "message": "删除成功"}


# ---------------------------------------------------------------
# CSV 导入 / 导出
# ---------------------------------------------------------------
@app.post("/api/import/csv", response_model=ImportReport)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db),
                     _auth: None = Depends(auth.require_token)):
    """上传 CSV 导入：校验 + 单位归一化 + 幂等去重，返回导入报告。需管理 Token。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 .csv 文件")
    report = ie.import_csv(db, file.filename or "upload.csv", data,
                           source=f"upload:{file.filename}")
    return ImportReport(**report)


@app.get("/api/export/csv")
def export_csv(
    year: int | None = None,
    region: str | None = None,
    crop: str | None = None,
    indicator: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """按筛选条件导出 CSV（带 BOM，Excel 可直接打开）。"""
    text = ie.export_csv_text(db, year, region, crop, indicator, keyword)
    content = b"\xef\xbb\xbf" + text.encode("utf-8")
    return PlainTextResponse(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=\"crop_records.csv\"; "
                "filename*=UTF-8''%E7%A7%8D%E6%A4%8D%E4%B8%9A%E6%95%B0%E6%8D%AE.csv",
        },
    )


@app.get("/api/imports")
def list_imports(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """导入历史（raw_imports 表）。"""
    rows = db.execute(
        select(RawImport).order_by(RawImport.id.desc()).limit(limit)
    ).scalars().all()
    return [{
        "id": r.id, "filename": r.filename,
        "import_time": r.import_time.strftime("%Y-%m-%d %H:%M:%S")
        if r.import_time else "",
        "total_rows": r.total_rows, "inserted_rows": r.inserted_rows,
        "updated_rows": r.updated_rows, "failed_rows": r.failed_rows,
        "message": r.message,
    } for r in rows]


# ---------------------------------------------------------------
# 分析聚合（大屏对接）
# ---------------------------------------------------------------
@app.get("/api/analytics/summary")
def analytics_summary(year: int = Query(..., description="年份"), db: Session = Depends(get_db)):
    """大屏总览 KPI。"""
    return analytics.summary(db, year)


@app.get("/api/analytics/ranking")
def analytics_ranking(year: int = Query(...),
                      by: str = Query("crop", pattern="^(crop|region)$"),
                      db: Session = Depends(get_db)):
    """排名：by=crop 作物产量/面积排名，by=region 省份排名。"""
    return analytics.ranking(db, year, by=by)


@app.get("/api/analytics/geo")
def analytics_geo(year: int = Query(...), db: Session = Depends(get_db)):
    """省级地图数据（含行政区划编码）。"""
    return analytics.geo(db, year)


@app.get("/api/analytics/structure")
def analytics_structure(year: int = Query(...), db: Session = Depends(get_db)):
    """作物结构：分类产量/面积占比。"""
    return analytics.structure(db, year)


@app.get("/api/analytics/trend")
def analytics_trend(crop: str | None = None, region: str | None = None,
                    start: int | None = None, end: int | None = None,
                    indicator: str = Query("产量", description="产量/面积"),
                    db: Session = Depends(get_db)):
    """时间趋势。"""
    return analytics.trend(db, crop=crop, region=region, start=start, end=end,
                           indicator=indicator)


@app.get("/api/analytics/province/{name}")
def analytics_province(name: str, year: int = Query(...),
                       db: Session = Depends(get_db)):
    """省份×作物明细：name 支持简称（山东）或全称（山东省），year 必填。

    契约字段见 analytics.province_crop_detail docstring（大屏详情面板按此解析）。
    - "全国"/空 等全国汇总级 → 400（明细口径不适用于全国行）。
    - 省份不存在 → 404；省份存在但该年无数据 → 200 + crops 空数组（前端渲染空态）。
    """
    if is_national_level(name):
        raise HTTPException(status_code=400, detail="省份不能为全国级（全国/空）")
    result = analytics.province_crop_detail(db, name, year)
    if result is None:
        raise HTTPException(status_code=404, detail="省份不存在")
    return result


@app.get("/api/dashboard")
def api_dashboard(db: Session = Depends(get_db)):
    """大屏聚合端点：返回与 dashboard_data.json 兼容的完整数据包。"""
    return analytics.dashboard_payload(db)


# 供导出脚本调用的纯函数（无 HTTP 依赖）
build_dashboard_payload = analytics.dashboard_payload


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)