# 06.5 · 测试与文档（pytest、TestClient、OpenAPI）

> 本章配套代码：`projects/fastapi-lab/05_tests/`（3/3 通过）+ 实战项目 [book-insight/tests/](../../projects/book-insight/tests/)（14/14 通过）

## 学习目标

- 掌握 TestClient 的标准写法与依赖覆盖（dependency_overrides）做测试隔离
- 会写参数化测试与 422 校验断言
- 理解 OpenAPI 即契约：/docs 如何服务前后端并行开发

## 6.5.1 为什么 API 必须有自动化测试

手工 curl 回归一个 20 端点的服务要半小时，且容易漏；CI 上的 pytest 全绿只要几秒。本仓库两套测试的实测速度：`fastapi-lab 3 passed in 0.18s`、`book-insight 14 passed in 0.05s`。

## 6.5.2 TestClient + 临时库：标准隔离模板

`05_tests/test_db_app.py` 的完整套路（对 03 章 CRUD 应用测试）：

```python
@pytest.fixture()
def client(tmp_path: Path):
    db_file = tmp_path / "test_lab03.db"          # ① 临时库：跑完自动删
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA)

    def override_conn():                          # ② 覆盖依赖：应用根本不知道
        c = sqlite3.connect(db_file)              #    真实库的存在
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[get_conn] = override_conn
    with TestClient(app) as test_client:          # ③ with 语法触发 lifespan
        yield test_client
    app.dependency_overrides.clear()              # ④ 清覆盖，防串扰
```

四要素：**临时库 / 依赖覆盖 / with TestClient / 清理覆盖**。与实战项目 14 个测试同款模板（见 [测试与CI篇](../07-final-project/05-测试CI与部署上线.md)）。

## 6.5.3 测试用例设计（真实代码）

```python
def test_crud_full_cycle(client):
    assert client.get("/api/books").json()["total"] == 0          # 空起点
    r1 = client.post("/api/books", json={"title": "Book A", "price": 10.5, "rating": 4, "category": "Fiction"})
    assert r1.status_code == 201                                  # 201 语义
    upd = client.put(f"/api/books/{r1.json()['id']}", json={...})
    assert upd.json()["title"] == "Book A v2"
    assert client.delete(f"/api/books/{r1.json()['id']}").status_code == 204
    assert client.get(f"/api/books/{r1.json()['id']}").status_code == 404

def test_validation_422(client):
    resp = client.post("/api/books", json={"title": "", "price": -1, "rating": 9, "category": ""})
    assert resp.status_code == 422
    locs = [e["loc"][-1] for e in resp.json()["detail"]]
    assert {"title", "price", "rating"} <= set(locs)              # 三个字段都被校验捕获
```

用例设计三原则：

1. **走完整生命周期**：create → read → update → delete 一条用例串起来，状态转换最容易被回归
2. **断言精确值**：断言 `total == 2` 而不是 `> 0`；重构改坏口径时精确断言立刻报警
3. **把 422 当功能测**：校验规则是需求的一部分，`loc` 断言保证每个字段的规则都生效

实测运行：

```text
$ python -m pytest ../05_tests/test_db_app.py -v
test_crud_full_cycle PASSED
test_validation_422 PASSED
test_not_found PASSED
3 passed, 2 warnings in 0.18s
```

（warnings 是 Starlette 的 TestClient 底层迁移提示——读一下有备无患，升级前要处理。）

## 6.5.4 参数化与异步测试（速览）

```python
@pytest.mark.parametrize("limit,expect", [(1, 1), (5, 2), (100, 2)])
def test_limit_bounds(client, limit, expect):
    client.post("/api/books", json={...}); client.post("/api/books", json={...})
    assert len(client.get(f"/api/books?limit={limit}").json()["items"]) <= expect
```

异步测试（AsyncClient + pytest-asyncio）适合含真实异步 IO 的端点；本 lab 的同步路由用 TestClient 已覆盖，异步测试模板见 [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)。

覆盖率粗查：

```bash
python -m pytest ../05_tests/ --cov=03_database --cov-report=term-missing   # 需 pytest-cov
```

## 6.5.5 OpenAPI：文档即契约

FastAPI 自动从类型注解生成 OpenAPI schema（/json 端点可见原始 JSON），Swagger UI（/docs）可视化调试。三个工程价值：

1. **前后端并行**：后端把 schema 定稿 → 前端按 schema 开发 mock → 联调零歧义（第 05 章「契约先行」的落地）
2. **文档永远不过期**：文档由代码生成，代码改了文档必变
3. **可定制**：

```python
app = FastAPI(
    title="Book Insight API",
    version="1.0.0",
    description="图书数据洞察平台：爬虫采集 -> SQLite -> pandas -> FastAPI -> ECharts",
)
```

生产环境可关文档（`docs_url=None`，见 06_deploy lab 的 production 分支）。

## 常见坑与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 测试互相污染 | 共享模块级状态/同一个库文件 | 每测试临时库 + 覆盖清理（模板 6.5.2） |
| TestClient 报 lifespan 错误 | 用了裸 `TestClient(app)` | `with TestClient(app) as client:` |
| 422 断言过不了 | JSON 键拼错 | 先打印 resp.json() 看 loc |
| 覆盖了依赖但没生效 | override 的 key 不是原依赖函数对象 | 必须 `app.dependency_overrides[get_conn]`（同一函数对象） |
| CI 上测试慢 | 每次全量装依赖 | pip 缓存 + 只装测试所需（本仓库 ci.yml 做法） |

## 动手练习

1. 给 03 章应用补 `test_limit_bounds` 参数化用例（模板见上）。
2. 加一条「PUT 不存在的 id 返回 404」的反向用例。
3. 装 pytest-cov，把 03_database 的覆盖率跑到 >90%，补齐缺失行。

## 小结与自检清单

- [ ] 四要素隔离模板能默写
- [ ] 精确断言与 422 测试会写
- [ ] 能说清 OpenAPI 服务并行开发的机制
- [ ] 本地跑过 --cov 并能看懂 missing 列

## 延伸阅读

- [FastAPI: Testing](https://fastapi.tiangolo.com/zh/tutorial/testing/)
- [pytest 官方文档](https://docs.pytest.org/en/stable/)
