# -*- coding: utf-8 -*-
"""MQTT 接入预留：配置读取/保存 + 数据源切换。

- GET  /api/mqtt/config  返回当前配置（默认关闭）
- POST /api/mqtt/config  保存配置；enabled=true 且未安装 paho-mqtt 时返回 501（不崩溃）
- 配置持久化到 server/mqtt_config.json
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import auth
from simulator import MqttSource, engine

router = APIRouter(prefix="/api/mqtt", tags=["mqtt"])

CONFIG_FILE = Path(__file__).resolve().parent.parent / "mqtt_config.json"

DEFAULT_CONFIG = {
    "enabled": False,
    "host": "127.0.0.1",
    "port": 1883,
    "topic": "agri/sensors/#",
    "username": "",
    "password": "",
}


def _load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def _save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                           encoding="utf-8")


def _paho_available() -> bool:
    try:
        import paho.mqtt.client  # noqa: F401
        return True
    except ImportError:
        return False


class MqttConfigIn(BaseModel):
    enabled: bool = False
    host: str = Field("127.0.0.1", max_length=128)
    port: int = Field(1883, ge=1, le=65535)
    topic: str = Field("agri/sensors/#", max_length=256)
    username: str = Field("", max_length=128)
    password: str = Field("", max_length=128)


@router.get("/config")
def get_config():
    """读取 MQTT 配置（默认关闭）。"""
    cfg = _load_config()
    return {**cfg, "paho_available": _paho_available(),
            "source": "mqtt" if (cfg["enabled"] and _paho_available()) else "simulated"}


@router.post("/config")
def set_config(payload: MqttConfigIn, _auth: str = Depends(auth.require_token)):
    """保存 MQTT 配置并尝试切换数据源。需管理 Token。"""
    cfg = payload.model_dump()
    if cfg["enabled"]:
        if not _paho_available():
            raise HTTPException(
                status_code=501,
                detail="需 pip install paho-mqtt 后才能启用 MQTT；当前保留模拟数据源",
            )
        try:
            source = MqttSource(host=cfg["host"], port=cfg["port"], topic=cfg["topic"])
            source.connect()
            engine.set_source(source)
        except Exception as exc:
            raise HTTPException(status_code=502,
                                detail=f"MQTT 连接失败: {exc}（模拟数据源已保留）")
    else:
        from simulator import SimulatedSource
        engine.set_source(SimulatedSource())
    _save_config(cfg)
    return {**cfg, "paho_available": _paho_available(),
            "source": "mqtt" if (cfg["enabled"] and _paho_available()) else "simulated"}