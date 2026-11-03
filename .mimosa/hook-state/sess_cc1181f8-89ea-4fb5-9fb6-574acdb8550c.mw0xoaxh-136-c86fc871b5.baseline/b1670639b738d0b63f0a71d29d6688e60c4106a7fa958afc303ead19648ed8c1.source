"""数据库连接管理（运行时用标准库 sqlite3 直连）。

为什么用 sqlite3 而不是 SQLAlchemy 会话？本项目数据集固定在单文件
SQLite（1000 行）且只读，标准库直连最简单可靠；ORM 建模的教学见
models.py 与教程 docs/06-fastapi-backend/03-数据库集成(SQLAlchemy).md。
部署到 MySQL 时把本模块替换为 PyMySQL 连接即可，SQL 基本不变。
"""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Generator
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("BOOKS_DB_PATH", str(PROJECT_DIR / "data" / "books.db")))


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI 依赖：请求级连接，row_factory 让行可按列名访问。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
