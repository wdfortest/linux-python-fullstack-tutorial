#!/usr/bin/env python
"""book-insight 数据分析模块。

从 data/books.db 读取 1000 本图书数据，用 pandas 完成聚合分析：
1. 输出 data/stats.json —— 前端大屏与 API 共用的聚合结果
2. 输出 analysis/output/charts/*.png —— matplotlib 静态图表（供教程引用）
3. 终端打印结论摘要

用法：cd projects/book-insight && python analysis/analyze.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

matplotlib.use("Agg")
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Arial Unicode MS", "Noto Sans CJK SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "books.db"
OUT_DIR = Path(__file__).resolve().parent / "output"
CHART_DIR = OUT_DIR / "charts"
STATS_PATH = PROJECT_DIR / "data" / "stats.json"

ACCENT = "#3b82f6"
PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"]


def load_df() -> pd.DataFrame:
    """SQLite -> DataFrame。read_sql 走 SQLAlchemy/DBAPI 参数绑定机制。"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    return df


def save_chart(fig: plt.Figure, name: str) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  图表已保存: {path}")


def chart_rating_dist(rating_counts: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar([f"{r} 星" for r in rating_counts.index], rating_counts.values, color=ACCENT)
    ax.set_title("图书评分分布（共 %d 本）" % int(rating_counts.sum()))
    ax.set_xlabel("评分"); ax.set_ylabel("数量")
    for i, v in enumerate(rating_counts.values):
        ax.text(i, v + 3, str(v), ha="center", fontsize=9)
    save_chart(fig, "01_rating_dist.png")


def chart_price_hist(prices: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(prices, bins=20, color=ACCENT, edgecolor="white")
    ax.axvline(prices.mean(), color="#ef4444", ls="--", label="均价 %.2f" % prices.mean())
    ax.set_title("图书价格分布（英镑）"); ax.set_xlabel("价格"); ax.set_ylabel("数量"); ax.legend()
    save_chart(fig, "02_price_hist.png")


def chart_category_top(top: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["category"][::-1], top["avg_price"][::-1], color=PALETTE[0])
    ax.set_title("书目最多的 10 个分类：平均价格")
    ax.set_xlabel("平均价格（英镑）")
    save_chart(fig, "03_category_top.png")


def chart_price_vs_rating(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = df["rating"].map({1: "#ef4444", 2: "#f59e0b", 3: "#facc15", 4: "#84cc16", 5: "#22c55e"})
    ax.scatter(df["price"], df["rating"], s=14, c=colors, alpha=0.55)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_title("价格与评分关系散点"); ax.set_xlabel("价格（英镑）"); ax.set_ylabel("评分")
    save_chart(fig, "04_price_vs_rating.png")


def chart_availability(avail_counts: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.pie(avail_counts.values, labels=avail_counts.index, autopct="%1.1f%%",
           colors=[PALETTE[1], PALETTE[3]], startangle=90)
    ax.set_title("在售状态占比")
    save_chart(fig, "05_availability.png")


def build_stats(df: pd.DataFrame) -> dict:
    """全部聚合计算，输出可 JSON 化的 dict。"""
    rating_counts = df["rating"].value_counts().sort_index()
    hist_edges = list(range(0, 70, 10))
    hist_labels = ["%d-%d" % (hist_edges[i], hist_edges[i + 1]) for i in range(len(hist_edges) - 1)]
    price_bucket = pd.cut(df["price"], bins=hist_edges + [1000], labels=hist_labels + ["60+"], right=False)
    price_counts = price_bucket.value_counts().reindex(hist_labels + ["60+"]).fillna(0)

    by_cat = (df.groupby("category")
                .agg(count=("title", "size"), avg_price=("price", "mean"),
                     avg_rating=("rating", "mean"), total_stock=("availability", "sum"))
                .round(2).sort_values("count", ascending=False))

    summary = {
        "total_books": int(len(df)),
        "categories": int(df["category"].nunique()),
        "avg_price": round(float(df["price"].mean()), 2),
        "median_price": round(float(df["price"].median()), 2),
        "max_price": round(float(df["price"].max()), 2),
        "min_price": round(float(df["price"].min()), 2),
        "avg_rating": round(float(df["rating"].mean()), 2),
        "in_stock": int((df["availability"] > 0).sum()),
        "out_of_stock": int((df["availability"] == 0).sum()),
        "total_reviews": int(df["num_reviews"].sum()),
        "avg_stock": round(float(df["availability"].mean()), 1),
    }
    stats = {
        "summary": summary,
        "rating_distribution": [{"rating": int(r), "count": int(c)} for r, c in rating_counts.items()],
        "price_histogram": [{"bucket": b, "count": int(c)} for b, c in price_counts.items()],
        "categories": [{"category": r.category, "count": int(r.count), "avg_price": float(r.avg_price),
                        "avg_rating": float(r.avg_rating), "total_stock": int(r.total_stock)}
                       for r in by_cat.reset_index().itertuples()],
        "top_rated": (df.sort_values(["rating", "num_reviews", "availability"], ascending=False)
                      [["title", "price", "rating", "category"]].head(10).to_dict("records")),
        "price_rating_scatter": df[["price", "rating"]].sample(frac=0.5, random_state=42).round(2).to_dict("records"),
        "availability": [
            {"name": "在售", "value": summary["in_stock"]},
            {"name": "缺货", "value": summary["out_of_stock"]},
        ],
    }
    return stats


def print_report(stats: dict, by_cat_head: pd.DataFrame) -> None:
    s = stats["summary"]
    print("\n========== 图书数据洞察报告 ==========")
    print(f"总书目: {s['total_books']}    分类数: {s['categories']}")
    print(f"均价: £{s['avg_price']}（中位数 £{s['median_price']}，区间 £{s['min_price']}~£{s['max_price']}）")
    print(f"平均评分: {s['avg_rating']} 星    在售: {s['in_stock']} / 缺货: {s['out_of_stock']}")
    print("\n书目最多的 5 个分类:")
    print(by_cat_head.to_string(index=False))
    print("\n评分 TOP5:")
    for b in stats["top_rated"][:5]:
        print(f"  [{b['rating']}星 £{b['price']}] {b['title']} ({b['category']})")
    print("======================================\n")


def main() -> None:
    df = load_df()
    print(f"已加载 {len(df)} 行数据")

    stats = build_stats(df)
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"聚合统计已写入: {STATS_PATH}")

    rating_counts = df["rating"].value_counts().sort_index()
    by_cat = pd.DataFrame(stats["categories"])
    chart_rating_dist(rating_counts)
    chart_price_hist(df["price"])
    chart_category_top(by_cat.head(10))
    chart_price_vs_rating(df)
    chart_availability(pd.Series({d["name"]: d["value"] for d in stats["availability"]}))
    print_report(stats, by_cat.head(5)[["category", "count", "avg_price", "avg_rating"]])


if __name__ == "__main__":
    main()
