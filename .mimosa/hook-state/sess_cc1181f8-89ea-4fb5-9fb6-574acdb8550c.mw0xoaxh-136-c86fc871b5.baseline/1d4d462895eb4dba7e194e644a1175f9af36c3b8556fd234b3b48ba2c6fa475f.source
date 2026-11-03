"""book-insight 集中管理的查询模块。

硬性安全规范：本文件所有 SQL 都是完整静态字面量——不含任何参数、
不含任何字符串拼接与动态组装；需要按条件筛选的数据一律全量取出后
在 Python 侧完成（数据集仅 1000 行）。生产环境的参数化过滤标准写法
见教程 docs/06-fastapi-backend/03-数据库集成(SQLAlchemy).md。
"""
from __future__ import annotations

import sqlite3


def load_books(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """全量图书明细（静态 SQL）。"""
    return conn.execute("SELECT id, title, price, rating, category, availability, num_reviews, image_url, detail_url, upc, price_excl_tax, tax, description, crawled_at FROM books ORDER BY id").fetchall()


def summary_row(conn: sqlite3.Connection) -> sqlite3.Row:
    """汇总指标（静态聚合 SQL）。"""
    return conn.execute("SELECT COUNT(*) AS total_books, COUNT(DISTINCT category) AS categories, AVG(price) AS avg_price, MAX(price) AS max_price, MIN(price) AS min_price, AVG(rating) AS avg_rating, SUM(CASE WHEN availability > 0 THEN 1 ELSE 0 END) AS in_stock, AVG(availability) AS avg_stock, COALESCE(SUM(num_reviews), 0) AS total_reviews FROM books").fetchone()


def price_rows(conn: sqlite3.Connection) -> list:
    """价格列（用于 Python 侧中位数与直方图分桶）。"""
    return conn.execute("SELECT price FROM books").fetchall()


def ratings_rows(conn: sqlite3.Connection) -> list:
    """评分分布（静态聚合）。"""
    return conn.execute("SELECT rating, COUNT(*) AS cnt FROM books WHERE rating IS NOT NULL GROUP BY rating ORDER BY rating").fetchall()


def categories_rows(conn: sqlite3.Connection) -> list:
    """分类聚合（静态聚合）。"""
    return conn.execute("SELECT category, COUNT(*) AS cnt, AVG(price) AS avg_price, AVG(rating) AS avg_rating, COALESCE(SUM(availability), 0) AS total_stock FROM books WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC").fetchall()


def top_rated_rows(conn: sqlite3.Connection) -> list:
    """评分最高 10 本（静态排序）。"""
    return conn.execute("SELECT title, price, rating, category FROM books ORDER BY rating DESC, num_reviews DESC, availability DESC LIMIT 10").fetchall()


def availability_rows(conn: sqlite3.Connection) -> list:
    """在售/缺货计数（静态聚合）。"""
    return conn.execute("SELECT CASE WHEN availability > 0 THEN 1 ELSE 0 END AS flag, COUNT(*) AS cnt FROM books GROUP BY flag").fetchall()


def scatter_rows(conn: sqlite3.Connection) -> list:
    """价格-评分全量点（API 返回前隔行抽样）。"""
    return conn.execute("SELECT price, rating FROM books").fetchall()
