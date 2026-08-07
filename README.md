# AI_EXAM

项目根目录，包含两个独立子项目及通用文档/资源。

## 目录结构

```
AI_EXAM/
├── projects/                    # 独立项目根目录
│   ├── expense-tracker/        # 项目 A：费用追踪器
│   │   ├── expense-tracker/    # 前端源码（Vite + TS）
│   │   └── data/               # 原始与清洗后 CSV 数据
│   └── digital-twin-pro/       # 项目 B：数字孪生系统
│       ├── frontend/           # 前端源码（Vite）
│       ├── server/             # 后端服务（FastAPI + SQLite）
│       └── admin/              # 管理后台（静态页面）
├── docs/                        # 项目文档
│   └── prompt-engineering/     # Prompt Engineering 学习资料
├── screenshots/                 # 统一截图目录（含 e2e 测试截图）
├── reports/                     # 报告输出目录
├── scripts/                     # 脚本目录
└── temp/                        # 临时文件目录
```

## 快速开始

### expense-tracker
```bash
cd projects/expense-tracker/expense-tracker
npm install
npm run dev
```

### digital-twin-pro
```bash
# 前端
cd projects/digital-twin-pro/frontend
npm install
npm run dev

# 后端
cd projects/digital-twin-pro/server
pip install -r requirements.txt
uvicorn main:app --reload
```

## 备注

- `prompt/` 目录因文件占用暂无法自动清理，内容已迁移至 `docs/prompt-engineering/`
- 所有截图已统一整理至 `screenshots/`