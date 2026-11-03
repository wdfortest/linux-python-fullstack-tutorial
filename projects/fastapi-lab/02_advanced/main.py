"""fastapi-lab/02 进阶：响应模型、依赖注入、错误处理、中间件、后台任务。

运行：
    cd projects/fastapi-lab/02_advanced && uvicorn main:app --port 8101 --reload
验证要点：
    curl http://127.0.0.1:8101/users/1          # response_model 过滤掉 password
    curl http://127.0.0.1:8101/stats            # 依赖注入 + 计时中间件日志
    curl -X POST http://127.0.0.1:8101/mail?to=a@b.c   # BackgroundTasks
"""
from __future__ import annotations

import logging
import time

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("lab02")

app = FastAPI(title="fastapi-lab 02 · 请求与响应进阶", version="1.0.0")

USERS = {
    1: {"id": 1, "name": "alice", "role": "admin", "password": "never-return-this", "email": "alice@example.com"},
    2: {"id": 2, "name": "bob", "role": "user", "password": "secret-too", "email": "bob@example.com"},
}


class UserOut(BaseModel):
    """响应模型：明确「哪些字段允许出现在响应里」。"""

    id: int
    name: str
    role: str
    email: str


def pagination(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    """函数依赖：可复用的分页参数组。"""
    return {"limit": limit, "offset": offset}


def user_stats() -> dict:
    """类间依赖：模拟一次耗时的统计查询。"""
    return {"users": len(USERS), "admins": sum(1 for u in USERS.values() if u["role"] == "admin")}


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int) -> dict:
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user  # 多余的 password 字段会被 response_model 过滤掉


@app.get("/users", response_model=list[UserOut])
def list_users(page: dict = Depends(pagination)) -> list[dict]:
    items = list(USERS.values())[page["offset"] : page["offset"] + page["limit"]]
    return items  # 实测教训：最初版本漏了 response_model，password 字段直接泄漏！


@app.get("/leaky-users")
def leaky_users(page: dict = Depends(pagination)) -> dict:
    """⚠️ 反面演示端点：故意不挂 response_model，用于教学对比（见 /users）。"""
    items = list(USERS.values())[page["offset"] : page["offset"] + page["limit"]]
    return {"total": len(USERS), **page, "items": items}


@app.get("/stats")
def stats(info: dict = Depends(user_stats)) -> dict:
    return info


@app.middleware("http")
async def add_timing(request, call_next):
    """中间件：给每个响应加 X-Process-Time 头并记录慢请求。"""
    start = time.perf_counter()
    response = await call_next(request)
    cost_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{cost_ms:.1f}ms"
    if cost_ms > 50:
        logger.warning("慢请求 %s 耗时 %.1fms", request.url.path, cost_ms)
    return response


def send_welcome_email(to: str) -> None:
    time.sleep(1)  # 模拟慢 IO
    logger.info("欢迎邮件已发送至 %s", to)


@app.post("/mail")
def send_mail(to: str, tasks: BackgroundTasks) -> dict:
    tasks.add_task(send_welcome_email, to)   # 响应先返回，任务后台跑
    return {"queued": True, "to": to}
