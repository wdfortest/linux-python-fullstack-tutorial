#!/usr/bin/env python
"""lab 07 · 实战：图书数据全流程分析（本篇高潮综合实验）。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/07_book_insight_analysis.py

流程：SQLAlchemy 抽取（参数绑定）-> pandas 清洗 -> 分组聚合 ->
      5 张新角度图表 -> markdown 结论报告 + 终端答案摘要。

数据：projects/book-insight/data/books.db（真实采集的 1000 本图书，只读）。
输出：projects/data-analysis-lab/output/ 下的 1x_07_*.png 与 07_report.md，
      图片同步复制到 assets/images/data-analysis/ 供教程引用。
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text

LAB_DIR = Path(__file__).resolve().parent
OUT_DIR = LAB_DIR / "output"
ASSET_DIR = LAB_DIR.parents[1] / "assets" / "images" / "data-analysis"
DB_PATH = LAB_DIR.parent / "book-insight" / "data" / "books.db"

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ACCENT = "#3b82f6"
PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


def save_and_copy(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(exist_ok=True)
    for target in (OUT_DIR / name, ASSET_DIR / name):
        fig.savefig(target, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  图表已保存: {OUT_DIR / name}")


# ================================================================ 1 抽取
def extract() -> pd.DataFrame:
    section("1. 抽取：SQLAlchemy + pandas，全部参数绑定")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM books"), conn)  # 全表静态查询，无参数
        print(f"  全量抽取: {len(df)} 行")
        pricey = pd.read_sql(
            text("SELECT title, price, category FROM books WHERE price >= :p AND rating >= :r ORDER BY price DESC LIMIT 3"),
            conn,
            params={"p": 50.0, "r": 4},
        )
        print("  [带条件抽取演示] 50 英镑以上的 4 星书 Top3:")
        for row in pricey.itertuples(index=False):
            print(f"    £{row.price:>5.2f}  {row.title[:44]}")
    engine.dispose()
    return df


# ================================================================ 2 清洗
def clean(df: pd.DataFrame) -> pd.DataFrame:
    section("2. 清洗：类型 / 重复 / 缺失")
    df = df.copy()
    df["crawled_at"] = pd.to_datetime(df["crawled_at"], utc=True)
    dup_titles = int(df["title"].duplicated().sum())
    dup_list = df.loc[df["title"].duplicated(keep=False), "title"].unique().tolist()
    df = df.drop_duplicates(subset=["title"], keep="first")
    missing_desc = int(df["description"].isna().sum())
    df["description"] = df["description"].fillna("（无简介）")
    print(f"  重复书名: {dup_titles} 行（{dup_list}）-> 已去重，剩 {len(df)} 行")
    print(f"  缺失简介: {missing_desc} 行 -> 填充占位文本")
    print("  各数值列 dtype:", {c: str(t) for c, t in df[["price", "availability", "rating"]].dtypes.items()})
    return df


# ================================================================ 3 分析
def analyze(df: pd.DataFrame) -> dict:
    section("3. 聚合分析：回答五个业务问题")

    # ---- Q1 库存
    stock = df["availability"]
    low = int((stock <= 5).sum())
    low_rate = low / len(df)
    q1_low_by_cat = (
        df.assign(low=stock <= 5)
        .groupby("category").agg(n=("title", "size"), low_rate=("low", "mean"))
        .query("n >= 20").sort_values("low_rate", ascending=False)
    )
    q1 = {
        "mean": float(stock.mean()), "median": float(stock.median()),
        "low": low, "low_rate": low_rate,
        "worst": q1_low_by_cat.head(3), "best": q1_low_by_cat.tail(3).sort_values("low_rate"),
    }
    print(f"\n[Q1 库存] 均值 {q1['mean']:.2f} 本，中位数 {q1['median']:.0f} 本；")
    print(f"  低库存（<=5 本）{q1['low']} 种，占 {q1['low_rate']:.1%}")
    print("  低库存率最高的 3 个分类（样本数 >=20）:")
    print(q1["worst"].round(3).to_string())

    # ---- Q2 分类评分排名
    q2 = (
        df.groupby("category").agg(n=("title", "size"), avg_rating=("rating", "mean"),
                                   avg_price=("price", "mean"))
        .query("n >= 20").sort_values("avg_rating", ascending=False)
    )
    print(f"\n[Q2 分类评分] 参与排名的分类（样本数 >=20）共 {len(q2)} 个")
    print("  最高 3:", q2.head(3).round(2).to_dict("index"))
    print("  最低 3:", q2.tail(3).round(2).to_dict("index"))

    # ---- Q3 评分与价格
    q3 = df.groupby("rating")["price"].agg(["mean", "median", "count"]).round(2)
    spread = float(q3["mean"].max() - q3["mean"].min())
    corr_pr = float(df["price"].corr(df["rating"]))
    print(f"\n[Q3 评分 x 价格] 各档均价差最大 {spread:.2f} 英镑，皮尔逊 r = {corr_pr:.3f}")
    print(q3.to_string())

    # ---- Q4 库存与定价
    corr_ps = float(df["price"].corr(df["availability"]))
    print(f"\n[Q4 库存 x 价格] 皮尔逊 r = {corr_ps:.3f}（不存在「稀缺即高价」规律）")

    # ---- Q5 数据质量审计
    q5 = {
        "tax_all_zero": bool((df["tax"] == 0).all()),
        "reviews_all_zero": bool((df["num_reviews"] == 0).all()),
        "price_eq_excl": bool((df["price"] == df["price_excl_tax"]).all()),
        "rating_share": (df["rating"].value_counts(normalize=True).sort_index() * 100).round(1),
    }
    print("\n[Q5 数据质量审计]")
    print(f"  tax 恒为 0: {q5['tax_all_zero']} | num_reviews 恒为 0: {q5['reviews_all_zero']} "
          f"| price == price_excl_tax 恒成立: {q5['price_eq_excl']}")
    print("  评分占比(%):", q5["rating_share"].to_dict())

    return {"q1": q1, "q2": q2, "q3": q3, "spread": spread, "corr_pr": corr_pr,
            "corr_ps": corr_ps, "q5": q5, "low_by_cat": q1_low_by_cat}


# ================================================================ 4 图表
def charts(df: pd.DataFrame, res: dict) -> None:
    section("4. 五张新角度图表")

    # 图 1：库存分布直方图
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.hist(df["availability"], bins=range(0, 25), color=ACCENT, edgecolor="white")
    ax.axvline(df["availability"].median(), color="#ef4444", ls="--",
               label=f"中位数 {df['availability'].median():.0f} 本")
    ax.set_title("库存分布直方图：右偏，低库存书目集中")
    ax.set_xlabel("库存数量（本）"); ax.set_ylabel("书目数量"); ax.legend()
    ax.grid(alpha=0.3)
    save_and_copy(fig, "1x_07_stock_hist.png")

    # 图 2：分类低库存率
    low_cat = res["q1"]["worst"].head(8).sort_values("low_rate")
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.barh(low_cat.index, low_cat["low_rate"] * 100, color="#f59e0b")
    ax.set_title("低库存率（库存 <=5 的书目占比）最高的分类（样本数 >=20）")
    ax.set_xlabel("低库存率（%）")
    for i, v in enumerate(low_cat["low_rate"] * 100):
        ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    save_and_copy(fig, "1x_07_lowstock_by_category.png")

    # 图 3：分类评分排名
    q2 = res["q2"]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    plot_df = q2.sort_values("avg_rating")
    colors = ["#ef4444" if v < 2.8 else "#84cc16" if v >= 3.3 else ACCENT for v in plot_df["avg_rating"]]
    ax.barh(plot_df.index, plot_df["avg_rating"], color=colors)
    ax.axvline(df["rating"].mean(), color="#64748b", ls="--",
               label=f"全站均分 {df['rating'].mean():.2f}")
    ax.set_title("分类评分排名（样本数 >=20 的分类，共 %d 个）" % len(q2))
    ax.set_xlabel("平均评分（1~5 星）"); ax.set_xlim(0, 5)
    ax.legend(); ax.grid(axis="x", alpha=0.3)
    save_and_copy(fig, "1x_07_category_rating.png")

    # 图 4：各评分档价格箱线
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    data = [df.loc[df["rating"] == r, "price"] for r in range(1, 6)]
    ax.boxplot(data, tick_labels=[f"{r} 星" for r in range(1, 6)], showmeans=True)
    ax.set_title("各评分档价格箱线图：五档几乎同分布（r = %.3f）" % res["corr_pr"])
    ax.set_ylabel("价格（英镑）"); ax.grid(axis="y", alpha=0.3)
    save_and_copy(fig, "1x_07_price_by_rating_box.png")

    # 图 5：库存 x 价格散点
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.scatter(df["availability"], df["price"], s=14, c="#8b5cf6", alpha=0.45)
    ax.set_title("库存与定价散点：无'稀缺高价'规律（r = %.3f）" % res["corr_ps"])
    ax.set_xlabel("库存数量（本）"); ax.set_ylabel("价格（英镑）")
    ax.grid(alpha=0.3)
    save_and_copy(fig, "1x_07_stock_price_scatter.png")


# ================================================================ 5 报告
def report(df: pd.DataFrame, res: dict) -> None:
    section("5. 生成 markdown 结论报告")
    q1, q2, q3 = res["q1"], res["q2"], res["q3"]
    q5 = res["q5"]
    lines = [
        "# 图书数据全流程分析结论报告",
        "",
        f"- 数据源：books.toscrape.com 真实采集（{len(df)} 种图书，50 个分类，采集于 {df['crawled_at'].min():%Y-%m-%d}）",
        "- 分析脚本：`projects/data-analysis-lab/07_book_insight_analysis.py`（可一键复现本文全部数字与图表）",
        "",
        "## 结论",
        "",
        f"1. **库存呈右偏分布，补货压力集中在尾部**：均值 {q1['mean']:.2f} 本、中位数 {q1['median']:.0f} 本，"
        f"{q1['low']} 种书目（{q1['low_rate']:.1%}）库存不超过 5 本；"
        f"低库存率最高的大分类是 {q1['worst'].index[0]}（{q1['worst'].iloc[0]['low_rate']:.1%}）。",
        f"2. **分类评分差异有限但真实存在**（样本数 >=20 的 {len(q2)} 个分类）："
        f"最高 {q2.index[0]}（{q2.iloc[0]['avg_rating']:.2f} 星），最低 {q2.index[-1]}（{q2.iloc[-1]['avg_rating']:.2f} 星），"
        "极差约 1 星量级。",
        f"3. **价格与评分无关得到量化确认**：各评分档均价差不超过 {res['spread']:.2f} 英镑，皮尔逊 r = {res['corr_pr']:.3f}；"
        "箱线图五档几乎同分布，与 book-insight 大屏散点图的目测结论一致且更严谨。",
        f"4. **库存与定价同样无关**（r = {res['corr_ps']:.3f}）：站点没有「稀缺即高价」的定价策略。",
        "5. **数据质量**：tax 恒为 0、num_reviews 恒为 0、price 与 price_excl_tax 恒相等、"
        f"五档评分占比 {q5['rating_share'].min():.0f}%~{q5['rating_share'].max():.0f}% 近似均匀——"
        "这是练习站的人造特性，分析结论不能外推到真实图书市场。",
        "",
        "## 可信度声明",
        "",
        "- 样本量：1000 种图书，单一站点、单次快照，价格与库存均为采集时刻状态；",
        "- 分类评分排名只纳入书目数 >=20 的分类，样本数 1~19 的分类（如 Erotica 5 星但仅 1 本）不具统计意义；",
        "- 皮尔逊相关系数只衡量线性关系；本文所有「无相关」结论均在 r 与分组分布双重验证下成立；",
        "- 练习站数据由程序生成，均匀评分与零税费是站点特性而非市场规律。",
    ]
    path = OUT_DIR / "07_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已写出: {path}")


def summary(res: dict) -> None:
    section("答案摘要（对应教程正文五个业务问题）")
    q1 = res["q1"]
    print(f"Q1: 均值 {q1['mean']:.2f} / 中位数 {q1['median']:.0f}，低库存 {q1['low']} 种（{q1['low_rate']:.1%}）")
    q2 = res["q2"]
    print(f"Q2: 评分最高 {q2.index[0]} {q2.iloc[0]['avg_rating']:.2f} 星 / 最低 {q2.index[-1]} {q2.iloc[-1]['avg_rating']:.2f} 星（n>=20）")
    print(f"Q3: 各评分档均价差 <= {res['spread']:.2f} 英镑，r = {res['corr_pr']:.3f} -> 无关")
    print(f"Q4: 库存与价格 r = {res['corr_ps']:.3f} -> 无关")
    print("Q5: tax/num_reviews 恒 0、评分近似均匀 -> 练习站人造特性，结论不外推真实市场")


def main() -> None:
    df = extract()
    df = clean(df)
    res = analyze(df)
    charts(df, res)
    report(df, res)
    summary(res)


if __name__ == "__main__":
    main()
