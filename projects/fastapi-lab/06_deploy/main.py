"""fastapi-lab/06 部署就绪配置：环境变量分层 + 结构化启动。

运行：
    cd projects/fastapi-lab/06_deploy
    cp .env.example .env && python -m pip install python-dotenv（如未装）
    uvicorn main:app --port 8104 --reload
验证：
    curl http://127.0.0.1:8104/healthz
    curl http://127.0.0.1:8104/config    # 观察 env -> 默认值 的优先级
    APP_ENV=production uvicorn main:app --port 8104   # 生产去 --reload、加 workers
"""
from __future__ import annotations

import os
import platform
from pathlib import Path

from fastapi import FastAPI

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")   # .env 不入库（.gitignore 已覆盖）
except ImportError:
    pass  # 允许无 python-dotenv：环境变量直接注入


class Settings:
    """12-factor 风格配置：环境变量 > 默认值。绝不把密钥写进代码或 git。"""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "dev")
        self.app_name: str = os.getenv("APP_NAME", "fastapi-lab06")
        self.debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/lab06.db")
        self.secret_key: str = os.getenv("SECRET_KEY", "")    # 生产必须显式提供
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def unsafe_for_production(self) -> list[str]:
        """上线自检：返回「生产环境不允许的配置」清单。"""
        problems: list[str] = []
        if self.app_env == "production":
            if not self.secret_key:
                problems.append("SECRET_KEY 未设置")
            if self.debug:
                problems.append("APP_DEBUG 在生产必须为 false")
            if self.database_url.startswith("sqlite"):
                problems.append("生产建议 MySQL/PostgreSQL（本项目教学环境 SQLite 可接受）")
        return problems


settings = Settings()

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url=None if settings.app_env == "production" else "/docs")


@app.get("/healthz")
def healthz() -> dict:
    problems = settings.unsafe_for_production()
    return {
        "status": "degraded" if problems else "ok",
        "app_env": settings.app_env,
        "python": platform.python_version(),
        "problems": problems,
    }


@app.get("/config")
def config() -> dict:
    """演示配置来源；真实项目不要把内部配置暴露成端点！"""
    return {
        "app_env": settings.app_env,
        "debug": settings.debug,
        "database_url": settings.database_url.replace("://", "://***@") if "@" in settings.database_url else settings.database_url,
        "log_level": settings.log_level,
        "secret_key_set": bool(settings.secret_key),   # 只报告「是否设置」，绝不回显值
    }
