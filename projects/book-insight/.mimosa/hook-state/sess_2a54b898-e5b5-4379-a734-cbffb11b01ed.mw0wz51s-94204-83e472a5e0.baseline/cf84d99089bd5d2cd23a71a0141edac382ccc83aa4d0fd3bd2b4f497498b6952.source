"""SQLAlchemy ORM 模型，与爬虫建的 books 表一一对应（不负责建表）。"""
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Book(Base):
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
