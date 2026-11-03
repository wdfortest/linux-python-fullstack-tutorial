#!/usr/bin/env python
"""book-insight 数据采集：抓取 books.toscrape.com（Scrapy 官方练习站，明确欢迎爬取）。

用法：python crawl_books.py [--limit N] [--delay 0.3] [-v]
产出：data/books.db（SQLite 表 books）+ data/books.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = urljoin(BASE_URL, "catalogue/")
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "books.db"
CSV_PATH = DATA_DIR / "books.csv"

# 该站响应头不含 charset，requests 会误判编码导致乱码（教学经典坑），该站实为 UTF-8
FORCE_ENCODING = "utf-8"
REQUEST_HEADERS = {"User-Agent": "book-insight-tutorial-crawler/1.0 (educational)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PRICE_RE = re.compile(r"[\d.]+")

logger = logging.getLogger("crawl_books")


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc TEXT UNIQUE,
            title TEXT NOT NULL,
            price REAL,
            price_excl_tax REAL,
            tax REAL,
            availability INTEGER,
            rating INTEGER,
            category TEXT,
            num_reviews INTEGER,
            description TEXT,
            image_url TEXT,
            detail_url TEXT UNIQUE,
            crawled_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
        CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating);
        """
    )
    return conn


def fetch(session: requests.Session, url: str, *, max_retries: int = 3) -> str:
    """带重试与线性退避的 GET。"""
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            resp.encoding = FORCE_ENCODING
            return resp.text
        except requests.RequestException as exc:
            if attempt == max_retries:
                raise
            time.sleep(attempt * 2)
    raise RuntimeError("unreachable")


def parse_catalogue_page(html: str) -> list[dict]:
    """目录页 -> 书名/价格/评分/详情链接（每页 20 本）。"""
    soup = BeautifulSoup(html, "lxml")
    books = []
    for article in soup.select("article.product_pod"):
        a = article.select_one("h3 a")
        price_text = article.select_one("p.price_color").get_text(strip=True)
        rating_class = article.select_one("p.star-rating")["class"]
        books.append(
            {
                "title": a["title"].strip(),
                "price": float(PRICE_RE.search(price_text).group()),
                "rating": RATING_MAP.get(rating_class[-1], 0),
                "detail_url": urljoin(CATALOGUE_URL, a["href"]),
            }
        )
    return books


def parse_detail_page(html: str, detail_url: str) -> dict:
    """详情页 -> UPC/税前价/税率/库存/评论数/分类/简介/封面。"""
    soup = BeautifulSoup(html, "lxml")
    info: dict[str, str] = {}
    for row in soup.select("table.table-striped tr"):
        th, td = row.find("th"), row.find("td")
        if th and td:
            info[th.get_text(strip=True)] = td.get_text(strip=True)

    m = re.search(r"\((\d+) available\)", info.get("Availability", ""))
    breadcrumb = soup.select("ul.breadcrumb li a")
    desc_p = soup.select_one("#product_description ~ p")
    img = soup.select_one("div.item.active img")
    price_excl = info.get("Price (excl. tax)")
    tax_text = info.get("Tax")
    reviews = info.get("Number of reviews")
    return {
        "upc": info.get("UPC"),
        "price_excl_tax": float(PRICE_RE.search(price_excl).group()) if price_excl else None,
        "tax": float(PRICE_RE.search(tax_text).group()) if tax_text else None,
        "availability": int(m.group(1)) if m else 0,
        "num_reviews": int(reviews) if reviews else 0,
        "category": breadcrumb[-1].get_text(strip=True) if len(breadcrumb) >= 3 else None,
        "description": desc_p.get_text(strip=True) if desc_p else None,
        "image_url": urljoin(BASE_URL, img["src"]) if img else None,
        "detail_url": detail_url,
    }


def insert_book(conn: sqlite3.Connection, book: dict) -> None:
    """入库。安全规范：单行静态 SQL + ? 参数绑定，字段先解包为局部变量。"""
    title = book["title"]
    price = book["price"]
    rating = book["rating"]
    detail_url = book["detail_url"]
    upc = book.get("upc")
    price_excl_tax = book.get("price_excl_tax")
    tax = book.get("tax")
    availability = book.get("availability")
    num_reviews = book.get("num_reviews")
    category = book.get("category")
    description = book.get("description")
    image_url = book.get("image_url")
    crawled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute("INSERT OR REPLACE INTO books (title, price, rating, detail_url, upc, price_excl_tax, tax, availability, num_reviews, category, description, image_url, crawled_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (title, price, rating, detail_url, upc, price_excl_tax, tax, availability, num_reviews, category, description, image_url, crawled_at))


def export_csv(conn: sqlite3.Connection, csv_path: Path) -> None:
    rows = conn.execute("SELECT * FROM books ORDER BY id").fetchall()
    cur = conn.execute("SELECT * FROM books LIMIT 1")
    cols = [d[0] for d in cur.description]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    logger.info("CSV 导出 %d 行", len(rows))


def crawl(limit: int | None, delay: float) -> None:
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    conn = init_db(DB_PATH)

    # 1) 目录分页：沿 li.next 翻页
    catalogue_url = urljoin(CATALOGUE_URL, "page-1.html")
    items: list[dict] = []
    while catalogue_url:
        html = fetch(session, catalogue_url)
        page_items = parse_catalogue_page(html)
        items.extend(page_items)
        logger.info("目录累计 %d 本", len(items))
        if limit and len(items) >= limit:
            items = items[:limit]
            break
        next_link = BeautifulSoup(html, "lxml").select_one("li.next a")
        catalogue_url = urljoin(catalogue_url, next_link["href"]) if next_link else None
        time.sleep(delay)

    logger.info("目录完成，共 %d 本，开始详情页", len(items))

    # 2) 详情页逐本入库，每 20 本提交一次
    failed = 0
    total_items = len(items)
    for i, item in enumerate(items, 1):
        try:
            item.update(parse_detail_page(fetch(session, item["detail_url"]), item["detail_url"]))
        except requests.RequestException as exc:
            failed += 1
            logger.error("详情失败 %s: %s", item["detail_url"], exc)
        insert_book(conn, item)
        if i % 20 == 0 or i == total_items:
            conn.commit()
            logger.info("进度 %d/%d 失败=%d", i, total_items, failed)
        time.sleep(delay)

    conn.commit()
    export_csv(conn, CSV_PATH)
    total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    conn.close()
    logger.info("完成：库内 %d 本", total)


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取 books.toscrape.com 图书数据")
    parser.add_argument("--limit", type=int, default=None, help="最多抓多少本")
    parser.add_argument("--delay", type=float, default=0.3, help="请求间隔秒")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        crawl(args.limit, args.delay)
    except requests.RequestException as exc:
        logger.error("采集失败：%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
