# -*- coding: utf-8 -*-
"""把数据库聚合结果导出为 dashboard_data.json（大屏静态兜底文件）。

大屏 digital_twin_pro.html 通过 fetch('dashboard_data.json') 读取数据；
本脚本生成与旧文件相同结构的 JSON，可配合系统计划任务定时执行。

用法：cd server && python export_dashboard.py
"""

import json
import sys
from pathlib import Path

from analytics import dashboard_payload
from database import SessionLocal, init_db

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
OUT_PATH = PROJECT_DIR / "dashboard_data.json"


def main():
    init_db()
    db = SessionLocal()
    try:
        payload = dashboard_payload(db)
        OUT_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        years = payload["years"]
        print(f"已导出 {OUT_PATH}")
        print(f"  年份: {years}")
        print(f"  kpi: { {str(y): payload['kpi'][str(y)]['total_production'] for y in years} }"
              f"（总产量，吨）")
        print(f"  省份地图数据: {len(payload['province'])} 条")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())