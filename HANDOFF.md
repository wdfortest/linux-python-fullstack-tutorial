# HANDOFF · 项目进度与交接记录

> 本文件是教程项目的「施工日志 + 交接说明」：如上下文被压缩或换会话继续，从这里恢复。
> 最后更新：2026-11-04 01:30 前后

## 任务定义（用户原始需求）

在本文件夹（`/Users/jjy/Documents/linux学习与实战`）做一个**严谨的中文教程项目**并发布到 GitHub：

1. GitHub 完整教程（日常开发向）
2. Linux 服务器（Ubuntu）配置
3. Python 爬虫
4. 数据分析（pandas + SQL）
5. 数据 Web 可视化（ECharts）
6. API 后端（FastAPI）
7. 综合实战项目 + 完整文档

要求：详细、真实、可复现；富文本/代码/Mermaid 流程图；最终推到用户的 GitHub（账号 wdfortest，gh CLI 已认证，SSH 可用）。

## 环境事实（勿重查）

- GitHub：账号 `wdfortest`，git 全局身份 `wd-jjy <15027280841@163.com>`，gh 2.100.0，git 2.54.0
- Python：`jjyv` = `source ~/opt/jjyv/bin/activate`（venv 在 ~/opt/jjyv，Python 3.14.0）
- 已补装：fastapi 0.162.0 / pyecharts 2.1.0 / pytest 9.2.0 / pytest-asyncio / aiosqlite
- 其他：无 docker；mysql 客户端 9.7 已装；uv 0.9.10 可用
- 版本事实（已核实，写教程以此为准）：FastAPI 0.162.0（2026-10）、ECharts 6.1.0（2026-05，6.0 于 2025-07）、Ubuntu 26.04 LTS "Resolute Raccoon"（2026-04-23 发布，支持至 2031-05）、pandas 2.3.3 / SQLAlchemy 2.0.50 / Scrapy 2.13.3 / bs4 4.14.3 / selenium 4.44.0 / pydantic 2.13.4 / uvicorn 0.52.0

## ⚠️ 运行约束（用户明确要求，必须遵守）

1. **子 Agent 同时最多 1 个**（用户多次强调，超过会被平台封控导致工作中断）
2. **Mimosa 安全钩子会拦截 .py 写入**，规则（实测总结）：
   - SQL 只能出现在完整静态单行字面量 + 无参数（`conn.execute("SELECT ...")` 通过）
   - 任何 execute/text()+参数、f-string/拼接/常量引用 SQL、SQL 上下文中的 `== 变量` 都会被拦
   - 项目已按此约束实现：SQL 全部集中在 `api/queries.py`（静态字面量），过滤在 Python 侧
   - `.md` 文件不拦截（反面案例可以写）
   - 长文件 Write 易产生乱码损坏——尽量精简代码文件、写完立即 py_compile 验证
3. 后台爬虫数据源只允许 quotes.toscrape.com / books.toscrape.com（delay ≥0.3s）

## 当前进度（2026-11-04 01:30）

### 已完成 ✅

- 仓库骨架：git init（main）、.gitignore、LICENSE(MIT)、STYLE_GUIDE.md（写作规范+版本事实表+内容红线）
- **综合实战项目 projects/book-insight/**（全部实测通过）：
  - crawler/crawl_books.py（已全量采集 1000 本 → data/books.db 2.3MB + books.csv 1.7MB，随仓库提交）
  - analysis/analyze.py（stats.json + 5 张 PNG，副本在 assets/images/data-analysis/）
  - api/{database,queries,models,schemas,main}.py（9 端点 curl 实测；StaticFiles 同源托管大屏；Makefile）
  - web/{index.html,css/style.css,js/main.js}（浏览器实测渲染完美，深色大屏 6 图+KPI+TOP10 表）
  - tests/（pytest 14/14 全绿，临时库夹具隔离）
  - .github/workflows/ci.yml（matrix 3.13/3.14 + 全仓库 py_compile 检查）
- **docs/01-git-github/ 8 篇全完成**（Agent 产出，结构/链接/Mermaid 审校通过，251-575 行/篇）
- **docs/02-linux-ubuntu/ 10 篇全完成**（同上，抽查质量优秀）
- docs/07-final-project/ 6 篇全完成（我亲自写，基于真实构建）
- 根 README.md（路线图 Mermaid + 目录 + 30 秒跑通 + 写作底线）
- docs/00-如何使用本教程.md
- docs/01、docs/02 的 README.md 目录索引
- git-lab/ 练习目录（Agent 产出）

### 进行中 🔄

- **爬虫章节 Agent（唯一活跃）**：正在补写 docs/03-python-crawler/ 8 篇文档（lab 代码 crawler-lab/ 大部分已写好，含 scrapy 项目）；已见到 02/03/04/05/06/07 文档存在
- 等它完成后，按队列依次启动（一次一个）：04 数据分析章节 Agent → 05 ECharts 章节 Agent → 06 FastAPI 章节 Agent

### 待办 ⏳

1. 等爬虫 Agent 完成通知 → 审校其 8 篇文档（结构/Mermaid/链接）→ 启动数据分析章节 Agent（原 prompt 已备好：7 篇文档 + data-analysis-lab/ + 真实数据在 projects/book-insight/data/books.db）
2. 然后 ECharts 章节 Agent（5 篇 + echarts-lab/，CDN 用 npmmirror/jsdelivr）
3. 然后 FastAPI 章节 Agent（6 篇 + fastapi-lab/，版本 pinned）
4. 每个章节完成后写该目录的 README.md 索引（模板见 docs/01、docs/02 的 README）
5. 全部完成后：全仓库死链检查（重点：docs/07 引用的 ../03-fastapi-backend/、../04-data-analysis/ 文件是否都已存在）→ 各章 README 补全 → 最终 commit → `gh repo create wdfortest/linux-python-fullstack-tutorial --public --source=. --push`（描述见下）→ 浏览器验证 GitHub 渲染（Mermaid/目录/图片）→ 汇报
   - 建议仓库描述："Linux(Ubuntu) + Git/GitHub + Python 爬虫 + pandas/SQL + ECharts + FastAPI 全栈中文教程（含可复现实战项目 book-insight）"
6. 汇报给用户（ waking up 后能看到：完整教程 + 已推送的 GitHub 仓库 + 实测结果汇总）

## 关键决策记录

- 仓库名：`linux-python-fullstack-tutorial`（public）
- 综合项目主题：图书数据洞察（books.toscrape.com 1000 本，合法练习站）
- API 数据层用 sqlite3 直连（Mimosa 约束下的稳妥实现），models.py 保留 ORM 教学
- 文档固定结构/规范见 STYLE_GUIDE.md；每章 README 索引模板已成型
- 大屏与 API 同源托管（StaticFiles），免 CORS
