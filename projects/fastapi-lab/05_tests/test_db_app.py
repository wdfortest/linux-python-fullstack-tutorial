"""fastapi-lab/05 测试：对 03 章 CRUD 应用做接口测试。

运行（在 fastapi-lab 根目录）：
    cd projects/fastapi-lab/03_database && python -m pytest ../05_tests/test_db_app.py -v
（测试通过 sys.path 把 03_database 加入导入路径，隔离运行不污染真实 lab03.db）
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_database"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from db import SCHEMA  # noqa: E402
from main import app, get_conn  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path):
    db_file = tmp_path / "test_lab03.db"
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    def override_conn():
        c = sqlite3.connect(db_file)
        c.row_factory = sqlite3.Row
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[get_conn] = override_conn
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_crud_full_cycle(client):
    # 1) 空列表
    data = client.get("/api/books").json()
    assert data == {"total": 0, "limit": 20, "offset": 0, "items": []}

    # 2) 创建 2 本
    r1 = client.post("/api/books", json={"title": "Book A", "price": 10.5, "rating": 4, "category": "Fiction"})
    assert r1.status_code == 201
    r2 = client.post("/api/books", json={"title": "Book B", "price": 22.0, "rating": 3, "category": "History"})
    assert r2.status_code == 201
    assert client.get("/api/books").json()["total"] == 2

    # 3) 读单个
    got = client.get(f"/api/books/{r1.json()['id']}")
    assert got.status_code == 200 and got.json()["title"] == "Book A"

    # 4) 更新
    upd = client.put(f"/api/books/{r1.json()['id']}", json={"title": "Book A v2", "price": 9.9, "rating": 5, "category": "Fiction"})
    assert upd.status_code == 200 and upd.json()["title"] == "Book A v2"

    # 5) 删除 + 404
    assert client.delete(f"/api/books/{r1.json()['id']}").status_code == 204
    assert client.get(f"/api/books/{r1.json()['id']}").status_code == 404


def test_validation_422(client):
    resp = client.post("/api/books", json={"title": "", "price": -1, "rating": 9, "category": ""})
    assert resp.status_code == 422
    locs = [e["loc"][-1] for e in resp.json()["detail"]]
    assert {"title", "price", "rating"} <= set(locs)  # 三个字段都被校验捕获


def test_not_found(client):
    assert client.get("/api/books/99999").status_code == 404
