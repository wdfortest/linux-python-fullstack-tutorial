#!/usr/bin/env python
"""lab 04 · pandas 数据清洗实战：构造一份"故意很脏"的 CSV，走完清洗六步法。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/04_cleaning.py

说明：
- data/dirty_books.csv 由脚本生成（22 行，手工埋入全部常见脏数据模式），
  属于教学用的构造数据，非真实采集数据；
- 清洗结果写到 output/04_cleaned_books.csv，终端打印清洗前后对比。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "data"
OUT_DIR = LAB_DIR / "output"
DIRTY_CSV = DATA_DIR / "dirty_books.csv"
CLEAN_CSV = OUT_DIR / "04_cleaned_books.csv"

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


# 22 行脏数据：price 带 £ 与千分位、缺失、异常值；category 有空格与大小写变体；
# rating 有 0/9/英文单词；published 混用 4 种日期格式且含不存在日期；含重复行。
DIRTY_ROWS = [
    ("The Midnight Library", "£12.99", " Fiction ", "4", "3", "2021-03-01"),
    ("the midnight library", "£12.99", "fiction", "4", "3", "2021-03-01"),
    ("Sea of Tranquility", "14.5", "Science Fiction", "5", "8", "01/04/2022"),
    ("Piranesi", "£9.99", " FANTASY ", "four", "N/A", "March 2022"),
    ("Cloud Cuckoo Land", "", "Historical", "3", "12", "2021/9/7"),
    ("The Song of Achilles", "£11.99", "fantasy ", "0", "2", "2022-05-30"),
    ("Educated", "£13.20", "Memoir", "9", "5", "2018-02-20"),
    ("Klara and the Sun", "£14.99", "Science Fiction", "4", "", "2021-03-02"),
    ("Babel", "£16.80", " Fantasy", "5", "6", "2022-08-23"),
    ("The Lincoln Highway", "£15.49", "Historical", "", "4", "2021-10-05"),
    ("Tomorrow, and Tomorrow, and Tomorrow", "£16.99", "Fiction", "4", "N/A", "2023-01-10"),
    ("Demon Copperhead", "£199.90", "Fiction", "5", "7", "2022-10-18"),
    ("Lessons in Chemistry", "£12.00", "Historical", "4", "9", "2022-04-05"),
    ("The Cyclone", "£7.25", "poetry", "3", "1", "2020-11-11"),
    ("It Was an Awful Sound", "£10.10", " Poetry ", "2", "", "2023-02-14"),
    ("Starter Villain", "£14.40", "Science Fiction", "4", "11", "2023-09-19"),
    ("", "£8.00", "Fiction", "2", "3", "2021-06-01"),
    ("The Bee Sting", "£17.99", "Fiction", "five", "2", "2023-08-15"),
    ("Weyward", "£13.75", "Historical", "3", "5", "2023-03-02"),
    ("The Atlas Six (Collector's Edition)", "£1,299.00", " Fantasy", "5", "2", "2020-09-01"),
    ("In Memoriam", "£15.00", "Historical", "4", "6", "2022-02-30"),
    ("The Midnight Library", "£12.99", " Fiction ", "4", "3", "2021-03-01"),
]


def make_dirty_csv() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    import csv

    with DIRTY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "price", "category", "rating", "stock", "published"])
        writer.writerows(DIRTY_ROWS)  # csv.writer 自动给含逗号的字段加引号
    print(f"已生成脏数据: {DIRTY_CSV}（{len(DIRTY_ROWS)} 行）")


def main() -> None:
    make_dirty_csv()

    # ---------------------------------------------------------- 步骤 1
    section("步骤 1 · 读取与体检：先搞清楚数据长什么样")
    df = pd.read_csv(DIRTY_CSV)
    print("shape:", df.shape)
    print("\n各列推断类型:\n", df.dtypes.to_string())
    print("\n缺失统计（read_csv 默认把空串、N/A 读成 NaN）:\n", df.isna().sum().to_string())
    print("\ncategory 原始取值（大小写与空格变体）:", sorted(df["category"].dropna().unique()))

    # ---------------------------------------------------------- 步骤 2
    section("步骤 2 · 字符串标准化：strip 去空格、统一大小写")
    df["title"] = df["title"].str.strip()
    df["category"] = df["category"].str.strip().str.title()
    print("标准化后 category 取值:", sorted(df["category"].dropna().unique()))

    # ---------------------------------------------------------- 步骤 3
    section("步骤 3 · 类型转换：to_numeric / to_datetime")
    df["price"] = pd.to_numeric(
        df["price"].astype("string").str.replace("£", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce",
    )
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce")
    df["published"] = pd.to_datetime(df["published"], format="mixed", dayfirst=True, errors="coerce")
    print(df[["price", "rating", "stock", "published"]].dtypes.to_string())
    print("\n转换失败（coerce 成 NaN/NaT）统计:\n",
          df[["price", "rating", "stock", "published"]].isna().sum().to_string())
    bad_dates = df.loc[df["published"].isna(), "title"]
    print("\n无效日期示例:", bad_dates.tolist(), "（2022-02-30 不存在 -> NaT）")

    # ---------------------------------------------------------- 步骤 4
    section("步骤 4 · 缺失值：先定位，再按业务决定删还是补")
    print("全空行数:", int(df.isna().all(axis=1).sum()))
    df = df.dropna(subset=["title"])  # 标题都没有的行无法识别，删
    print("删除无标题行后 shape:", df.shape)
    price_missing = int(df["price"].isna().sum())
    price_median = df["price"].median()
    df["price"] = df["price"].fillna(price_median)
    print(f"price 缺失 {price_missing} 处，用中位数 {price_median} 补上")
    # ⚠️ 数据泄漏提醒：如果是建模场景，填充用的统计量只能来自训练集，
    #    且要在 train/test 划分之后分别计算；本例是纯描述统计，才允许全集中位数。
    df["stock"] = df["stock"].fillna(0).astype(int)  # 库存未知按 0 处理（宁缺勿多订）
    print("rating 缺失留给步骤 6 一并处理（无效值也会变 NaN）")

    # ---------------------------------------------------------- 步骤 5
    section("步骤 5 · 重复值：duplicated 定位，drop_duplicates 去重")
    df["title_norm"] = df["title"].str.lower()
    dup_mask = df.duplicated(subset=["title_norm"])
    print("检测到的重复行:", int(dup_mask.sum()), "->", df.loc[dup_mask, "title"].tolist())
    df = df.drop_duplicates(subset=["title_norm"], keep="first").drop(columns=["title_norm"])
    print("去重后 shape:", df.shape)

    # ---------------------------------------------------------- 步骤 6
    section("步骤 6 · 异常值：业务规则 + IQR / Z 分数")
    df["rating"] = df["rating"].where(df["rating"].between(1, 5))  # 0 和 9 视为无效
    print("无效评分（不在 1~5）已置 NaN，当前 rating 缺失行数:", int(df["rating"].isna().sum()))
    df = df.dropna(subset=["rating"])
    df["rating"] = df["rating"].astype(int)

    q1, q3 = df["price"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    print(f"IQR 法：Q1={q1:.2f}, Q3={q3:.2f}, 正常区间 [{lo:.2f}, {hi:.2f}]")
    outliers = df[(df["price"] < lo) | (df["price"] > hi)]
    print("IQR 判定异常:", outliers[["title", "price"]].to_string(index=False))
    z = (df["price"] - df["price"].mean()) / df["price"].std()
    print("Z 分数法 |z|>3 的行数:", int((z.abs() > 3).sum()))
    print("注意：7.25 英镑的《The Cyclone》其实是正常低价书——小样本上 IQR 会误伤，")
    print("      真实业务要先核实再决定删或改；本例为演示清洗流程照删。")
    df = df.drop(outliers.index)
    print("删除异常价格后 shape:", df.shape)

    df["category"] = df["category"].astype("category")
    print("\ncategory 改为 category dtype 后内存:",
          f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    # ---------------------------------------------------------- 对比
    section("清洗前 vs 清洗后")
    print(f"行数: {len(DIRTY_ROWS)} -> {len(df)}"
          f"（删 1 无标题 + 2 重复 + 5 无效评分 + 3 异常价格）")
    print("price 列: 字符串带 £/千分位 -> float64，无缺失")
    print("rating: 含 0/9/英文单词 -> 1~5 的 int")
    print("category: 大小写空格混杂 -> 规范化 + category dtype，取值",
          sorted(df["category"].unique()))
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8-sig")
    print("清洗结果已写出:", CLEAN_CSV)


if __name__ == "__main__":
    main()
