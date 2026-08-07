# -*- coding: utf-8 -*-
"""IoT 模拟数据引擎（v2）。

- threading 守护线程，每 3 秒为一轮：在线设备生成一批读数（温度/湿度/PH/光照/土壤墒情），
  写入内存队列（保留最近 200 条）+ sensor_readings 表；
- 阈值越界写入 alerts 表（同设备同类型 60 秒冷却，避免刷屏）；
- 设备状态 online/offline/fault 按概率轮换，在线率随状态平滑变化；
- 数据源抽象：SensorSource（SimulatedSource / MqttSource 两个实现）。
  MQTT 开启后（mqtt router 调用 engine.set_source），模拟线程停止，改用真实订阅源；
  paho-mqtt 未安装时 mqtt router 返回 501，模拟数据保留不崩溃。
"""

import random
import threading
from collections import deque
from datetime import datetime

from database import SessionLocal
from models import Alert, Device, SensorReading

TICK_SECONDS = 3.0
MAX_QUEUE = 200

# 设备定义：10 台，分布在不同省份（与种植业数据省份一致）
DEVICE_DEFS = [
    {"code": "SOIL-SD-01", "name": "济南土壤墒情站", "type": "soil", "province": "山东"},
    {"code": "SOIL-HN-01", "name": "郑州土壤墒情站", "type": "soil", "province": "河南"},
    {"code": "SOIL-HLJ-01", "name": "哈尔滨土壤墒情站", "type": "soil", "province": "黑龙江"},
    {"code": "SOIL-SC-01", "name": "成都土壤墒情站", "type": "soil", "province": "四川"},
    {"code": "WX-HB-01", "name": "石家庄气象站", "type": "weather", "province": "河北"},
    {"code": "WX-JS-01", "name": "南京气象站", "type": "weather", "province": "江苏"},
    {"code": "IRR-AH-01", "name": "合肥灌溉控制器", "type": "irrigation", "province": "安徽"},
    {"code": "IRR-HN-02", "name": "长沙灌溉控制器", "type": "irrigation", "province": "湖南"},
    {"code": "CAM-GD-01", "name": "广州农田摄像头", "type": "camera", "province": "广东"},
    {"code": "CAM-HB-02", "name": "武汉农田摄像头", "type": "camera", "province": "湖北"},
]

# 设备类型 → 读数类型
SENSOR_TYPES = {
    "soil": ["moisture", "ph", "temp"],
    "weather": ["temp", "humidity", "light"],
    "irrigation": ["moisture"],
    "camera": [],
}

# 读数生成范围
RANGES = {
    "temp": (15.0, 35.0, "°C"),
    "humidity": (40.0, 90.0, "%"),
    "ph": (5.5, 7.5, ""),
    "light": (1000.0, 80000.0, "lux"),
    "moisture": (20.0, 80.0, "%"),
}

# 告警阈值：(类型, 级别, 判定, 文案)
def _check_thresholds(dev, rtype, value):
    """返回 (告警类型, 级别, 文案) 或 None。"""
    if rtype == "temp":
        if value > 38:
            return ("高温", "critical", f"{dev['name']} 温度 {value:.1f}°C 严重超标（>38°C）")
        if value > 35:
            return ("高温", "warning", f"{dev['name']} 温度 {value:.1f}°C 超阈值（>35°C）")
    elif rtype == "humidity":
        if value < 30:
            return ("干旱", "critical", f"{dev['name']} 空气湿度 {value:.1f}% 严重偏低（<30%）")
        if value < 40:
            return ("干旱", "warning", f"{dev['name']} 空气湿度 {value:.1f}% 低于阈值（<40%）")
    elif rtype == "moisture":
        if value < 22:
            return ("干旱", "warning", f"{dev['name']} 土壤墒情 {value:.1f}% 过低（<22%）")
    elif rtype == "ph":
        if value < 5.0 or value > 8.0:
            return ("酸碱异常", "critical", f"{dev['name']} PH {value:.2f} 严重偏离（<5.0 或 >8.0）")
        if value < 5.5 or value > 7.5:
            return ("酸碱异常", "warning", f"{dev['name']} PH {value:.2f} 超阈值（5.5-7.5）")
    elif rtype == "light":
        if value > 75000:
            return ("光照过强", "warning", f"{dev['name']} 光照 {value:.0f} lux 过强（>75000）")
    return None


class SensorSource:
    """数据源抽象接口。"""

    def read_once(self):
        """生成/采集一批读数，返回 [{device_id, type, value, unit, ts}]。"""
        raise NotImplementedError

    def enabled(self):
        return True


class SimulatedSource(SensorSource):
    """模拟数据源：按 DEVICE_DEFS 概率轮换状态并生成读数。"""

    def __init__(self):
        self.devices = [dict(d) for d in DEVICE_DEFS]
        for d in self.devices:
            d["status"] = "online"
            d["online_rate"] = 100.0
            d["last_seen"] = None

    def _next_status(self, cur):
        """状态概率轮换：85% 保持在线，离线/故障小幅波动。"""
        r = random.random()
        if cur == "online":
            if r < 0.06:
                return "offline"
            if r < 0.10:
                return "fault"
            return "online"
        # 非在线：恢复概率更高，演示效果
        if r < 0.35:
            return "online"
        if r < 0.55:
            return "offline"
        return "fault"

    def read_once(self):
        """一轮模拟：返回 (readings, device_states)。device_states 供引擎写回 DB。"""
        readings = []
        states = []
        now = datetime.utcnow()
        for d in self.devices:
            d["status"] = self._next_status(d["status"])
            if d["status"] == "online":
                d["online_rate"] = min(100.0, d["online_rate"] + 0.5)
                d["last_seen"] = now
                for rtype in SENSOR_TYPES.get(d["type"], []):
                    lo, hi, unit = RANGES[rtype]
                    value = round(random.uniform(lo, hi), 2)
                    readings.append({
                        "device_id": None,  # 引擎回填真实 id
                        "code": d["code"],
                        "type": rtype, "value": value,
                        "unit": unit, "ts": now,
                    })
            else:
                d["online_rate"] = max(0.0, d["online_rate"] - 3.0)
            states.append({
                "code": d["code"], "status": d["status"],
                "online_rate": round(d["online_rate"], 1),
                "last_seen": d["last_seen"],
            })
        return readings, states


class MqttSource(SensorSource):
    """MQTT 数据源（预留）。paho-mqtt 未安装时不会实例化；已安装则订阅 topic 灌入读数。"""

    def __init__(self, host="127.0.0.1", port=1883, topic="agri/sensors/#"):
        self.host, self.port, self.topic = host, port, topic
        self.client = None
        self.connected = False

    def connect(self):
        import paho.mqtt.client as mqtt  # 可选依赖，未安装抛 ImportError
        self.client = mqtt.Client()
        self.client.connect(self.host, self.port, 5)
        self.client.subscribe(self.topic)
        self.client.loop_start()
        self.connected = True
        return True

    def read_once(self):
        # 预留：真实实现从 client 的消息缓冲取数据；此处返回空避免崩溃
        return [], []

    def enabled(self):
        return self.connected


class SimulatorEngine:
    """后台引擎：守护线程每 3 秒跑一轮。"""

    def __init__(self):
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.queue = deque(maxlen=MAX_QUEUE)  # 内存读数队列（保留最近 200 条）
        self.source = SimulatedSource()
        self._last_alert = {}  # (device_id, type) -> ts 冷却
        self._device_map = {}  # code -> device_id

    # ---------- 生命周期 ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._sync_devices()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="iot-simulator")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def running(self):
        return bool(self._thread and self._thread.is_alive())

    def set_source(self, source: SensorSource):
        """切换数据源（MQTT 启用时调用；模拟线程由外部决定是否 stop）。"""
        with self._lock:
            self.source = source

    # ---------- 设备同步 ----------
    def _sync_devices(self):
        """确保 DEVICE_DEFS 全部入库，返回 code->id 映射。"""
        db = SessionLocal()
        try:
            existing = {d.code: d.id for d in db.query(Device).all()}
            for d in DEVICE_DEFS:
                if d["code"] not in existing:
                    dev = Device(code=d["code"], name=d["name"], type=d["type"],
                                 province=d["province"], status="online",
                                 online_rate=100.0)
                    db.add(dev)
                    db.flush()
                    existing[d["code"]] = dev.id
            db.commit()
            self._device_map = existing
        finally:
            db.close()

    # ---------- 主循环 ----------
    def _loop(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                pass  # 单轮失败不影响引擎
            self._stop.wait(TICK_SECONDS)

    def _tick(self):
        readings, states = self.source.read_once()
        now = datetime.utcnow()
        db = SessionLocal()
        try:
            # 状态回写
            for s in states:
                did = self._device_map.get(s["code"])
                if did:
                    db.query(Device).filter(Device.id == did).update({
                        "status": s["status"], "online_rate": s["online_rate"],
                        "last_seen": s["last_seen"] or now,
                    })
            # 读数入库 + 内存队列 + 阈值告警
            for r in readings:
                did = self._device_map.get(r.pop("code"))
                if not did:
                    continue
                r["device_id"] = did
                db.add(SensorReading(device_id=did, type=r["type"],
                                     value=r["value"], unit=r["unit"], ts=r["ts"]))
                with self._lock:
                    self.queue.append(dict(r, device_code=self._code_of(did)))
                alert = _check_thresholds(self._dev_def(did), r["type"], r["value"])
                if alert:
                    key = (did, r["type"])
                    last = self._last_alert.get(key)
                    if last is None or (now - last).total_seconds() > 60:
                        db.add(Alert(device_id=did, type=alert[0], level=alert[1],
                                     message=alert[2], ts=now, ack=0))
                        self._last_alert[key] = now
            db.commit()
        finally:
            db.close()

    # ---------- 辅助 ----------
    def _code_of(self, did):
        for code, cid in self._device_map.items():
            if cid == did:
                return code
        return ""

    def _dev_def(self, did):
        for d in self.source.devices if isinstance(self.source, SimulatedSource) else []:
            if self._device_map.get(d["code"]) == did:
                return d
        return {"name": "设备"}

    # ---------- 查询（供 routers 使用） ----------
    def latest(self):
        """各设备最新读数（按 device_id+type 去重，取最新）。"""
        result = {}
        for r in list(self.queue):
            key = (r["device_id"], r["type"])
            result[key] = r
        return list(result.values())

    def history(self, device_id=None, limit=200):
        """内存队列最近 N 条（升序）。"""
        rows = list(self.queue)
        if device_id:
            rows = [r for r in rows if r["device_id"] == int(device_id)]
        return rows[-limit:]


# 模块级单例：routers 与 main 共用
engine = SimulatorEngine()