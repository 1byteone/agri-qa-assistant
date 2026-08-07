# 智慧农业管理系统 v2

面向本机演示的农业数据管理平台：FastAPI + SQLite 后端，Vue3 + Element Plus + ECharts 前端，双主题可切换，内置 IoT 模拟数据引擎（MQTT 预留）。

## 一、快速启动

**前置**：Python 3.13 + 已装 fastapi/uvicorn/sqlalchemy；Node 22 + npm（依赖已装则跳过）。

```bat
:: 终端 1：后端（端口 8001）
start_backend.bat

:: 终端 2：前端（端口 5173）
start_frontend.bat
```

启动后浏览器访问 **http://127.0.0.1:5173**。

**登录**：在登录页输入管理 Token。Token 由后端首次启动自动生成，位于 `server/auth_token.txt`；
也可通过环境变量 `AGRI_ADMIN_TOKEN` 指定。读接口公开，写接口（增删改/导入/设备控制/告警确认）需要 Token。

> 注：后端 uvicorn 固定监听 `127.0.0.1:8001`；前端 Vite dev 通过 proxy 转发 `/api` 与 `/vendor` 到 8001，
> 全程无外网 CDN 依赖（ECharts/Element Plus 均为 npm 本地包，中国地图 GeoJSON 已本地化到 `vendor/china.json`）。

## 二、架构

```
AI_EXAM/
├── server/                      # FastAPI 后端
│   ├── main.py                  # 入口：挂载全部路由 + lifespan 启动模拟引擎 + 播种示范地块
│   ├── database.py              # SQLite 引擎（WAL 模式）
│   ├── models.py                # 星型种植业模型 + v2 新增 devices/sensor_readings/alerts/fields
│   ├── auth.py                  # Bearer Token 鉴权（写接口）
│   ├── analytics.py             # 分析聚合（/api/dashboard 等，既有）
│   ├── simulator.py             # IoT 模拟引擎（守护线程 3 秒一轮）+ SensorSource 抽象
│   └── routers/                 # v2 新增路由：devices/sensors/alerts/fields/mqtt
├── frontend/                    # Vue3 前端
│   └── src/
│       ├── api/request.js       # axios 封装（Bearer token / 401 跳登录）
│       ├── stores/              # Pinia：auth(登录态) + theme(深浅主题)
│       ├── layouts/MainLayout.vue  # 侧边菜单(6模块) + 顶栏(主题切换/退出)
│       ├── styles/theme.css     # 双主题 CSS 变量
│       └── views/               # Login + 6 大模块
├── vendor/china.json            # 中国地图 GeoJSON（本地化，无外网依赖）
├── start_backend.bat / start_frontend.bat
└── README.md
```

## 三、六大模块

| 模块 | 路由 | 数据来源 | 说明 |
|------|------|----------|------|
| 驾驶舱 | `/cockpit` | `/api/dashboard` + `/api/devices/stats` + `/api/alerts` | KPI 卡片(数字滚动动画)、2023 vs 2024 省级产量对比、Top10 排名、全国产量地图 |
| 数据管理 | `/data` | `/api/records` + `/api/meta/dimensions` | 作物分类树、多维筛选、分页、新增/编辑/删除/批量删除、CSV 导入导出、数值校验(≥0) |
| 设备中心 | `/devices` | `/api/devices*` | 统计卡、在线率环形图、状态徽章、控制(启动/停机)、新增/编辑 |
| 农田GIS | `/gis` | `/api/fields` + `/vendor/china.json` | 省级健康着色地图 + 地块标记点、地块列表(优绿/良黄/差红) |
| 环境监测 | `/env` | `/api/sensors/*` + `/api/alerts` | 5 类传感器实时卡片(正常/超限)、每 3 秒轮询实时曲线、告警一键确认 |
| 分析报表 | `/analytics` | `/api/dashboard` + `/api/analytics/province/{name}` | 省级对比、作物结构饼图、Top 作物排名、省份×作物明细表、导出 CSV |

## 四、IoT 模拟引擎与 MQTT 预留

- `server/simulator.py` 内置 10 台模拟设备（4 土壤传感器 / 2 气象站 / 2 灌溉控制器 / 2 摄像头，分布 10 省），
  守护线程每 3 秒一轮：在线设备生成温度/湿度/PH/光照/土壤墒情读数（写 `sensor_readings` 表 + 内存队列保留 200 条），
  状态按概率在 在线/离线/故障 间轮换；阈值越界（温度>35 高温、湿度<40 干旱、PH 出界、光照>75000、墒情<22）写入 `alerts`（同设备同类型 60 秒冷却）。
- **数据源抽象**：`SensorSource`（`SimulatedSource` / `MqttSource`）。
  `GET /api/mqtt/config` 查看配置（默认关闭）；`POST /api/mqtt/config` 打开 `enabled=true` 时：
  - 已安装 `paho-mqtt` → 连接 broker 并切换为 MQTT 数据源；
  - 未安装 → 返回 501「需 pip install paho-mqtt」，模拟数据保留不崩溃。

## 五、后端 API（v2 新增）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/api/devices?status=&type=&page=` | 设备列表（分页筛选） | 公开 |
| GET | `/api/devices/stats` | 设备统计（total/online/offline/fault/online_rate） | 公开 |
| POST | `/api/devices` | 新增设备 | Token |
| PUT/DELETE | `/api/devices/{id}`、`/api/devices/{id}` | 编辑/删除 | Token |
| POST | `/api/devices/{id}/command` | 控制开关 `{action:on\|off}`（模拟） | Token |
| GET | `/api/sensors/latest` | 各设备最新读数 | 公开 |
| GET | `/api/sensors/history?device_id=&limit=` | 历史读数（升序） | 公开 |
| GET | `/api/alerts?ack=0&limit=` | 告警列表 | 公开 |
| PUT | `/api/alerts/{id}/ack` | 确认告警 | Token |
| GET | `/api/fields` | 地块列表（健康状态） | 公开 |
| GET/POST | `/api/mqtt/config` | MQTT 配置读取/保存 | GET 公开 / POST Token |

既有 API（/api/dashboard、/api/records、/api/analytics/*、/api/import/csv、/api/export/csv、/api/meta/dimensions 等）保持兼容不变。

## 六、主题切换

顶栏月亮/太阳按钮切换深浅主题：浅色企业风（默认）与深色科技风。
CSS 变量集中在 `frontend/src/styles/theme.css`（`:root` 浅色 + `html.dark` 深色），
配合 Element Plus `dark` class 联动，选择结果存 `localStorage`（key: `agri_theme`）。

## 七、常见问题

- **npm install 慢/失败**：已默认使用 npmmirror 镜像并采用本地缓存目录（`.npm-cache`）。
  若仍失败可执行 `npm config set registry https://registry.npmmirror.com` 后重试。
- **后端 8001 被占用**：先结束占用进程再启动 `start_backend.bat`。
- **数据管理导入 CSV**：列需为 年份/省份/作物/分类/指标/数值(含单位) 等，后端自动归一化单位并幂等去重，导入结果见弹窗报告。