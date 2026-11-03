# 第 06 章 · FastAPI 后端

> 6 篇 · 配套代码：`projects/fastapi-lab/`（6 个渐进式应用，全部真实运行验证）
> 实测环境：Python 3.14.0 + FastAPI 0.162.0 + Pydantic 2.13.4

从最小 API 到认证、测试、上线的完整后端能力；所有 lab 都能在本机一键复现。

## 目录

| # | 文档 | 内容一句话 | lab 与实测 |
|---|---|---|---|
| 01 | [FastAPI 入门（第一个 API）](01-FastAPI入门(第一个API).md) | 框架格局、三种输入、422 校验、async def 判定口诀 | 01_minimal（curl 全流程实测） |
| 02 | [请求与响应进阶](02-请求与响应进阶.md) | response_model 安全防线（含真实泄漏事故）、依赖注入三形态、中间件、后台任务 | 02_advanced（含反面演示端点） |
| 03 | [数据库集成](03-数据库集成(SQLAlchemy).md) | 分层架构、静态 SQL+参数绑定、CRUD 语义、SQLite→MySQL 切换 | 03_database（3 测试全绿） |
| 04 | [认证授权与安全](04-认证授权与安全(JWT-CORS).md) | Cookie-Session vs JWT、PBKDF2 哈希、OAuth2 流程、CORS、**安全清单** | 04_auth（JWT 全流程实测解码） |
| 05 | [测试与文档](05-测试与文档(pytest-OpenAPI).md) | TestClient 四要素隔离、422 当功能测、OpenAPI 契约 | 05_tests |
| 06 | [部署与生产实践](06-部署与生产实践.md) | 生产差距清单、12-factor 配置、healthz 自检、Nginx/Docker | 06_deploy |

## 学完你能做到

- 独立实现一个带校验、带文档、带认证、带测试的 REST API
- 把 API 安全清单当上线 checklist 用
- 与第 07 章实战项目（[FastAPI 后端实战](../07-final-project/03-FastAPI后端实战.md)）互相印证

## 快速跑全部 lab

```bash
source ~/opt/jjyv/bin/activate   # 或自建 venv
cd projects/fastapi-lab/01_minimal && uvicorn main:app --port 8100   # 依此类推 8101~8106
cd 03_database && python -m pytest ../05_tests/test_db_app.py -v    # 3 passed
```

← 返回 [总目录](../README.md)
