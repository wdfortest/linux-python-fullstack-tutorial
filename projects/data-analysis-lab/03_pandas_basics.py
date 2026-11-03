#!/usr/bin/env python
"""lab 03 · pandas 入门：Series/DataFrame、查看全家桶、loc/iloc、布尔掩码、IO。

运行方式（教程环境 jjyv 虚拟环境）：

    source ~/opt/jjyv/bin/activate
    python projects/data-analysis-lab/03_pandas_basics.py

说明：数据全程使用真实图书数据 projects/book-insight/data/books.csv
（books.toscrape.com 采集的 1000 本图书），输出与教程文档一致。
所有含条件的 SQL 均使用 ? 占位符参数绑定。
"""
from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

import pandas as pd

LAB_DIR = Path(__file__).resolve().parent
CSV_PATH = LAB_DIR.parent / "book-insight" / "data" / "books.csv"
DB_PATH = LAB_DIR.parent / "book-insight" / "data" / "books.db"

pd.set_option("display.width", 120)

BANNER = "\n" + "=" * 62 + "\n  {}\n" + "=" * 62


def section(title: str) -> None:
    print(BANNER.format(title))


def main() -> None:
    # ------------------------------------------------------------------ 1
    section("1. Series 与 DataFrame：创建的 5 种常见方式")
    s = pd.Series([226, 196, 203, 179, 196], index=[1, 2, 3, 4, 5], name="book_count")
    print("[1] 列表 + 自定义索引 -> Series:")
    print(s.to_string())

    df1 = pd.DataFrame({"rating": [1, 2, 3], "count": [226, 196, 203]})
    print("\n[2] 字典 -> DataFrame:\n", df1.to_string(index=False))

    df2 = pd.DataFrame([{"title": "A Light in the Attic", "price": 51.77},
                        {"title": "Tipping the Velvet", "price": 53.74}])
    print("\n[3] 记录列表 -> DataFrame:\n", df2.to_string(index=False))

    arr = pd.DataFrame([[1, 226], [2, 196]], columns=["rating", "count"])
    print("\n[4] 二维数组 + 列名:\n", arr.to_string(index=False))

    df5 = pd.read_csv(CSV_PATH)
    print("\n[5] read_csv（本文档主线）: shape =", df5.shape)

    print("\nDataFrame 内部 = 一组共享 Index 的 Series（列）:")
    print("df5['price'] 类型:", type(df5["price"]).__name__,
          "| 内部数组:", type(df5["price"].to_numpy()).__name__)

    # ------------------------------------------------------------------ 2
    section("2. 查看全家桶：head / info / describe / value_counts")
    print(df5.head(3)[["title", "price", "rating", "category"]].to_string(index=False))
    print("\n-- info() 摘要 --")
    df5.info()
    print("\n-- describe() 数值列五数概括 --")
    print(df5[["price", "availability", "rating"]].describe().round(2).to_string())
    print("\n-- value_counts：评分分布（真实数据，近似均匀是练习站特性）--")
    print(df5["rating"].value_counts().sort_index().to_string())
    print("\n-- 分类数量 Top5 --")
    print(df5["category"].value_counts().head(5).to_string())

    # ------------------------------------------------------------------ 3
    section("3. loc / iloc：按标签还是按位置取数")
    books = df5.set_index("title")  # 用书名做行标签（教学演示；真实列名不建议长文做索引）
    print("loc[按标签] =", books.loc["A Light in the Attic", ["price", "rating"]].to_dict())
    print("iloc[按位置] =", df5.iloc[0, [3, 7]].tolist(), "（第 0 行第 3、7 列：price、rating）")

    print("\n-- 链式赋值反面演示（会触发 SettingWithCopyWarning）--")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        frag = df5[df5["category"] == "Poetry"]
        frag["price"] = 0.0  # 反面案例：链式取片段后直接赋值
    if caught:
        print("触发警告:", caught[0].category.__name__, "-", str(caught[0].message)[:60], "...")
    print("正确写法是一步到位的 .loc 掩码赋值：")
    fixed = df5.copy()
    fixed.loc[fixed["category"] == "Poetry", "price"] = 0.0
    print("正确写法执行成功且不告警；Poetry 均价变为", fixed.loc[fixed["category"] == "Poetry", "price"].mean())

    # ------------------------------------------------------------------ 4
    section("4. 布尔掩码与 query：同一件事的两种写法")
    mask = (df5["rating"] == 5) & (df5["price"] < 15)
    print("[布尔掩码] 5 星且 <15 英镑:", len(df5[mask]), "本")
    q = df5.query("rating == 5 and price < 15")
    print("[query]   5 星且 <15 英镑:", len(q), "本")
    print("两者结果一致:", df5[mask].equals(q))
    print("\n其中 3 本:")
    print(q[["title", "price", "category"]].head(3).to_string(index=False))

    # ------------------------------------------------------------------ 5
    section("5. axis 概念：0 是沿行往下算，1 是沿列横着算")
    mini = df5[["price", "availability"]].head(3)
    print(mini.to_string())
    print("sum(axis=0)（每列合计）:", mini.sum(axis=0).to_dict())
    print("sum(axis=1)（每行合计）:", mini.sum(axis=1).round(2).tolist())

    # ------------------------------------------------------------------ 6
    section("6. IO 全家桶：read_csv 关键参数 / 分块 / Excel / SQL / 写出")
    slim = pd.read_csv(CSV_PATH, usecols=["title", "price", "rating"], dtype={"rating": "int8"})
    print("[usecols+dtype] 列:", list(slim.columns), "| rating 内存类型:", slim["rating"].dtype)
    total_rows = sum(len(chunk) for chunk in pd.read_csv(CSV_PATH, chunksize=200))
    print("[chunksize=200] 分 5 块读完，总行数 =", total_rows)

    xlsx_path = LAB_DIR / "output" / "03_books_sample.xlsx"
    xlsx_path.parent.mkdir(exist_ok=True)
    df5.head(20)[["title", "price", "rating", "category"]].to_excel(xlsx_path, index=False)
    back = pd.read_excel(xlsx_path)
    print("[to_excel/read_excel] 往返一致:", back.shape == (20, 4), "->", xlsx_path.name)

    conn = sqlite3.connect(DB_PATH)
    sql_df = pd.read_sql(
        "SELECT title, price, category FROM books WHERE rating >= ? AND price <= ? LIMIT 3",
        conn,
        params=(5, 20.0),
    )
    conn.close()
    print("[read_sql 参数绑定] 5 星且 <=20 英镑的前 3 本:")
    print(sql_df.to_string(index=False))

    out_csv = LAB_DIR / "output" / "03_rating5_cheap.csv"
    df5[df5["rating"] == 5][["title", "price", "category"]].to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("[to_csv] 已写出:", out_csv.name, "| utf-8-sig 保证 Excel 打开不乱码")
    print("[to_json] 单行示例:", df5.head(1)[["title", "price"]].to_json(orient="records", force_ascii=False))


if __name__ == "__main__":
    main()
