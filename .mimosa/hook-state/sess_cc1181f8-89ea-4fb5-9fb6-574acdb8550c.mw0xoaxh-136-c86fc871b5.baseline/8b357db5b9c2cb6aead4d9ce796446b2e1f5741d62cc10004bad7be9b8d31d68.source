"""04 章 lab：把 02 章抓到的 quotes 数据存进 SQLite 并查询验证。

顺带演示同一份数据的三种落盘方式（CSV / JSON Lines / SQLite），
以及去重、UPSERT、参数绑定、事务的完整流程。

前置：先运行 python projects/crawler-lab/02_requests_quotes.py 生成 data/quotes.json。

运行：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/04_store_sqlite.py
"""

import csv
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
QUOTES_JSON = DATA_DIR / "quotes.json"


def load_data() -> list[dict]:
    data = json.loads(QUOTES_JSON.read_text(encoding="utf-8"))
    return data["quotes"]


def save_csv(quotes: list[dict]) -> None:
    """CSV：utf-8-sig 带 BOM，Excel 双击打开不乱码。tags 列用 | 拼接。"""
    path = DATA_DIR / "quotes.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "author", "tags"])  # 表头
        for q in quotes:
            writer.writerow([q["text"], q["author"], "|".join(q["tags"])])
    print(f"[csv]    写入 {len(quotes)} 行 -> {path.name}")


def save_jsonl(quotes: list[dict]) -> None:
    """JSON Lines：每行一个独立 JSON 对象，适合大文件逐行追加写。"""
    path = DATA_DIR / "quotes.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for q in quotes:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"[jsonl]  写入 {len(quotes)} 行 -> {path.name}")


def save_sqlite(quotes: list[dict]) -> None:
    """SQLite：参数绑定 + UNIQUE 去重 + UPSERT + 事务。"""
    path = DATA_DIR / "quotes.db"
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quotes (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                text   TEXT NOT NULL UNIQUE,   -- 名言全文唯一 -> 数据库层去重防线
                author TEXT NOT NULL,
                tags   TEXT NOT NULL           -- 标签用逗号拼接（教学简化；规范库设计见第 4 章正文）
            )
            """
        )
        # UPSERT：已存在（text 重复）则只更新 tags，不产生重复行。
        # 注意 SQL 是常量字符串，外数据全部走 ? 占位符——这是硬规范。
        upsert_sql = """
            INSERT INTO quotes (text, author, tags)
            VALUES (?, ?, ?)
            ON CONFLICT(text) DO UPDATE SET tags = excluded.tags
        """
        params = [(q["text"], q["author"], ",".join(q["tags"])) for q in quotes]
        cur.executemany(upsert_sql, params)   # executemany 批量绑定，一条事务内完成
        conn.commit()                          # 写操作必须 commit 才落盘
        print(f"[sqlite] UPSERT {len(params)} 行 -> {path.name}")
    finally:
        conn.close()


def verify_sqlite() -> None:
    """SELECT 验证：总数、按作者聚合、条件查询。"""
    conn = sqlite3.connect(DATA_DIR / "quotes.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM quotes")
    print("\n== 验证：名言总数 =", cur.fetchone()[0])

    cur.execute(
        "SELECT author, COUNT(*) AS n FROM quotes GROUP BY author ORDER BY n DESC LIMIT 5"
    )
    print("== 作品最多的 5 位作者：")
    for author, n in cur.fetchall():
        print(f"   {author:<22} {n} 条")

    cur.execute("SELECT text FROM quotes WHERE tags LIKE ? LIMIT 2", ("%books%",))
    print("== 含 'books' 标签的样例：")
    for (text,) in cur.fetchall():
        print("   -", text[:52], "...")

    conn.close()


def main() -> None:
    quotes = load_data()
    save_csv(quotes)
    save_jsonl(quotes)
    save_sqlite(quotes)
    verify_sqlite()

    # 去重验证：再跑一遍入库，行数不应增加（UNIQUE + UPSERT 幂等）
    save_sqlite(quotes)
    conn = sqlite3.connect(DATA_DIR / "quotes.db")
    (n,) = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()
    conn.close()
    print(f"\n重复入库后总数仍为 {n}（UNIQUE 约束 + UPSERT 保证幂等）")


if __name__ == "__main__":
    main()
