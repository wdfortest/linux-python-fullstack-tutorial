#!/usr/bin/env python
"""lab 02 · SQLAlchemy 2.0：Engine / Connection / Session，2.0 风格 ORM 与参数绑定。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/02_sqlalchemy_orm.py

说明：
- 模型 Book 与 projects/book-insight/data/books.db 的 books 表一一对应；
- 脚本把源库复制到 data/lab02.db 再做增删改——原库始终只读；
- 本仓库硬规范：text() 原生 SQL 一律使用 :name 占位符 + params 字典绑定，
  禁止任何形式的 SQL 字符串拼接。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from sqlalchemy import URL, Integer, String, Text, create_engine, desc, func, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "data"
SRC_DB = LAB_DIR.parent / "book-insight" / "data" / "books.db"
LAB_DB = DATA_DIR / "lab02.db"

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


# ---------------------------------------------------------------- 模型定义
class Base(DeclarativeBase):
    pass


class Book(Base):
    """与爬虫建的 books 表一一对应（对齐 projects/book-insight/api/models.py）。"""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upc: Mapped[str | None] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    price: Mapped[float | None]
    price_excl_tax: Mapped[float | None]
    tax: Mapped[float | None]
    availability: Mapped[int | None]
    rating: Mapped[int | None]
    category: Mapped[str | None] = mapped_column(String(128))
    num_reviews: Mapped[int | None]
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(512))
    detail_url: Mapped[str | None] = mapped_column(String(512), unique=True)
    crawled_at: Mapped[str | None] = mapped_column(String(32))

    def __repr__(self) -> str:  # 让 print 会话查询结果时可读
        return f"Book(id={self.id}, title={self.title!r}, price={self.price}, rating={self.rating})"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if LAB_DB.exists():
        LAB_DB.unlink()
    shutil.copyfile(SRC_DB, LAB_DB)

    # ---------------------------------------------------------- 1 Engine
    section("1. Engine：连接串 + 连接池，全局只建一次")
    engine = create_engine(f"sqlite:///{LAB_DB}", echo=False)
    print("engine:", engine.url.render_as_string(hide_password=True))

    # MySQL 连接串写法（本机无 MySQL 服务，仅演示 URL 构造，不建立连接）：
    # 密码从环境变量读，绝不写进代码——部署步骤见 Ubuntu 教程第 8 篇。
    mysql_url = URL.create(
        drivername="mysql+pymysql",
        username="bookuser",
        password=os.environ.get("MYSQL_PASSWORD", "<from-env>"),
        host="127.0.0.1",
        port=3306,
        database="books",
    )
    print("MySQL URL 写法示例:", mysql_url.render_as_string(hide_password=True))

    # ---------------------------------------------------------- 2 Connection + text()
    section("2. Connection + text()：原生 SQL，:name 参数绑定（硬规范）")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT title, price FROM books WHERE rating >= :r AND price <= :p ORDER BY price DESC LIMIT :n"),
            {"r": 4, "p": 30.0, "n": 3},
        )
        for row in result:
            print("  ", row)
        agg = conn.execute(
            text("SELECT COUNT(*) AS n, ROUND(AVG(price), 2) AS avg_price FROM books WHERE rating = :r"),
            {"r": 5},
        ).one()
        print("   5 星书:", agg._asdict())

    # ---------------------------------------------------------- 3 Session 查询
    section("3. Session + 2.0 风格查询：select() 语句是核心")
    with Session(engine) as session:
        stmt = select(Book).where(Book.rating >= 5).order_by(desc(Book.price)).limit(3)
        for book in session.scalars(stmt):
            print("  ", book)

        print("\n[常用查询] func 聚合 + group_by：书目最多的 3 个分类")
        stmt = (
            select(Book.category, func.count().label("n"), func.avg(Book.price).label("avg_price"))
            .group_by(Book.category)
            .order_by(desc("n"))
            .limit(3)
        )
        for row in session.execute(stmt):
            print("  ", row.category, row.n, round(row.avg_price, 2))

        print("\n[标量子查询] 价格高于本分类均价的书（前 3 本）")
        sub = select(func.avg(Book.price)).where(Book.category == Book.category).scalar_subquery()
        stmt = select(Book.title, Book.price).where(Book.price > sub).limit(3)
        for row in session.execute(stmt):
            print("  ", row)

    # ---------------------------------------------------------- 4 CRUD
    section("4. CRUD：add / 修改属性 / delete，最后 commit 才落库")
    with Session(engine) as session:
        new_book = Book(
            upc="teach000000001",
            title="SQLAlchemy 2.0 入门（演示行）",
            price=9.99,
            price_excl_tax=9.99,
            tax=0.0,
            availability=1,
            rating=5,
            category="Default",
            num_reviews=0,
            detail_url="https://books.toscrape.com/catalogue/teaching-row/index.html",
            crawled_at="2026-11-04T00:00:00+00:00",
        )
        session.add(new_book)
        session.flush()  # 拿到自增 id，但尚未 commit
        print("flush 后（事务内可见）:", new_book)

        new_book.price = 12.49  # 修改属性 = UPDATE
        session.commit()
        print("commit 后 id =", new_book.id)

        with Session(engine) as s2:
            obj = s2.scalar(select(Book).where(Book.upc == "teach000000001"))
            print("重新查询验证:", obj)
            obj.price = 15.0
            s2.rollback()  # 未 commit 的修改被丢弃
            s2.refresh(obj)
            print("rollback + refresh 后 price =", obj.price)

            s2.delete(obj)
            s2.commit()
            print("delete + commit 后再查:", s2.scalar(select(Book).where(Book.upc == "teach000000001")))

    # ---------------------------------------------------------- 5 pandas 预告
    section("5. 与 pandas 结合预告：read_sql 也走参数绑定")
    import pandas as pd

    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT category, price, rating FROM books WHERE rating >= :r"),
            conn,
            params={"r": 5},
        )
    print(df.groupby("category").size().sort_values(ascending=False).head(3).to_string())
    print("...(第 3 章正式展开)")

    engine.dispose()
    print("\n工作库 lab02.db 已保留在 data/ 目录，可自行打开检查；源库未动。")


if __name__ == "__main__":
    main()
