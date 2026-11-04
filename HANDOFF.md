# HANDOFF · 项目完成记录（2026-11-04 02:00 收官）

> 本文件是教程项目的「施工日志 + 交接说明」。**项目已全部完成并发布**：
> **https://github.com/wdfortest/linux-python-fullstack-tutorial**（CI 全绿）
> 本地仓库：/Users/jjy/Documents/linux学习与实战（7 个 commit，全部已推送；2026-11-04 复核验收，见文末验收记录）

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

## 最终成果盘点

- **7 个章节全部完成**（55 篇文档，约 16,000 行 markdown）：00 使用说明、01 Git/GitHub(8)、02 Ubuntu(10)、03 爬虫(8)、04 数据分析(7+索引)、05 ECharts(5+索引)、06 FastAPI(6+索引)、07 实战(6)
- **综合实战项目 book-insight**：爬虫（1000 本真实数据采集）→ SQLite → pandas 分析 → FastAPI（9 端点）→ ECharts 大屏，pytest 14/14，CI 5/5 全绿
- **全部 lab 实测**：crawler-lab（scrapy 全站 1000 本、Selenium 真实跑通、异步 2.9s）、data-analysis-lab（7 脚本复跑、12 图）、fastapi-lab（6 应用）、echarts-lab（浏览器渲染验证）、git-lab（3 脚本）
- 质量机制：STYLE_GUIDE 统一规范、固定文档结构、全仓库死链 0、Mermaid 语法检查通过、版本事实表防过期断言

## 收尾待办（可选优化，均不影响可用性）

- 无必须项。可选：给仓库加 topics 标签、开 Issues 模板、补 CHANGELOG



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

### 验收记录（2026-11-04 复核，全部通过）

- 文档盘点：docs/ 共 57 个 markdown（55 篇正文 + 章节索引），00–07 各章齐全
- 死链复查：全仓库 222 个相对链接，修复 2 个真死链（docs/07 引用的 `../03-fastapi-backend/` 应为 `../06-fastapi-backend/`）；文件名含配平括号的链接为 CommonMark 合法写法，GitHub 正常渲染，非死链
- 代码验证：projects 全部 .py 通过 py_compile；book-insight pytest 14/14 通过
- 数据一致性：data/stats.json 与 README 宣称一致（1000 本 / 50 分类 / £35.07 / 2.92★ / 在售 1000）
- 仓库卫生：清除了被误跟踪的 projects/book-insight/.mimosa 与 crawler/.mimosa 共 26 个本地工具状态文件（gitignore 规则 `.mimosa/` 匹配任意层级，之后不会再被跟踪）
- CI：GitHub Actions 5/5 全绿；本地与 origin/main 同步

## 关键决策记录

- 仓库名：`linux-python-fullstack-tutorial`（public）
- 综合项目主题：图书数据洞察（books.toscrape.com 1000 本，合法练习站）
- API 数据层用 sqlite3 直连（Mimosa 约束下的稳妥实现），models.py 保留 ORM 教学
- 文档固定结构/规范见 STYLE_GUIDE.md；每章 README 索引模板已成型
- 大屏与 API 同源托管（StaticFiles），免 CORS
