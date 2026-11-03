"""pipelines.py：Item Pipeline 示例——内存去重 + SQLite 入库（参数绑定）。

Pipeline 是 Item 的“质检 + 仓储”流水线，返回 item 继续传递，抛 DropItem 则丢弃。
本文件演示三层去重里的两层：内存 set（快）+ 数据库 UNIQUE 约束（可靠）。
"""

import logging
import sqlite3
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from book_scrapy.settings import DATA_DIR

logger = logging.getLogger(__name__)

# 反面教材（仅示意，禁止出现在真实代码中）：
#   sql = f"INSERT INTO books VALUES ('{upc}', '{title}', ...)"   # 危险！
# 书名里出现 O'Brien 之类的单引号就会打碎 SQL 语法，更别说 SQL 注入风险。
# 正确做法永远是：占位符 ? + 参数元组，让驱动负责转义。
UPSERT_SQL = """
INSERT INTO books (upc, title, category, price, rating, in_stock, stock_qty, url)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(upc) DO UPDATE SET
    price = excluded.price,
    rating = excluded.rating,
    in_stock = excluded.in_stock,
    stock_qty = excluded.stock_qty
"""


class SQLitePipeline:
    """把 BookItem 写进 SQLite，按 UPC 去重（UPSERT 保证重跑幂等）。"""

    BATCH_COMMIT_SIZE = 100  # 每 100 条提交一次，兼顾性能与崩溃安全

    def open_spider(self, spider):
        DATA_DIR.mkdir(exist_ok=True)
        self.db_path = DATA_DIR / "books.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        # upc 设为主键：数据库层的最后防线，重复数据写不进来
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                upc      TEXT PRIMARY KEY,
                title    TEXT NOT NULL,
                category TEXT,
                price    REAL,
                rating   INTEGER,
                in_stock INTEGER,
                stock_qty INTEGER,
                url      TEXT
            )
            """
        )
        self.conn.commit()
        self.seen_upcs: set[str] = set()  # 内存层去重，避免无效的重复写入
        self.saved = 0
        self.dropped = 0

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        upc = adapter.get("upc")
        if not upc:
            self.dropped += 1
            raise DropItem(f"缺少 upc，丢弃: {adapter.get('title')!r}")
        if upc in self.seen_upcs:
            self.dropped += 1
            raise DropItem(f"重复 upc: {upc}")

        self.cur.execute(
            UPSERT_SQL,
            (
                upc,
                adapter.get("title"),
                adapter.get("category"),
                adapter.get("price"),
                adapter.get("rating"),
                int(bool(adapter.get("in_stock"))),
                adapter.get("stock_qty", 0),
                adapter.get("url"),
            ),
        )
        self.seen_upcs.add(upc)
        self.saved += 1
        if self.saved % self.BATCH_COMMIT_SIZE == 0:
            self.conn.commit()  # 分批提交：崩溃时最多丢一小批
        return item  # 必须返回 item（或抛 DropItem），否则后续管线/FEEDS 拿不到数据

    def close_spider(self, spider):
        self.conn.commit()
        self.cur.execute("SELECT COUNT(*) FROM books")
        (total,) = self.cur.fetchone()
        self.conn.close()
        logger.info("SQLitePipeline 完成：本次入库 %d 条，去重丢弃 %d 条，表内共 %d 条 -> %s",
                    self.saved, self.dropped, total, self.db_path)
