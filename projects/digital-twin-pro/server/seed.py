# -*- coding: utf-8 -*-
"""一键入库脚本：把 data/cleaned_*.csv 导入 SQLite（幂等，可重复执行）。

用法：cd server && python seed.py
"""

import sys
from pathlib import Path

from database import SessionLocal, db_counts, init_db
from import_export import import_csv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

# 待导入的清洗后文件（已归一化为 吨/亩）
SEED_FILES = ["cleaned_2023.csv", "cleaned_2024.csv"]


def main():
    init_db()
    db = SessionLocal()
    try:
        grand = {"inserted_rows": 0, "updated_rows": 0, "failed_rows": 0,
                 "warning_rows": 0, "total_rows": 0}
        for fname in SEED_FILES:
            path = DATA_DIR / fname
            if not path.exists():
                print(f"[跳过] 文件不存在: {path}")
                continue
            data = path.read_bytes()
            report = import_csv(db, fname, data, source=f"seed:{fname}")
            for k in ("inserted_rows", "updated_rows", "failed_rows",
                      "warning_rows", "total_rows"):
                grand[k] += report.get(k, 0)
            print(f"[{fname}] {report['message']}")

        counts = db_counts()
        print("-" * 60)
        print("入库汇总：")
        print(f"  CSV 总行数     : {grand['total_rows']} 行"
              f"（其中新增 {grand['inserted_rows']}，更新 {grand['updated_rows']}，"
              f"失败 {grand['failed_rows']}，警告 {grand['warning_rows']}）")
        print(f"  维度表 dim_year      : {counts['dim_year']} 行")
        print(f"  维度表 dim_region    : {counts['dim_region']} 行")
        print(f"  维度表 dim_crop      : {counts['dim_crop']} 行")
        print(f"  维度表 dim_indicator : {counts['dim_indicator']} 行")
        print(f"  事实表 fact_production : {counts['fact_production']} 行"
              "（<= 原始行数，四维唯一键自动去重合并）")
        print(f"  导入记录 raw_imports  : {counts['raw_imports']} 条")
        print("-" * 60)
        print("提示：cleaned_2023.csv 含 8 条『香蕉-产量』重复键（数值略有差异），"
              "按唯一键合并为 1 行（取后值）。")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())