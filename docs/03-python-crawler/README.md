# 第 03 章 · Python 爬虫

> 8 篇 · 配套代码：`projects/crawler-lab/`（全部在本地真实运行验证过，数据产物在 crawler-lab/data/）
> 建议总学习时长：约 3 周

从 HTTP 原理到工程化异步爬虫，**合规是贯穿全章的主线**：实战只用明确欢迎抓取的练习站点。

## 目录

| # | 文档 | 内容一句话 | lab 实测产物 |
|---|---|---|---|
| 01 | [HTTP 与网页结构基础](01-HTTP与网页结构基础.md) | 请求响应模型、状态码、Cookie/Session、CSS 选择器、Network 面板、robots.txt 读法 | 01_fetch_robots.py（robots.txt 标准读法与三种状态码解读） |
| 02 | [requests 爬虫实战](02-requests爬虫实战.md) | Session/超时/重试、**编码坑（真实演示）**、分页两种模式、JSON API | data/quotes.json（100 条名言） |
| 03 | [HTML 解析（BeautifulSoup 与 lxml）](03-HTML解析(BeautifulSoup与lxml).md) | 解析器对比、find/select、XPath 入门、解析失败排查 | 03_parse_bs4.py（离线解析 data/quotes_page1.html） |
| 04 | [数据存储（CSV / JSON / SQLite / MySQL）](04-数据存储(csv-json-SQLite-MySQL).md) | 四种存储选型决策树、参数绑定硬规范、去重与增量 | data/quotes.db / quotes.csv / quotes.jsonl |
| 05 | [Scrapy 框架完全指南](05-Scrapy框架完全指南.md) | 架构数据流、Pipeline 存库、ROBOTSTXT_OBEY、AutoThrottle | book_scrapy/ 项目 + data/books.db（全站） |
| 06 | [反爬应对与爬虫合规](06-反爬应对与爬虫合规.md) | 反爬手段全景、**法律红线逐条讲清**、合规自查清单、司法案例讨论 | — |
| 07 | [动态页面抓取（Selenium）](07-动态页面抓取(Selenium).md) | 何时上浏览器、显式等待、八大定位、无头模式 | 07_selenium_demo.py |
| 08 | [爬虫工程化（并发-调度-监控）](08-爬虫工程化(并发-调度-监控).md) | asyncio+httpx 异步、Semaphore 礼貌并发、断点续爬、APScheduler | data/quotes_async.json |

## 合规红线（本章立场）

- 实战代码只抓取 [quotes.toscrape.com](https://quotes.toscrape.com/) 与 [books.toscrape.com](https://books.toscrape.com/)（Scrapy 官方练习站）
- 请求间隔 ≥ 0.3s、UA 自报教育用途、robots.txt 语义按 RFC 9309 解读
- 不提供任何绕过登录/验证码/付费墙的技术；法律边界（个人信息保护法/数据安全法/刑法 285 条）在第 06 篇逐条讲清

## 与实战项目的关系

第 07 章实战项目 [book-insight](../07-final-project/00-项目总览与架构.md) 的采集模块
（[采集与存储实战](../07-final-project/01-数据采集与存储实战.md)）是本章方法论的落地：
两级抓取 + 幂等入库 + 参数绑定。

← 返回 [总目录](../../README.md)
