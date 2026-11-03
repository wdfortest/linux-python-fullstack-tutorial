#!/usr/bin/env python
"""lab 06 · matplotlib 六种基础图表 + 子图组合，全部用真实图书数据。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/06_matplotlib_charts.py

输出：projects/data-analysis-lab/output/1x_06_*.png，
并自动复制一份到 assets/images/data-analysis/ 供教程文档引用。

说明：中文显示按 macOS（PingFang SC）与 Ubuntu（Noto Sans CJK SC）双方案配置。
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

LAB_DIR = Path(__file__).resolve().parent
DB_PATH = LAB_DIR.parent / "book-insight" / "data" / "books.db"
OUT_DIR = LAB_DIR / "output"
ASSET_DIR = LAB_DIR.parents[1] / "assets" / "images" / "data-analysis"

# 中文字体：macOS 用 PingFang SC；Ubuntu 需先 sudo apt install fonts-noto-cjk
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ACCENT = "#3b82f6"
PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"]


def save_and_copy(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(exist_ok=True)
    for target in (OUT_DIR / name, ASSET_DIR / name):
        fig.savefig(target, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"图表已保存: {OUT_DIR / name}")


def load_df() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM books", conn)  # 全表静态查询，无参数
    conn.close()
    return df


def main() -> None:
    df = load_df()
    print(f"已加载真实数据 {len(df)} 行")

    # ------------------------------------------------------------- 折线图
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ts = pd.to_datetime(df["crawled_at"]).sort_values()
    ax.plot(ts, range(1, len(ts) + 1), color=ACCENT, lw=2)
    ax.set_title("爬虫采集进度累积曲线（books.toscrape.com，1000 本）")
    ax.set_xlabel("采集时间"); ax.set_ylabel("累计完成书目")
    ax.grid(alpha=0.3)
    save_and_copy(fig, "1x_06_line_crawl_progress.png")

    # ------------------------------------------------------------- 柱状图
    fig, ax = plt.subplots(figsize=(8, 4.4))
    top10 = df["category"].value_counts().head(10)
    ax.bar(top10.index, top10.values, color=ACCENT)
    ax.set_title("书目数量最多的 10 个分类")
    ax.set_ylabel("书目数量")
    ax.tick_params(axis="x", rotation=40)
    for i, v in enumerate(top10.values):
        ax.text(i, v + 2, str(v), ha="center", fontsize=9)
    plt.setp(ax.get_xticklabels(), ha="right")
    save_and_copy(fig, "1x_06_bar_category_count.png")

    # ------------------------------------------------------------- 饼图
    fig, ax = plt.subplots(figsize=(6, 4.6))
    rating_counts = df["rating"].value_counts().sort_index()
    ax.pie(rating_counts.values, labels=[f"{r} 星" for r in rating_counts.index],
           autopct="%1.1f%%", colors=PALETTE[:5], startangle=90,
           wedgeprops={"edgecolor": "white"})
    ax.set_title("评分占比（各档近似均匀是练习站特性）")
    save_and_copy(fig, "1x_06_pie_rating.png")

    # ------------------------------------------------------------- 散点图
    fig, ax = plt.subplots(figsize=(7, 4.5))
    r = df["price"].corr(df["availability"])
    ax.scatter(df["price"], df["availability"], s=16, c=ACCENT, alpha=0.45)
    ax.set_title(f"价格与库存散点（皮尔逊 r = {r:.3f}，几乎不相关）")
    ax.set_xlabel("价格（英镑）"); ax.set_ylabel("库存数量")
    ax.grid(alpha=0.3)
    save_and_copy(fig, "1x_06_scatter_price_stock.png")

    # ------------------------------------------------------------- 直方图
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.hist(df["price"], bins=20, color=ACCENT, edgecolor="white")
    ax.axvline(df["price"].mean(), color="#ef4444", ls="--",
               label=f"均价 {df['price'].mean():.2f} 英镑")
    ax.axvline(df["price"].median(), color="#22c55e", ls=":",
               label=f"中位数 {df['price'].median():.2f} 英镑")
    ax.set_title("价格分布直方图"); ax.set_xlabel("价格（英镑）"); ax.set_ylabel("书目数量")
    ax.legend(); ax.grid(alpha=0.3)
    save_and_copy(fig, "1x_06_hist_price.png")

    # ------------------------------------------------------------- 箱线图
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    data = [df.loc[df["rating"] == r, "price"] for r in range(1, 6)]
    ax.boxplot(data, tick_labels=[f"{r} 星" for r in range(1, 6)], showmeans=True)
    ax.set_title("各评分档的价格箱线图（中位线几乎齐平 -> 价格与评分无关）")
    ax.set_ylabel("价格（英镑）"); ax.grid(axis="y", alpha=0.3)
    save_and_copy(fig, "1x_06_box_price_by_rating.png")

    # ------------------------------------------------------------- 2x2 子图
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    fig.suptitle("图书数据四视图（2x2 子图组合）", fontsize=14)

    axes[0, 0].hist(df["price"], bins=20, color=ACCENT, edgecolor="white")
    axes[0, 0].set_title("价格分布")

    top5 = df["category"].value_counts().head(5)
    axes[0, 1].barh(top5.index[::-1], top5.values[::-1], color=PALETTE[1])
    axes[0, 1].set_title("书目最多 5 个分类")

    axes[1, 0].boxplot(data, tick_labels=[f"{r}" for r in range(1, 6)], showmeans=True)
    axes[1, 0].set_title("各评分档价格")

    axes[1, 1].scatter(df["price"], df["availability"], s=12, c=PALETTE[3], alpha=0.45)
    axes[1, 1].set_title("价格 x 库存")

    for ax in axes.flat:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    save_and_copy(fig, "1x_06_subplots_overview.png")

    print(f"\n7 张图已同步复制到: {ASSET_DIR}")


if __name__ == "__main__":
    main()
