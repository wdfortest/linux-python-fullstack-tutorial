#!/usr/bin/env python
"""lab 05 · pandas 分组聚合与透视：groupby 完全指南、pivot_table/crosstab、merge、时间序列。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/05_groupby_pivot.py

说明：分组聚合部分全程使用真实图书数据 projects/book-insight/data/books.db；
时间序列一节的演示序列是脚本内构造的教学数据（真实数据只采集于同一天，
不适合演示 resample），已在输出中明确标注。
所有含条件的 SQL 均使用 ? 占位符参数绑定。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

LAB_DIR = Path(__file__).resolve().parent
DB_PATH = LAB_DIR.parent / "book-insight" / "data" / "books.db"

pd.set_option("display.width", 130)

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


def load_df() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM books", conn)  # 全表静态查询，无参数
    conn.close()
    return df


def main() -> None:
    df = load_df()
    print(f"已加载真实数据 {len(df)} 行")

    # ------------------------------------------------------------------ 1
    section("1. split-apply-combine：groupby 的三段式心智模型")
    grouped = df.groupby("category")["price"]
    print("[split] 分组对象:", type(grouped).__name__, "共", grouped.ngroups, "个组")
    print("[apply+combine] 每类均价（前 5）:")
    print(grouped.mean().round(2).head(5).to_string())

    print("\n[多函数聚合] agg 一次算多个统计量:")
    print(df.groupby("category")["price"].agg(["count", "mean", "median", "max"]).round(2).head(5).to_string())

    print("\n[命名聚合] 列名自己起，可读性最好:")
    named = df.groupby("category").agg(
        book_count=("title", "size"),
        avg_price=("price", "mean"),
        avg_rating=("rating", "mean"),
        total_stock=("availability", "sum"),
    ).round(2).sort_values("book_count", ascending=False)
    print(named.head(6).to_string())

    # ------------------------------------------------------------------ 2
    section("2. transform 与 filter：聚合结果回到行级 / 整组淘汰")
    df2 = df.copy()
    df2["cat_avg_price"] = df2.groupby("category")["price"].transform("mean").round(2)
    df2["price_vs_cat_avg"] = (df2["price"] - df2["cat_avg_price"]).round(2)
    print("[transform] 行数不变，每行带上本类均价（抽样 4 行）:")
    print(df2[["title", "category", "price", "cat_avg_price", "price_vs_cat_avg"]].sample(4, random_state=7).to_string(index=False))

    big = df.groupby("category").filter(lambda g: len(g) >= 40)
    print("\n[filter] 只保留书目数 >= 40 的分类:", big["category"].nunique(), "个分类，", len(big), "行")

    # ------------------------------------------------------------------ 3
    section("3. pivot_table 与 crosstab：把长表掰成宽表")
    top4 = df["category"].value_counts().head(4).index.tolist()
    sub = df[df["category"].isin(top4)]
    pt = sub.pivot_table(index="rating", columns="category", values="price", aggfunc="mean").round(2)
    print("[pivot_table] 行=评分 列=书目最多的 4 个分类 值=均价:")
    print(pt.to_string())

    df_low = df.assign(low_stock=df["availability"] <= 5)
    ct = pd.crosstab(df_low["rating"], df_low["low_stock"], normalize="index").round(3)
    ct.columns = ["库存>5 占比", "库存<=5 占比"]
    print("\n[crosstab 行百分比] 各评分档的低库存率:")
    print(ct.to_string())

    # ------------------------------------------------------------------ 4
    section("4. merge / join / concat：三张表怎么拼")
    stats = df.groupby("category").agg(book_count=("title", "size")).reset_index()
    meta = pd.DataFrame({
        "category": ["Poetry", "Fantasy", "Mystery"],
        "shelf": ["A-01", "B-03", "C-02"],
    })
    merged = meta.merge(stats, on="category", how="left")
    print("[merge 左连接] 备注表 x 统计表（无书的分类计数为 NaN）:")
    print(merged.to_string(index=False))
    left = pd.DataFrame({"id": [1, 2], "price": [10.0, 20.0]})
    right = pd.DataFrame({"id": [1, 3], "stock": [5, 9]})
    inner = left.merge(right, on="id", how="inner")
    outer = left.merge(right, on="id", how="outer")
    print("\n[inner vs outer] inner 只留交集 id:", inner["id"].tolist(),
          "| outer 并集 id:", outer["id"].tolist())
    stacked = pd.concat([df.head(2), df.tail(2)], axis=0)[["title", "price"]]
    print("\n[concat axis=0 纵向拼接] 2+2 行:")
    print(stacked.to_string(index=False))

    # ------------------------------------------------------------------ 5
    section("5. dt 访问器：真实采集时间能拆出什么")
    ts = pd.to_datetime(df["crawled_at"])
    print("采集时间跨度:", ts.min(), "->", ts.max(), "（共", (ts.max() - ts.min()).components.minutes, "分钟）")
    print("每分钟采集完成的书（前 5 分钟）:")
    per_min = ts.dt.floor("min").value_counts().sort_index().head(5)
    print(per_min.to_string())

    print("\n[演示数据] resample 与 rolling（30 天模拟日销序列，非真实数据）:")
    idx = pd.date_range("2026-10-01", periods=30, freq="D")
    daily = pd.Series(np.random.default_rng(42).integers(8, 20, size=30).cumsum(), index=idx, name="sales")
    weekly = daily.resample("W").sum()
    print("周汇总 resample('W'):")
    print(weekly.to_string())
    ma7 = daily.rolling(7).mean().round(1).dropna()
    print("\n7 日均值 rolling(7)（最后 3 个值）:", ma7.tail(3).tolist())


if __name__ == "__main__":
    main()
