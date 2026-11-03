# data-analysis-lab · 数据分析篇全部实验代码

对应教程：`docs/04-data-analysis/`（第 01~07 章）。每章一个独立脚本，
在仓库根目录按下面方式运行；全部脚本在作者环境（Python 3.14.0，jjyv 虚拟环境）实测通过。

## 运行方式

```bash
source ~/opt/jjyv/bin/activate   # 教程虚拟环境，见 docs/02-linux-ubuntu/07
python projects/data-analysis-lab/01_sql_basics.py
python projects/data-analysis-lab/02_sqlalchemy_orm.py
python projects/data-analysis-lab/03_pandas_basics.py
python projects/data-analysis-lab/04_cleaning.py
python projects/data-analysis-lab/05_groupby_pivot.py
python projects/data-analysis-lab/06_matplotlib_charts.py
python projects/data-analysis-lab/07_book_insight_analysis.py
```

| 脚本 | 对应章节 | 数据 | 产出 |
|---|---|---|---|
| `01_sql_basics.py` | 第 01 章 SQL | books.db（复制副本） | 终端查询结果 |
| `02_sqlalchemy_orm.py` | 第 02 章 SQLAlchemy | books.db（复制副本） | 终端输出 |
| `03_pandas_basics.py` | 第 03 章 pandas 入门 | books.csv | `output/03_*.csv/.xlsx` |
| `04_cleaning.py` | 第 04 章 数据清洗 | 脚本构造的脏 CSV | `data/dirty_books.csv`、`output/04_cleaned_books.csv` |
| `05_groupby_pivot.py` | 第 05 章 分组聚合 | books.db | 终端输出 |
| `06_matplotlib_charts.py` | 第 06 章 可视化 | books.db | `output/1x_06_*.png`（7 张） |
| `07_book_insight_analysis.py` | 第 07 章 全流程实战 | books.db | `output/1x_07_*.png`（5 张）+ `output/07_report.md` |
| `07_book_insight_analysis.ipynb` | 第 07 章 notebook 版 | books.db | 同上，含已执行输出 |

## 数据说明

- 真实数据：`projects/book-insight/data/books.db` 与 `books.csv`
  （books.toscrape.com 采集的 1000 本图书，该站是 Scrapy 官方维护的爬虫练习站）；
- 第 04 章的 `dirty_books.csv` 是**教学构造数据**，脚本每次运行重新生成；
- 第 05 章时间序列一节的 30 天日销序列同样是脚本内构造的演示数据（真实数据只采集于同一天）。

## 安全约定（本仓库硬规范）

所有含外部数据的 SQL 一律参数绑定：sqlite3 用 `?`、SQLAlchemy `text()` 用 `:name`，
每条 SQL 都是完整静态字面量；字符串拼接 SQL 的做法禁止出现在任何真实代码中，
反面案例仅出现在教程文档的警示小节。

## 目录结构

```text
data-analysis-lab/
├── 01_sql_basics.py … 07_book_insight_analysis.py
├── 07_book_insight_analysis.ipynb
├── data/          # 运行时生成：lab01.db / lab02.db / dirty_books.csv
└── output/        # 运行时生成：CSV / Excel / PNG / 07_report.md
```

`data/` 与 `output/` 均可随时删除重跑。
