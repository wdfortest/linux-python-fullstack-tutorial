#!/usr/bin/env python
"""lab 01 · SQL 从入门到进阶：用真实图书数据练习 SELECT / GROUP BY / JOIN / CTE / 窗口函数。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/01_sql_basics.py

说明：
- 数据来自 projects/book-insight/data/books.db（1000 本图书，全程只读不改）；
- 脚本会把 books 表复制到本目录 data/lab01.db，并新建一张小的 category_notes
  表用于演示 JOIN 与写操作——原库不受任何影响；
- 本仓库硬规范：所有 SQL 都是完整静态字面量，含外部数据处一律参数绑定
  （SQLite 用 ? 占位符）。拼接 SQL 字符串的做法禁止出现在真实代码中。
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "data"
SRC_DB = LAB_DIR.parent / "book-insight" / "data" / "books.db"
LAB_DB = DATA_DIR / "lab01.db"

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


def show(cur: sqlite3.Cursor, sql: str, params: tuple = ()) -> None:
    """执行一条 SQL 并打印结果（自动带上列名）。"""
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print("-- SQL:", sql)
    if params:
        print("-- 绑定参数:", params)
    print("   | ".join(cols))
    for row in rows[:8]:
        print("   " + " | ".join(str(v)[:38] for v in row))
    if len(rows) > 8:
        print(f"   ...（共 {len(rows)} 行，只展示前 8 行）")


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if LAB_DB.exists():
        LAB_DB.unlink()
    shutil.copyfile(SRC_DB, LAB_DB)
    print(f"已把只读源库复制为工作库: {LAB_DB}")

    conn = sqlite3.connect(LAB_DB)
    cur = conn.cursor()
    print(f"SQLite 版本: {sqlite3.sqlite_version}（RIGHT/FULL JOIN 需 3.39+，窗口函数需 3.25+）")

    # ------------------------------------------------------------------ 1
    section("1. SELECT 三件套：WHERE / ORDER BY / LIMIT")
    show(cur, "SELECT title, price, rating, category FROM books WHERE rating >= ? AND price <= ? ORDER BY price DESC LIMIT 5", (4, 30.0))
    show(cur, "SELECT title, price FROM books WHERE category = ? ORDER BY price LIMIT 3", ("Poetry",))
    show(cur, "SELECT COUNT(*) AS total, ROUND(AVG(price), 2) AS avg_price, MIN(price) AS min_price, MAX(price) AS max_price FROM books")

    # ------------------------------------------------------------------ 2
    section("2. GROUP BY + HAVING：先分组聚合，再对聚合结果过滤")
    show(cur, "SELECT category, COUNT(*) AS n, ROUND(AVG(price), 2) AS avg_price, ROUND(AVG(rating), 2) AS avg_rating FROM books GROUP BY category HAVING COUNT(*) >= 40 ORDER BY n DESC")

    # WHERE 与 HAVING 的区别：同一条件放两个位置，结果完全不同
    print("\n[WHERE 过滤行] 每个分类里 rating=5 的书有几本（先筛行再分组）:")
    show(cur, "SELECT category, COUNT(*) AS n5 FROM books WHERE rating = 5 GROUP BY category ORDER BY n5 DESC LIMIT 5")
    print("\n[HAVING 过滤组] 书目数 >= 50 的分类才有几本（先分组再筛组）:")
    show(cur, "SELECT category, COUNT(*) AS n FROM books GROUP BY category HAVING COUNT(*) >= 50 ORDER BY n DESC")

    # ------------------------------------------------------------------ 3
    section("3. 准备 JOIN 演示数据：一张书架位置备注表 category_notes")
    cur.execute("DROP TABLE IF EXISTS category_notes")
    cur.execute("CREATE TABLE category_notes (category TEXT PRIMARY KEY, shelf TEXT, note TEXT)")
    notes = [
        ("Poetry", "A-01", "诗歌区靠窗"),
        ("Fantasy", "B-03", "奇幻区书架较高"),
        ("Mystery", "C-02", "悬疑区需要预约"),
        ("Add a comment", "D-09", "此分类是站点遗留命名"),
        ("Archival", "Z-99", "该分类在 books 表中不存在"),
    ]
    # 参数绑定写操作：executemany + ? 占位符，杜绝拼接
    cur.executemany("INSERT INTO category_notes (category, shelf, note) VALUES (?, ?, ?)", notes)
    conn.commit()
    print(f"category_notes 已建表并插入 {len(notes)} 行（参数绑定写入）")

    print("\n[INNER JOIN] 只返回两边都匹配的行（books 只有 Poetry/Fantasy/Mystery/Add a comment 有备注）:")
    show(cur, "SELECT b.category, COUNT(*) AS n, c.shelf FROM books b INNER JOIN category_notes c ON b.category = c.category GROUP BY b.category, c.shelf ORDER BY n DESC")
    print("\n[LEFT JOIN] 保留左表全部行（无备注的分类 shelf 为 NULL）:")
    show(cur, "SELECT b.category, c.shelf FROM books b LEFT JOIN category_notes c ON b.category = c.category GROUP BY b.category, c.shelf ORDER BY b.category LIMIT 6")
    print("\n[LEFT JOIN ... IS NULL] 反连接：找没有备注的分类（前 5 个）:")
    show(cur, "SELECT DISTINCT b.category FROM books b LEFT JOIN category_notes c ON b.category = c.category WHERE c.category IS NULL ORDER BY b.category LIMIT 5")
    print("\n[RIGHT JOIN] 以右表为主（Archival 只有备注没有书）:")
    show(cur, "SELECT c.category, c.shelf, COUNT(b.id) AS book_cnt FROM category_notes c RIGHT JOIN books b ON b.category = c.category GROUP BY c.category, c.shelf HAVING c.category IS NOT NULL")
    print("\n[CROSS JOIN] 笛卡尔积：39 个 5 星分类 x 5 条备注 = 195 行（截取 6 行）:")
    cur.execute("SELECT b.category, c.shelf FROM books b CROSS JOIN category_notes c WHERE b.rating = 5 LIMIT 6")
    for row in cur.fetchall():
        print("  ", row)

    # ------------------------------------------------------------------ 4
    section("4. 子查询：标量 / IN / 相关子查询")
    print("[标量子查询] 比全站均价贵的书有几本:")
    show(cur, "SELECT COUNT(*) AS n FROM books WHERE price > (SELECT AVG(price) FROM books)")
    print("[相关子查询] 价格高于本分类均价的书（每类前 2 本）:")
    show(cur, "SELECT category, title, price FROM books AS b WHERE price > (SELECT AVG(price) FROM books AS i WHERE i.category = b.category) ORDER BY category, price DESC LIMIT 6")

    # ------------------------------------------------------------------ 5
    section("5. CTE（WITH 公用表表达式）：把复杂查询拆成有名字的步骤")
    show(cur, "WITH big AS (SELECT category, COUNT(*) AS n, AVG(price) AS avg_price FROM books GROUP BY category HAVING COUNT(*) >= 40) SELECT category, n, ROUND(avg_price, 2) AS avg_price FROM big ORDER BY avg_price DESC")

    # ------------------------------------------------------------------ 6
    section("6. 窗口函数（MySQL 8+ / SQLite 3.25+）：聚合不折叠行")
    print("[ROW_NUMBER] 每个分类最贵的 2 本书（子查询里编号，外层过滤）:")
    show(cur, "SELECT category, title, price FROM (SELECT category, title, price, ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rn FROM books) WHERE rn <= 2 ORDER BY category, price DESC LIMIT 8")
    print("[RANK] 全站价格第 1~5 名（并列同名次）:")
    show(cur, "SELECT RANK() OVER (ORDER BY price DESC) AS rk, title, price FROM books LIMIT 5")
    print("[窗口累计] 按价格升序的累计金额（前 5 行）:")
    show(cur, "SELECT title, price, ROUND(SUM(price) OVER (ORDER BY price, id), 2) AS running_total FROM books ORDER BY price, id LIMIT 5")

    # ------------------------------------------------------------------ 7
    section("7. 索引与执行计划：让查询从全表扫描变成索引查找")
    # 源库爬虫已建过 idx_books_rating；在副本上先删掉，才能看到"无索引"的样子
    cur.execute("DROP INDEX IF EXISTS idx_books_rating")
    conn.commit()
    cur.execute("EXPLAIN QUERY PLAN SELECT title FROM books WHERE rating = 5")
    print("-- 建索引前（SCAN books = 全表扫描）:")
    for row in cur.fetchall():
        print("  ", row[3])
    cur.execute("CREATE INDEX idx_books_rating ON books (rating)")
    conn.commit()
    cur.execute("EXPLAIN QUERY PLAN SELECT title FROM books WHERE rating = 5")
    print("-- 建索引后（SEARCH ... USING INDEX = 索引查找）:")
    for row in cur.fetchall():
        print("  ", row[3])
    print("   （MySQL 里对应命令是 EXPLAIN SELECT ...，输出列不同但思想一致）")

    # ------------------------------------------------------------------ 8
    section("8. 写操作与事务：commit 生效，rollback 撤销")
    cur.execute("SELECT COUNT(*) FROM category_notes")
    before = cur.fetchone()[0]
    cur.execute("INSERT INTO category_notes (category, shelf, note) VALUES (?, ?, ?)", ("Temp", "X-00", "待会回滚"))
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM category_notes")
    print(f"插入并 commit 后行数: {before} -> {cur.fetchone()[0]}")
    cur.execute("INSERT INTO category_notes (category, shelf, note) VALUES (?, ?, ?)", ("Temp2", "X-01", "马上回滚"))
    conn.rollback()
    cur.execute("SELECT COUNT(*) FROM category_notes")
    print(f"插入后 rollback，行数恢复为: {cur.fetchone()[0]}")

    # 清理演示用表，保持工作库干净
    cur.execute("DROP TABLE category_notes")
    conn.commit()
    print("\n演示表已清理。books 表数据与源库一致，未做任何修改。")
    conn.close()


if __name__ == "__main__":
    main()
