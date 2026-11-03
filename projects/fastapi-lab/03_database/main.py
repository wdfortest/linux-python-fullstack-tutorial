"""fastapi-lab/03 完整 CRUD 应用：分层（路由 -> db 层）+ Pydantic 契约。

运行：
    cd projects/fastapi-lab/03_database && uvicorn main:app --port 8102 --reload
验证：
    curl -X POST http://127.0.0.1:8102/api/books -H "Content-Type: application/json" \
         -d '{"title":"Sapiens","price":54.2,"rating":5,"category":"History"}'
    curl http://127.0.0.1:8102/api/books?limit=5
    curl http://127.0.0.1:8102/api/books/1
    curl -X PUT http://127.0.0.1:8102/api/books/1 -H "Content-Type: application/json" \
         -d '{"title":"Sapiens (2nd)","price":49.9,"rating":5,"category":"History"}'
    curl -X DELETE http://127.0.0.1:8102/api/books/1
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from db import connect, count_books, delete_book, get_book, insert_book, list_books, update_book

app = FastAPI(title="fastapi-lab 03 · 数据库集成", version="1.0.0")


def get_conn():
    """yield 依赖：请求级连接，结束自动关闭。"""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0)
    rating: int = Field(ge=1, le=5)
    category: str = Field(max_length=80)


class BookOut(BookIn):
    id: int


@app.get("/api/books")
def read_books(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn: Depends = Depends(get_conn),
) -> dict:
    return {
        "total": count_books(conn),
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in list_books(conn, limit, offset)],
    }


@app.get("/api/books/{book_id}", response_model=BookOut)
def read_book(book_id: int, conn: Depends = Depends(get_conn)) -> dict:
    row = get_book(conn, book_id)
    if row is None:
        raise HTTPException(status_code=404, detail="book not found")
    return dict(row)


@app.post("/api/books", status_code=201, response_model=BookOut)
def create_book(book: BookIn, conn: Depends = Depends(get_conn)) -> dict:
    new_id = insert_book(conn, book.title, book.price, book.rating, book.category)
    return {"id": new_id, **book.model_dump()}


@app.put("/api/books/{book_id}", response_model=BookOut)
def replace_book(book_id: int, book: BookIn, conn: Depends = Depends(get_conn)) -> dict:
    if not update_book(conn, book_id, book.title, book.price, book.rating, book.category):
        raise HTTPException(status_code=404, detail="book not found")
    return {"id": book_id, **book.model_dump()}


@app.delete("/api/books/{book_id}", status_code=204)
def remove_book(book_id: int, conn: Depends = Depends(get_conn)) -> None:
    if not delete_book(conn, book_id):
        raise HTTPException(status_code=404, detail="book not found")
