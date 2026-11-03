# 06.1 · FastAPI 入门：第一个 API

> 本章配套代码：`projects/fastapi-lab/01_minimal/`
> 运行：`cd projects/fastapi-lab/01_minimal && uvicorn main:app --port 8100 --reload`
> 实测环境：Python 3.14.0 + FastAPI 0.162.0 + uvicorn 0.52.0

## 学习目标

- 说清 Python Web 框架格局与 FastAPI 的定位
- 用最小代码写出带校验、带文档的 API 并理解每个部分
- 分清路径参数 / 查询参数 / 请求体三种输入
- 知道 `async def` 与普通 `def` 该怎么选（新手第一困惑）

## 6.1.1 Web 后端职责与框架格局

Web 后端做的事：**接收 HTTP 请求 → 校验 → 执行业务 → 返回响应**。Python 主流框架定位：

| 框架 | 定位 | 适合 | 不适合 |
|---|---|---|---|
| **FastAPI** | 现代 API 框架（ASGI） | REST API、微服务、数据产品后端 | 传统模板渲染大站 |
| Flask | 微框架（WSGI） | 小工具、学习 Web 原理 | 原生异步/自动文档 |
| Django | 全家桶（ORM/后台/认证） | 内容型网站、快速全功能站点 | 轻量 API（偏重） |

FastAPI 三个杀手锏：**基于类型注解的自动校验**（Pydantic）、**自动交互式文档**（OpenAPI/Swagger）、**原生异步**。

两个基础概念：

- **ASGI vs WSGI**：WSGI 是同步时代的网关协议（Flask/Django 老栈）；ASGI 支持异步与 WebSocket（uvicorn/Daphne 是 ASGI 服务器）
- **uvicorn 的角色**：FastAPI 只是「应用」，真正监听端口、解析 HTTP 的是 uvicorn 这样的 ASGI 服务器

## 6.1.2 最小应用与三种输入

完整代码见 `01_minimal/main.py`（约 60 行），三种输入全部覆盖：

```python
class BookIn(BaseModel):                    # ③ 请求体模型：字段即校验
    title: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0, le=1000)
    rating: int = Field(ge=1, le=5)

@app.get("/books/{book_id}")                # ① 路径参数
def get_book(
    book_id: int = Path(ge=1),              # 类型自动转换 + 校验
    fields: str = Query("title,price", pattern="^[a-z,]+$"),   # ② 查询参数
) -> dict:
    if book_id not in FAKE_BOOKS:
        raise HTTPException(status_code=404, detail="book not found")
    wanted = set(fields.split(","))
    return {k: v for k, v in FAKE_BOOKS[book_id].items() if k in wanted}

@app.post("/books", status_code=201)
def create_book(book: BookIn) -> dict:      # ③ 请求体：Pydantic 自动校验
    new_id = max(FAKE_BOOKS) + 1
    FAKE_BOOKS[new_id] = book.model_dump()
    return {"id": new_id, **FAKE_BOOKS[new_id]}
```

## 6.1.3 真实运行记录

```text
$ curl -s http://127.0.0.1:8100/
{"message":"hello, FastAPI","docs":"/docs"}

$ curl -s "http://127.0.0.1:8100/books/3?fields=title,price"
{"title":"Sapiens: A Brief History","price":54.23}

$ curl -s -X POST http://127.0.0.1:8100/books -H "Content-Type: application/json" \
    -d '{"title": "示例书", "price": 42.0, "rating": 5}'
{"id":4,"title":"示例书","price":42.0,"rating":5}

$ curl -s http://127.0.0.1:8100/books/99 -w " [%{http_code}]"
{"detail":"book not found"} [404]

$ curl -s -X POST .../books -d '{"title": "", ...}' -w " [%{http_code}]"
{"detail":[{"type":"string_too_short","loc":["body","title"],
 "msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]} [422]
```

**422 是你的免费质检员**：`loc` 告诉你哪个字段错了、`type` 告诉你错因。前端传错参数时，看 422 响应就能定位，不用翻服务器日志。

浏览器打开 `http://127.0.0.1:8100/docs`：Swagger UI 里可以直接点 Try it out 调试每个端点——这就是「文档即产品」。

## 6.1.4 async def 还是 def？（新手第一困惑）

```python
@app.get("/a")
async def endpoint_a():
    await some_async_io()          # 路由内部真的在 await 异步 IO

@app.get("/b")
def endpoint_b():                  # 纯同步代码
    time.sleep(0.1)
```

判定口诀：

1. **函数体里有 await（异步库：httpx.AsyncClient、asyncpg…）→ 用 `async def`**
2. **函数体是同步阻塞（requests、pandas、time.sleep）→ 用普通 `def`**：FastAPI 会把它丢进线程池，不阻塞事件循环
3. **最危险的写法**：`async def` 里调同步阻塞库（如 requests）——整个事件循环被卡住，所有并发请求一起卡

## 6.1.5 项目结构建议

```text
01_minimal/
├── main.py        # 全部代码（教学阶段单文件最直观）
└── __pycache__/
```

小项目单文件起步完全正确；等路由超过 5 个再用 APIRouter 拆分（见 03 章）。

## 常见坑与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: main` | 在错误目录启动 | `cd` 到 main.py 所在目录再 uvicorn |
| 422 但参数看起来没问题 | JSON 里传了字符串数字 | 看 422 的 loc/type 定位 |
| POST 收不到 body | 忘了 `-H "Content-Type: application/json"` | curl 必须带头 |
| 端口被占用 | 之前的 uvicorn 没退 | `lsof -i:8100` 找到进程 kill（见 [Ubuntu·进程](../02-linux-ubuntu/03-用户与进程管理.md)） |
| 改了代码不生效 | 没开 --reload | 开发期加 --reload（生产不要，见第 6 篇） |

## 动手练习

1. 给 `/books/{id}` 增加 `rating` 过滤查询参数并校验范围 1~5。
2. 增加 `DELETE /books/{id}`，返回 204。
3. 在 /docs 里故意传错类型，观察 422 的 loc 字段。

## 小结与自检清单

- [ ] 能说出三大框架的定位差异
- [ ] 三种输入（路径/查询/请求体）都能写对
- [ ] 会看 422 的 loc/type 定位参数错误
- [ ] async def 的判定口诀能背出来

## 延伸阅读

- [FastAPI 官方教程（中文）](https://fastapi.tiangolo.com/zh/tutorial/first-steps/)——本篇的权威展开
- [Pydantic v2 文档](https://docs.pydantic.dev/latest/concepts/fields/)
