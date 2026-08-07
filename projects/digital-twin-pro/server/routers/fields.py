# -*- coding: utf-8 -*-
"""农田 GIS：地块列表（示范数据由 main 启动时 seed）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Field

router = APIRouter(prefix="/api/fields", tags=["fields"])

HEALTH_ORDER = {"优": 0, "良": 1, "差": 2}


def _fmt(f: Field) -> dict:
    return {
        "id": f.id, "name": f.name, "province": f.province,
        "area": round(f.area or 0.0, 1), "main_crop": f.main_crop,
        "health": f.health, "owner": f.owner,
    }


@router.get("")
def list_fields(db: Session = Depends(get_db)):
    """地块列表（优/良/差 排序）。"""
    rows = db.query(Field).all()
    rows.sort(key=lambda f: HEALTH_ORDER.get(f.health, 1))
    return {"total": len(rows), "items": [_fmt(f) for f in rows]}