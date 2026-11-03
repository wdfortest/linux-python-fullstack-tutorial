"""API 端点测试。运行：cd projects/book-insight && python -m pytest tests/ -v"""
from __future__ import annotations


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_summary(client):
    resp = client.get("/api/stats/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_books"] == 12
    assert data["categories"] == 2  # 最小字段插入的行 category 为 NULL，不计入
    assert 10 <= data["min_price"] <= data["avg_price"] <= data["max_price"] <= 60
    assert data["in_stock"] == 3  # 仅显式给了 availability 的三行
    assert data["out_of_stock"] == 9


def test_books_pagination(client):
    resp = client.get("/api/books?limit=5&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 12
    assert len(data["items"]) == 5
    ids = [b["id"] for b in data["items"]]
    assert ids == sorted(ids)  # 按 id 升序

    page2 = client.get("/api/books?limit=5&offset=5").json()
    assert page2["items"][0]["id"] != data["items"][0]["id"]


def test_books_filter_category_and_rating(client):
    resp = client.get("/api/books?category=Fiction&min_rating=5")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Fiction Beta"


def test_books_search(client):
    resp = client.get("/api/books?search=poetry")
    data = resp.json()
    assert data["total"] == 3  # 搜索不区分大小写


def test_books_param_validation(client):
    # limit 超出上限应返回 422 校验错误
    resp = client.get("/api/books?limit=500")
    assert resp.status_code == 422


def test_book_detail_404(client):
    resp = client.get("/api/books/99999")
    assert resp.status_code == 404


def test_book_detail_found(client):
    resp = client.get("/api/books/6")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Fiction Alpha"
    assert data["category"] == "Fiction"
    assert data["availability"] == 10


def test_ratings_distribution(client):
    resp = client.get("/api/stats/ratings")
    assert resp.status_code == 200
    dist = {d["rating"]: d["count"] for d in resp.json()}
    assert dist == {1: 2, 2: 1, 3: 2, 4: 3, 5: 4}


def test_price_histogram(client):
    resp = client.get("/api/stats/prices")
    assert resp.status_code == 200
    buckets = {b["bucket"]: b["count"] for b in resp.json()}
    assert buckets["10-20"] == 3   # 10.5 / 15.0 / 12.3
    assert buckets["40-50"] == 2   # 48.0 / 45.0
    assert buckets["50-60"] == 1   # 59.9
    assert sum(buckets.values()) == 12


def test_categories_sorted_by_count(client):
    resp = client.get("/api/stats/categories")
    data = resp.json()
    counts = [c["count"] for c in data]
    assert counts == sorted(counts, reverse=True)
    fiction = next(c for c in data if c["category"] == "Fiction")
    assert fiction["count"] == 2
    assert fiction["avg_price"] == 27.5


def test_top_rated_length(client):
    resp = client.get("/api/stats/top-rated")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    ratings = [b["rating"] for b in data]
    assert ratings == sorted(ratings, reverse=True)


def test_charts_all_bundle(client):
    resp = client.get("/api/charts/all")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("summary", "rating_distribution", "price_histogram", "categories", "top_rated", "price_rating_scatter", "availability"):
        assert key in data
    assert len(data["price_rating_scatter"]) == 6  # 隔行抽样，取一半


def test_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
