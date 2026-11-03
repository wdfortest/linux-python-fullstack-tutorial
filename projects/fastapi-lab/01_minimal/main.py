"""fastapi-lab/01 最小可运行应用：第一个 API。

运行（在仓库根目录）：
    source ~/opt/jjyv/bin/activate
    cd projects/fastapi-lab/01_minimal && uvicorn main:app --port 8100 --reload
验证：
    curl http://127.0.0.1:8100/
    curl "http://127.0.0.1:8100/books/3?fields=title,price"
    curl -X POST http://127.0.0.1:8100/books -H "Content-Type: application/json" -d '{"title": "示例书", "price": 42.0, "rating": 5}'
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="fastapi-lab 01 · 最小应用",
    description="路由 / 路径参数 / 查询参数 / Pydantic 请求体 / 自动文档",
    version="1.0.0",
)

FAKE_BOOKS: dict[int, dict] = {
    1: {"title": "A Light in the Attic", "price": 51.77, "rating": 3},
    2: {"title": "Tipping the Velvet", "price": 53.74, "rating": 1},
    3: {"title": "Sapiens: A Brief History", "price": 54.23, "rating": 5},
}


class BookIn(BaseModel):
    """请求体模型：字段即校验规则（Pydantic v2）。"""

    title: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0, le=1000)
    rating: int = Field(ge=1, le=5)


@app.get("/")
def root() -> dict:
    return {"message": "hello, FastAPI", "docs": "/docs"}


@app.get("/books/{book_id}")
def get_book(
    book_id: int = Path(ge=1),          # 路径参数：类型自动转换 + 校验
    fields: str = Query("title,price", pattern="^[a-z,]+$"),   # 查询参数带校验
) -> dict:
    if book_id not in FAKE_BOOKS:
        raise HTTPException(status_code=404, detail="book not found")
    wanted = set(fields.split(","))
    return {k: v for k, v in FAKE_BOOKS[book_id].items() if k in wanted}


@app.post("/books", status_code=201)
def create_book(book: BookIn) -> dict:   # 请求体：Pydantic 自动校验
    new_id = max(FAKE_BOOKS) + 1
    FAKE_BOOKS[new_id] = book.model_dump()
    return {"id": new_id, **FAKE_BOOKS[new_id]}
