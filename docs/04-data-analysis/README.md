# 第 04 篇 · 数据分析（SQL / SQLAlchemy / pandas / matplotlib）

从数据库到图表的完整分析能力。前置：[第 03 篇 Python 爬虫](../03-python-crawler/README.md)（本章数据由它采集）；后继：[第 05 篇 ECharts 可视化](../05-echarts-visualization/)（把静态图升级为交互大屏）、[第 06 篇 FastAPI](../06-fastapi-backend/)（把查询变成服务）。

## 章节目录

| 章 | 文档 | 配套实验 | 建议时长 |
|---|---|---|---|
| 01 | [SQL 从入门到进阶（MySQL）](01-SQL从入门到进阶(MySQL).md) | `01_sql_basics.py` | 4 小时 |
| 02 | [SQLAlchemy 2.0：ORM 与数据库连接](02-SQLAlchemy2.0-ORM与数据库连接.md) | `02_sqlalchemy_orm.py` | 3.5 小时 |
| 03 | [pandas 入门（核心数据结构）](03-pandas入门(核心数据结构).md) | `03_pandas_basics.py` | 4 小时 |
| 04 | [pandas 数据清洗实战](04-pandas数据清洗实战.md) | `04_cleaning.py` | 4 小时 |
| 05 | [pandas 分组聚合与透视](05-pandas分组聚合与透视.md) | `05_groupby_pivot.py` | 4 小时 |
| 06 | [数据可视化（matplotlib）](06-数据可视化(matplotlib).md) | `06_matplotlib_charts.py` | 4 小时 |
| 07 | [实战：图书数据全流程分析](07-实战-图书数据全流程分析.md) | `07_book_insight_analysis.py` / `.ipynb` | 5 小时 |

## 数据

真实数据集随仓库提供：`projects/book-insight/data/books.db`（SQLite，1000 本图书）与同名 CSV，来自爬虫练习站 books.toscrape.com 的合规采集。全部实验代码在 `projects/data-analysis-lab/`，运行方式见其 [README](../../projects/data-analysis-lab/README.md)。

## 学习路线

```mermaid
flowchart LR
    A["01 SQL<br/>会问数据"] --> B["02 SQLAlchemy<br/>会管连接"]
    B --> C["03 pandas 入门<br/>会看数据"]
    C --> D["04 清洗<br/>会洗数据"]
    D --> E["05 聚合透视<br/>会出统计量"]
    E --> F["06 matplotlib<br/>会画图"]
    F --> G["07 全流程实战<br/>会下结论"]
```

## 本篇硬规范（与仓库 STYLE_GUIDE 一致）

1. **SQL 一律参数绑定**：SQLite `?`、pymysql `%s`、SQLAlchemy `text()` 用 `:name`；每章都有拼接反面案例警示；
2. **数字必须真实**：文档中所有运行输出与统计数字均来自 lab 脚本的真实运行，改数据请同步重跑；
3. 版本实测环境：Python 3.14.0 / pandas 2.3.3 / numpy 2.3.5 / SQLAlchemy 2.0.50 / matplotlib 3.10.7 / pymysql 1.1.2（详见 STYLE_GUIDE 版本事实表）。

## 图表资产

`assets/images/data-analysis/` 下 `1x_` 前缀的 PNG 由 lab 06/07 生成（book-insight 项目的既有图为 `01~05_*.png`，互不冲突）；想更新图片请重跑对应脚本，勿手工改图。
