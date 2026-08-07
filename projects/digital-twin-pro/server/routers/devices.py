# -*- coding: utf-8 -*-
"""设备中心：设备 CRUD + 统计 + 控制命令（模拟）。"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import auth
from database import get_db
from models import Device

router = APIRouter(prefix="/api/devices", tags=["devices"])

DEVICE_TYPES = ["soil", "weather", "irrigation", "camera"]


class DeviceCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=64, description="设备编号")
    name: str = Field(..., min_length=1, max_length=128, description="设备名称")
    type: str = Field(..., description="类型：soil/weather/irrigation/camera")
    province: str = Field("", max_length=64, description="所在省份")
    status: str = Field("online", description="online/offline/fault")


class DeviceUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    type: str | None = None
    province: str | None = Field(None, max_length=64)
    status: str | None = None


class CommandIn(BaseModel):
    action: str = Field(..., pattern="^(on|off)$", description="on=上线 / off=下线")


def _fmt(d: Device) -> dict:
    return {
        "id": d.id, "code": d.code, "name": d.name, "type": d.type,
        "province": d.province, "status": d.status,
        "online_rate": round(d.online_rate or 0.0, 1),
        "last_seen": d.last_seen.strftime("%Y-%m-%d %H:%M:%S") if d.last_seen else "",
        "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else "",
    }


@router.get("")
def list_devices(
    status: str | None = Query(None, description="online/offline/fault"),
    type: str | None = Query(None, description="soil/weather/irrigation/camera"),
    keyword: str | None = Query(None, description="编号/名称模糊搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """设备列表：状态/类型筛选 + 分页。"""
    q = db.query(Device)
    if status:
        q = q.filter(Device.status == status)
    if type:
        q = q.filter(Device.type == type)
    if keyword:
        q = q.filter(Device.code.contains(keyword) | Device.name.contains(keyword))
    total = q.count()
    items = [ _fmt(d) for d in q.order_by(Device.id).offset((page - 1) * page_size)
              .limit(page_size).all() ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/stats")
def device_stats(db: Session = Depends(get_db)):
    """在线率统计。"""
    rows = db.query(Device.status, Device.online_rate).all()
    total = len(rows)
    online = sum(1 for s, _ in rows if s == "online")
    offline = sum(1 for s, _ in rows if s == "offline")
    fault = sum(1 for s, _ in rows if s == "fault")
    online_rate = round(online / total * 100, 1) if total else 0.0
    return {
        "total": total, "online": online, "offline": offline, "fault": fault,
        "online_rate": online_rate,
    }


@router.post("", status_code=201)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db),
                  _auth: str = Depends(auth.require_token)):
    """新增设备。需管理 Token。"""
    if payload.type not in DEVICE_TYPES:
        raise HTTPException(status_code=422, detail=f"类型必须是 {DEVICE_TYPES}")
    if db.query(Device).filter(Device.code == payload.code).first():
        raise HTTPException(status_code=409, detail="设备编号已存在")
    dev = Device(code=payload.code, name=payload.name, type=payload.type,
                 province=payload.province, status=payload.status, online_rate=100.0)
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return _fmt(dev)


@router.put("/{device_id}")
def update_device(device_id: int, payload: DeviceUpdate,
                  db: Session = Depends(get_db),
                  _auth: str = Depends(auth.require_token)):
    """编辑设备。需管理 Token。"""
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    data = payload.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(dev, k, v)
    db.commit()
    db.refresh(dev)
    return _fmt(dev)


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db),
                  _auth: str = Depends(auth.require_token)):
    """删除设备。需管理 Token。"""
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(dev)
    db.commit()
    return {"deleted": device_id, "message": "删除成功"}


@router.post("/{device_id}/command")
def device_command(device_id: int, payload: CommandIn,
                   db: Session = Depends(get_db),
                   _auth: str = Depends(auth.require_token)):
    """控制开关（模拟）：on → 上线，off → 下线。需管理 Token。"""
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    dev.status = "online" if payload.action == "on" else "offline"
    dev.last_seen = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": device_id, "status": dev.status}