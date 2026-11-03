"""Pydantic v2 Schema：请求/响应的数据契约，与 ORM 模型分层。

为什么分开？ORM 模型面向数据库结构，Schema 面向 API 消费者；
二者解耦后，内部字段调整不会直接泄漏到 API 契约。
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float | None
    rating: int | None
    category: str | None
    availability: int | None
    num_reviews: int | None
    image_url: str | None
    detail_url: str | None


class BookDetail(BookOut):
    upc: str | None
    price_excl_tax: float | None
    tax: float | None
    description: str | None
    crawled_at: str | None


class BookPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BookOut]


class Summary(BaseModel):
    total_books: int
    categories: int
    avg_price: float
    median_price: float
    max_price: float
    min_price: float
    avg_rating: float
    in_stock: int
    out_of_stock: int
    total_reviews: int
    avg_stock: float


class RatingItem(BaseModel):
    rating: int
    count: int


class PriceBucket(BaseModel):
    bucket: str
    count: int


class CategoryStat(BaseModel):
    category: str
    count: int
    avg_price: float
    avg_rating: float
    total_stock: int


class TopBook(BaseModel):
    title: str
    price: float | None
    rating: int | None
    category: str | None


class NamedValue(BaseModel):
    name: str
    value: int


class ChartsAll(BaseModel):
    """大屏一次拉取全部图表数据的聚合响应。"""

    summary: Summary
    rating_distribution: list[RatingItem]
    price_histogram: list[PriceBucket]
    categories: list[CategoryStat]
    top_rated: list[TopBook]
    price_rating_scatter: list[dict]
    availability: list[NamedValue]
