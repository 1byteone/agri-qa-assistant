# -*- coding: utf-8 -*-
"""数据库引擎与会话管理（SQLite WAL 模式）。"""

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from constants import DB_PATH

# 数据库文件绝对路径：server/crop_data.db
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / DB_PATH

# SQLite 引擎：check_same_thread=False 允许 FastAPI 多线程访问
engine = create_engine(
    f"sqlite:///{DB_FILE}",
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):
    """连接建立时开启 WAL 模式与外键约束（提升并发读写性能）。"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


def init_db() -> None:
    """首次运行时自动建表（幂等）。"""
    # 延迟导入模型，确保所有表都注册到 metadata
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖：提供数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_counts() -> dict:
    """各表行数统计（健康检查用）。"""
    with engine.connect() as conn:
        tables = [
            "dim_year", "dim_region", "dim_crop", "dim_indicator",
            "fact_production", "raw_imports",
            "devices", "sensor_readings", "alerts", "fields",
        ]
        counts = {}
        for t in tables:
            try:
                counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            except Exception:
                counts[t] = None
        return counts


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成:", DB_FILE)
    print(db_counts())