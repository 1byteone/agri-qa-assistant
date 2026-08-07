# -*- coding: utf-8 -*-
"""环境监测：传感器最新读数 + 历史曲线。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from models import Device, SensorReading
from simulator import engine

router = APIRouter(prefix="/api/sensors", tags=["sensors"])

SENSOR_META = {
    "temp": ("温度", "°C"),
    "humidity": ("湿度", "%"),
    "ph": ("土壤PH", ""),
    "light": ("光照", "lux"),
    "moisture": ("土壤墒情", "%"),
}


@router.get("/latest")
def sensors_latest(db: Session = Depends(get_db)):
    """各设备各类型最新读数（内存队列，升序）。"""
    rows = engine.latest()
    dev_map = {d.id: d for d in db.query(Device).all()}
    items = []
    for r in rows:
        dev = dev_map.get(r["device_id"])
        label, unit = SENSOR_META.get(r["type"], (r["type"], r.get("unit", "")))
        items.append({
            "device_id": r["device_id"],
            "device_code": r.get("device_code", ""),
            "device_name": dev.name if dev else "",
            "province": dev.province if dev else "",
            "type": r["type"],
            "label": label,
            "value": r["value"],
            "unit": unit,
            "ts": r["ts"].strftime("%Y-%m-%d %H:%M:%S"),
        })
    items.sort(key=lambda x: (x["device_id"], x["type"]))
    return {"generated_at": items[-1]["ts"] if items else "", "items": items}


@router.get("/history")
def sensors_history(device_id: int | None = Query(None, description="设备 id，缺省返回全部"),
                    limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """历史读数（DB，按时间升序返回，供曲线追加）。"""
    q = db.query(SensorReading)
    if device_id:
        q = q.filter(SensorReading.device_id == device_id)
    rows = q.order_by(desc(SensorReading.ts)).limit(limit).all()
    rows = list(reversed(rows))  # 升序
    dev_map = {d.id: d for d in db.query(Device).all()}
    items = []
    for r in rows:
        dev = dev_map.get(r.device_id)
        label, _unit = SENSOR_META.get(r.type, (r.type, r.unit or ""))
        items.append({
            "id": r.id, "device_id": r.device_id,
            "device_code": dev.code if dev else "",
            "device_name": dev.name if dev else "",
            "type": r.type, "label": label,
            "value": round(r.value, 2), "unit": r.unit or "",
            "ts": r.ts.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {"items": items, "limit": limit}