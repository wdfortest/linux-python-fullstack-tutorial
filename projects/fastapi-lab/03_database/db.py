"""fastapi-lab/03 数据层：全部 SQL 为完整静态字面量 + 参数元组绑定。

安全规范（与实战项目 book-insight 一致）：
- 每条 SQL 都是单行静态字面量，任何变量只能经 ? 占位符进入
- 变量先解包为普通局部变量，再绑定（保持调用处干净可审计）
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "lab03.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL,
    price    REAL,
    rating   INTEGER,
    category TEXT
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def list_books(conn: sqlite3.Connection, limit: int, offset: int) -> list[sqlite3.Row]:
    lim = limit
    off = offset
    return conn.execute("SELECT id, title, price, rating, category FROM books ORDER BY id LIMIT ? OFFSET ?", (lim, off)).fetchall()


def count_books(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) AS c FROM books").fetchone()["c"])


def get_book(conn: sqlite3.Connection, book_id: int) -> sqlite3.Row | None:
    bid = book_id
    return conn.execute("SELECT id, title, price, rating, category FROM books WHERE id = ?", (bid,)).fetchone()


def insert_book(conn: sqlite3.Connection, title: str, price: float, rating: int, category: str) -> int:
    t, p, r, c = title, price, rating, category
    cur = conn.execute("INSERT INTO books (title, price, rating, category) VALUES (?, ?, ?, ?)", (t, p, r, c))
    conn.commit()
    return int(cur.lastrowid)


def update_book(conn: sqlite3.Connection, book_id: int, title: str, price: float, rating: int, category: str) -> bool:
    bid, t, p, r, c = book_id, title, price, rating, category
    cur = conn.execute("UPDATE books SET title = ?, price = ?, rating = ?, category = ? WHERE id = ?", (t, p, r, c, bid))
    conn.commit()
    return cur.rowcount > 0


def delete_book(conn: sqlite3.Connection, book_id: int) -> bool:
    bid = book_id
    cur = conn.execute("DELETE FROM books WHERE id = ?", (bid,))
    conn.commit()
    return cur.rowcount > 0
