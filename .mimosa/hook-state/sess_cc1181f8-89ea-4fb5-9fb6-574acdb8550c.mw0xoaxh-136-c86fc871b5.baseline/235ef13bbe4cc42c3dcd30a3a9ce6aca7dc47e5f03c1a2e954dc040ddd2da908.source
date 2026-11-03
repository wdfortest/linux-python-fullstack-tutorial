"""pytest 共享夹具：用临时 SQLite + 样例数据替换真实数据库依赖。

测试隔离三原则：
1. 不碰真实 books.db（用 tmp_path 临时库）
2. 不发网络请求（样例数据手工造）
3. 每个 fixture 独立建库，用完即删
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from api.database import get_db
from api.main import app
from fastapi.testclient import TestClient

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upc TEXT UNIQUE,
    title TEXT NOT NULL,
    price REAL,
    price_excl_tax REAL,
    tax REAL,
    availability INTEGER,
    rating INTEGER,
    category TEXT,
    num_reviews INTEGER,
    description TEXT,
    image_url TEXT,
    detail_url TEXT UNIQUE,
    crawled_at TEXT
);
"""


def _insert_minimal(conn: sqlite3.Connection, title: str, price: float, rating: int, detail_url: str) -> None:
    """插入最小字段的书。静态 SQL + 参数元组绑定。"""
    t = title
    p = price
    r = rating
    u = detail_url
    conn.execute("INSERT OR REPLACE INTO books (title, price, rating, detail_url) VALUES (?, ?, ?, ?)", (t, p, r, u))


def _insert_full(conn: sqlite3.Connection, title: str, price: float, rating: int, category: str, availability: int, detail_url: str) -> None:
    """插入较全字段的书（供详情接口断言）。"""
    t = title
    p = price
    r = rating
    c = category
    a = availability
    u = detail_url
    conn.execute("INSERT OR REPLACE INTO books (title, price, rating, category, availability, detail_url) VALUES (?, ?, ?, ?, ?, ?)", (t, p, r, c, a, u))


@pytest.fixture()
def client(tmp_path: Path):
    """提供指向临时库的 TestClient。"""
    db_file = tmp_path / "test_books.db"
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA)

    # 造 12 本样例书：覆盖多个分类/评分，保证统计有差异
    _insert_minimal(conn, "Book A", 10.5, 5, "u1")
    _insert_minimal(conn, "Book B", 20.0, 4, "u2")
    _insert_minimal(conn, "Book C", 35.5, 3, "u3")
    _insert_minimal(conn, "Book D", 48.0, 2, "u4")
    _insert_minimal(conn, "Book E", 59.9, 1, "u5")
    _insert_full(conn, "Fiction Alpha", 25.0, 4, "Fiction", 10, "u6")
    _insert_full(conn, "Fiction Beta", 30.0, 5, "Fiction", 5, "u7")
    _insert_full(conn, "History One", 45.0, 3, "History", 0, "u8")
    _insert_full(conn, "History Two", 15.0, 5, "History", 3, "u9")
    _insert_minimal(conn, "Poetry X", 12.3, 4, "u10")
    _insert_minimal(conn, "Poetry Y", 22.8, 5, "u11")
    _insert_minimal(conn, "Poetry Z", 33.1, 1, "u12")
    conn.commit()
    conn.close()

    def override_get_db():
        c = sqlite3.connect(db_file)
        c.row_factory = sqlite3.Row
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
