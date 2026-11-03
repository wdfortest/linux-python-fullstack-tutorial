"""fastapi-lab/04 认证：密码哈希 + OAuth2 Password 流程 + JWT。

运行：
    cd projects/fastapi-lab/04_auth && uvicorn main:app --port 8103 --reload
全流程验证：
    # 1) 注册（用 -d 表单，OAuth2PasswordRequestForm 是 form 不是 json）
    curl -X POST http://127.0.0.1:8103/register -d "username=alice&password=wonderland123"
    # 2) 登录拿 token（/docs 页面的 Authorize 按钮也走这个端点）
    curl -X POST http://127.0.0.1:8103/token -d "username=alice&password=wonderland123"
    # 3) 带 token 访问受保护路由
    curl http://127.0.0.1:8103/me -H "Authorization: Bearer <上面拿到的token>"
    # 4) 不带 token -> 401
    curl http://127.0.0.1:8103/me

安全要点：
- 密码绝不存明文：哈希加盐（本 lab 用 hashlib.pbkdf2_hmac，标准库零依赖）
- SECRET_KEY 从环境变量读取（.env），绝不写死进代码
- token 有效期 exp 由 JWT 签名保证不可篡改
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

import jwt  # PyJWT 2.15.1
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI(title="fastapi-lab 04 · 认证授权与安全", version="1.0.0")

# 环境变量优先；本地演示给的默认值仅用于 lab，生产必须显式配置
SECRET_KEY = os.getenv("LAB_SECRET_KEY", "lab-only-not-for-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 30 * 60

USERS: dict[str, dict] = {}   # username -> {hash, salt, role}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def hash_password(password: str, salt: bytes) -> str:
    """PBKDF2-HMAC-SHA256，迭代 30 万次（标准库实现，成本高于通行 10 万的基线）。"""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300000)
    return digest.hex()


def verify_password(password: str, salt: bytes, expected_hex: str) -> bool:
    """恒定时间比较，防时序侧信道。"""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300000)
    return hmac.compare_digest(digest.hex(), expected_hex)


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """依赖：校验 JWT 并返回用户信息；无效/过期一律 401。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    username = payload.get("sub", "")
    if username not in USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user gone")
    return {"username": username, "role": payload.get("role")}


@app.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends()) -> dict:
    if form.username in USERS:
        raise HTTPException(status_code=400, detail="username exists")
    salt = secrets.token_bytes(16)
    USERS[form.username] = {"salt": salt, "hash": hash_password(form.password, salt), "role": "user"}
    return {"registered": form.username}


@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()) -> dict:
    record = USERS.get(form.username)
    if record is None or not verify_password(form.password, record["salt"], record["hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")
    return {"access_token": create_token(form.username, record["role"]), "token_type": "bearer"}


@app.get("/me")
def me(user: dict = Depends(get_current_user)) -> dict:
    return user


@app.get("/admin")
def admin_only(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin required")
    return {"secret": "only admins see this"}
