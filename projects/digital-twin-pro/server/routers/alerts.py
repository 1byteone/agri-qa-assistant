# -*- coding: utf-8 -*-
"""告警：列表 + 确认。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

import auth
from database import get_db
from models import Alert, Device

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _fmt(a: Alert, dev_map) -> dict:
    dev = dev_map.get(a.device_id)
    return {
        "id": a.id,
        "device_id": a.device_id,
        "device_code": dev.code if dev else "",
        "device_name": dev.name if dev else "",
        "type": a.type, "level": a.level, "message": a.message,
        "ts": a.ts.strftime("%Y-%m-%d %H:%M:%S") if a.ts else "",
        "ack": a.ack or 0,
    }


@router.get("")
def list_alerts(ack: int | None = Query(None, description="0 未确认 / 1 已确认 / 缺省全部"),
                level: str | None = Query(None, description="warning/critical"),
                limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """告警列表（新→旧）。"""
    q = db.query(Alert)
    if ack is not None:
        q = q.filter(Alert.ack == ack)
    if level:
        q = q.filter(Alert.level == level)
    rows = q.order_by(desc(Alert.ts)).limit(limit).all()
    dev_map = {d.id: d for d in db.query(Device).all()}
    return {"total": len(rows), "items": [_fmt(a, dev_map) for a in rows]}


@router.put("/{alert_id}/ack")
def ack_alert(alert_id: int, db: Session = Depends(get_db),
              _auth: str = Depends(auth.require_token)):
    """确认告警。需管理 Token。"""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert.ack = 1
    db.commit()
    return {"ok": True, "id": alert_id, "ack": 1}