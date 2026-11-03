# 第 7 章 · Python 环境部署（venv / uv / 多版本）

> 本章配套代码：服务器上的部署目录 `/opt/book-insight/`（对应仓库 `projects/book-insight/`）；本章新建的最小 FastAPI 应用 `/opt/book-insight/main.py` 与服务文件 `/etc/systemd/system/book-insight.service`。
> 建议学习时长：约 4 小时

## 学习目标

学完本章，你能够：

1. 解释 PEP 668 的来龙去脉，遇到 `externally-managed-environment` 报错知道三种正解与一种不推荐的逃生门；
2. 用 deadsnakes PPA 或 uv 安装指定版本的 Python（3.12/3.13/3.14）；
3. 说清 venv 的实现原理（Python 解释器软链接 + 独立 site-packages + PATH 前置），会创建/激活/退出；
4. 管理依赖：pip 换源、requirements.txt 的「freeze 模式」与「顶层依赖模式」取舍，并用 uv 完成现代工作流（`uv venv` / `uv pip install` / `uv sync`）；
5. **把本仓库的 `projects/book-insight` 完整部署到 Ubuntu**：git clone → uv 环境 → systemd 服务（复用第 4 章模板）→ curl 验收。

## 7.1 前置知识 / 本章地位

前六章把服务器本身准备好了：能登录（第 1 章）、会文件与权限（第 2 章）、懂进程与用户（第 3 章）、会写服务（第 4 章）。从本章开始，**把你真正的东西——Python 项目——搬上去**。

本章以本仓库 `projects/book-insight`（爬虫产出 `data/books.db`，第 6 章已写过备份脚本）为部署对象。全书主线版本事实（以 STYLE_GUIDE 版本表为准，撰写时实测）：本地 venv 用 Python 3.14.0、FastAPI 0.162.0、uvicorn 0.52.0；Ubuntu 24.04 自带的系统 Python 是 3.12，**这正是本章要解决的第一组矛盾**。

## 7.2 为什么不能直接 pip 装系统 Python：PEP 668

### 7.2.1 报错现场

在 Ubuntu 24.04 直接执行：

```bash
pip install requests
```

预期报错（文本节选，读者对照自查）：

```text
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.

    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    You can also use `python3 -m venv --system-site-packages
    path/to/venv` to use packages already installed via apt.
    See https://venv.python.org for more information.

note: If you believe this is a mistake, please contact your Python installation
or OS distribution provider. You can override this, at the risk of breaking your
Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the original specification.
```

### 7.2.2 为什么 Ubuntu 要拦你

这个拦截是 Ubuntu 有意为之：系统 Python 由 apt 管理，apt 装的系统工具里大量脚本依赖 `python3-*` 系统包（Ubuntu 自身组件就是 Python 写的）。如果你用 pip 往系统 Python 的 site-packages 装包，**pip 与 apt 会开始争夺同一批文件**：pip 升级某库可能与 apt 包冲突、覆盖系统工具依赖的版本，轻则 apt 升级报错，重则把系统工具链搞坏且难以回滚。PEP 668 定义了 `EXTERNALLY-MANAGED` 标记文件（Ubuntu 放在 `/usr/lib/python3.12/EXTERNALLY-MANAGED`），pip 看到它就拒绝在「外部管理的环境」里安装。

### 7.2.3 三种解法与一个逃生门

| 方案 | 适用场景 | 推荐度 |
|---|---|---|
| ① venv 虚拟环境 | 项目依赖（95% 的场景） | 推荐，本章主线 |
| ② `apt install python3-xxx` | 需要「系统级」可用的小工具/库 | 有限推荐 |
| ③ pipx | 独立命令行工具（如 `pipx install httpie`） | 工具场景推荐 |
| ④ `--break-system-packages` | 明知后果的临时实验 | 不推荐 |

```bash
# 方案②：让 apt 管理系统级包（注意包名前缀 python3-）
sudo apt install python3-requests

# 方案③：pipx 每个工具独立环境
sudo apt install pipx
pipx ensurepath
pipx install httpie
```

方案④只在「一次性、用完即弃的容器/测试机」里可接受；在长期运行的服务器上它就是 7.2.2 描述的所有事故的入口，本教程后续一律不使用。

## 7.3 多版本 Python：deadsnakes PPA 与 uv

Ubuntu 24.04 自带 3.12。当你需要 3.13/3.14（比如与本地 `jjyv` 环境的 3.14.0 对齐）时，两条路：

### 路线 A：deadsnakes PPA（apt 风格）

deadsnakes 是 Ubuntu 社区长期维护的 Python 多版本 PPA（呼应第 4 章 PPA 风险说明：它是知名 PPA，但仍是第三方源）：

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
apt list 2>/dev/null | grep python3.1   # 看看有哪些版本
sudo apt install python3.14 python3.14-venv python3.14-dev
python3.14 --version
```

注意配套包：`-venv` 提供 venv 模块支持、`-dev` 提供编译头文件（装需要编译的库如 psycopg2 时必需）。可用版本随 PPA 更新，以 PPA 页面为准。

### 路线 B：uv 托管 Python（推荐，见 7.5 节）

```bash
uv python install 3.12     # uv 下载并管理独立的 CPython 构建
uv python list             # 查看可用/已装版本
```

uv 管理的 Python 与系统 apt 的 Python 完全隔离，互不影响，且不需要碰任何 PPA。**新部署优先用路线 B**，路线 A 留给「必须 apt 化管理」的场景。另有 pyenv（7.6 节）走「源码编译」路线，历史悠久但部署机不首选。

## 7.4 venv：虚拟环境的原理与操作

### 7.4.1 原理：它到底做了什么

venv（Virtual Environment，虚拟环境）解决的问题：**项目 A 要 requests==2.31，项目 B 要 requests==2.34，同一解释器装不下两份**。它的实现出奇简单，理解了就不怕任何 venv 问题——创建 venv 时只做了三件事：

1. 复制（多数平台是**软链接**，`ls -l .venv/bin/python3` 能看到 `-> /usr/bin/python3.12`）一份解释器入口；
2. 新建一个**独立的 site-packages** 目录（`.venv/lib/python3.12/site-packages/`），pip 装的包都进这里；
3. 写几个激活脚本，激活时把 `.venv/bin` **前置到 PATH**，让 `python`/`pip` 优先命中 venv 内的入口。

所以「激活」只是改了当前 shell 的 PATH 和提示符变量，**不改变任何系统状态**；解释器本体仍是系统那个（升级系统 Python 可能影响链接它的 venv，重建即可）。验证一下：

```bash
which python3    # 激活后指向 .venv/bin/python3
echo $PATH       # .venv/bin 排在最前
```

### 7.4.2 创建、激活、退出

```bash
cd /opt/book-insight
python3 -m venv .venv            # 用系统 3.12 创建
source .venv/bin/activate        # 激活（提示符前出现 (.venv)）
python --version                 # Python 3.12.x（venv 内）
pip install requests
deactivate                       # 退出
```

用指定版本创建：`uv python install 3.14` 后 `uv venv --python 3.14`（见 7.5），或 `python3.14 -m venv .venv`。

**一个重要习惯：`.venv` 不进 git**（本仓库 `.gitignore` 已排除 `venv/`、`.venv/`），虚拟环境是「本机产物」，可重建、不该共享。要迁移的是依赖清单，不是目录。

### 7.4.3 激活脚本做了什么（好奇者的解剖）

`cat .venv/bin/activate` 的核心三行（节选）：

```bash
VIRTUAL_ENV="/opt/book-insight/.venv"
export VIRTUAL_ENV
PATH="$VIRTUAL_ENV/bin:$PATH"     # 前置 PATH——venv 生效的全部秘密
```

没有 export PATH 操作的进程不受影响——这就是为什么 systemd 服务文件里**不激活 venv，而是直接用 `.venv/bin/uvicorn` 绝对路径**（第 4 章 ExecStart 的写法）。想通这一点，你就理解了生产部署里 venv 的正确打开方式。

## 7.5 uv：现代工作流（重点）

### 7.5.1 uv 是什么、为什么快

uv 是 Rust 编写的 Python 包与环境管理器（Astral 出品），一个二进制同时覆盖 pip、venv、pyenv 的核心能力：并行下载、全局缓存（同版本包只下载一次）、内存级元数据解析，安装速度通常是 pip 的 10 倍以上；还能把「装 Python、建环境、锁依赖」统一成一条流水线。对部署来说它最大的价值是**快与可复现**：服务器上重建环境从「几分钟」变「几秒」。

### 7.5.2 安装

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env      # 让当前 shell 找到 uv（按安装完成提示执行）
uv --version
```

`curl | sh` 的安全须知：这是官方文档给的一键安装方式，执行前可以先把脚本下载下来看一眼再跑（`curl -LsSf https://astral.sh/uv/install.sh -o uv-install.sh`，审查后 `sh uv-install.sh`），以 uv 官方文档为准。

### 7.5.3 三种日常姿势

```bash
# 姿势一：uv 管理环境，pip 风格安装（与既有习惯最接近）
uv venv --python 3.14            # 创建 .venv（自动下载 3.14 解释器）
source .venv/bin/activate
uv pip install requests beautifulsoup4    # 装「进」这个 venv，速度快
uv pip install -r requirements.txt
uv pip list

# 姿势二：uv 项目模式（pyproject.toml + uv.lock，团队协作首选）
uv init --no-readme              # 已有项目可跳过，手写 pyproject.toml 亦可
uv add requests fastapi uvicorn  # 添加依赖并写入 pyproject + 锁定 uv.lock
uv sync                          # 按 uv.lock 精确重建整个环境（部署机用这个）

# 姿势三：一次性运行（不落地环境）
uvx ruff check .                 # 临时环境跑工具，用完即弃
uv run python main.py            # 在项目环境里执行
```

`pyproject.toml` 与 `uv.lock` 的分工：前者声明**直接依赖与版本下限**（人维护），后者锁定**全部间接依赖的精确版本**（uv 自动生成，进 git）。部署机执行 `uv sync` 时按 lock 精确复现，这就是第 10 章「依赖锁定」检查项的落地方式。

### 7.5.4 pip 换源与 requirements.txt 的两种哲学

不使用 uv 时，pip 也应换国内源提速（以清华 PyPI 镜像为例）：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config list                  # 验证已写入 ~/.config/pip/pip.conf
```

requirements.txt 有两种生成哲学，部署认知关键点：

```bash
pip freeze > requirements.txt    # freeze 模式：连间接依赖与精确版本全部列出
```

- **freeze 模式**：完整但冗长（requests 一条会拖出 certifi、urllib3 等十几条），适合「精确复现某个已验证环境」；
- **顶层依赖模式**：手写只含直接依赖（`requests`、`fastapi`、`uvicorn[standard]`），间接依赖交给解析器，可读、可维护，适合开发期；
- 工程折中：pip-tools 的 `requirements.in`（顶层）→ `pip-compile` 生成 `requirements.txt`（锁定），或 uv 的 `pyproject.toml` + `uv.lock`。**本教程主线用 uv 锁定方案**；写顶层依赖时，major 版本锚定（如 `fastapi>=0.162,<0.163` 风格按团队约定）。

## 7.6 pyenv 简述

pyenv 是老牌的 Python 多版本管理器：在用户目录编译安装各版本 Python，用垫片（shim）机制按目录切换版本（`.python-version` 文件）。适合「单机多项目、各要不同小版本」的开发机。部署机场景的局限：**需要源码编译**（要先装 `build-essential libssl-dev zlib1g-dev` 等一串构建依赖，每版本数分钟），而 uv 下载预编译解释器秒级完成。本教程部署路线用 uv，pyenv 留作了解——维护存量服务器脚本时你可能会遇到它。

## 7.7 【实战】把 projects/book-insight 部署到 Ubuntu

目标：把爬虫项目部署到 `/opt/book-insight`，再补一个最小 FastAPI 服务把 `data/books.db` 的数据以 API 形式提供，由 systemd 托管。完成后 `curl http://127.0.0.1:8000/api/books` 能拿到数据——这就是第 9 章 Nginx 反代和第 10 章上线的地基。

### 第 1 步：创建部署用户与目录（复用第 3 章）

```bash
sudo adduser --system --group --home /opt/book-insight --shell /usr/sbin/nologin booksvc
sudo mkdir -p /opt/book-insight
sudo chown booksvc:booksvc /opt/book-insight
```

### 第 2 步：获取代码

```bash
sudo -u booksvc git clone <你的仓库地址> /opt/book-insight/app
# 示例（替换为你的仓库）：git clone git@github.com:<your-username>/linux学习与实战.git /opt/book-insight/app
cd /opt/book-insight/app
```

国内服务器访问 GitHub 慢时的稳妥做法：改用 SSH 部署密钥（`ssh-keygen` 生成后加入 GitHub Deploy Keys），或把代码镜像到国内托管平台。**不要**把 GitHub 账号密码写进任何脚本。

### 第 3 步：uv 建环境、装依赖

```bash
cd /opt/book-insight/app/projects/book-insight/crawler   # 代码在仓库内的位置
sudo -u booksvc bash -c 'export PATH="$HOME/.local/bin:$PATH" && uv venv --python 3.12'
sudo -u booksvc bash -c 'export PATH="$HOME/.local/bin:$PATH" && cd /opt/book-insight/app/projects/book-insight && uv pip install -p .venv/bin/python requests beautifulsoup4 lxml fastapi "uvicorn[standard]"'
```

说明：本仓库各 project 正逐步补齐 `pyproject.toml`/`uv.lock`；**仓库里有 `uv.lock` 时用 `uv sync` 一步到位**（依赖版本与开发机完全一致），没有时先 `uv pip install` 顶层依赖（上面就是这样做的），并在本机 `uv pip compile` 生成锁定文件补进仓库。版本对齐 STYLE_GUIDE 实测表：fastapi 0.162.0、uvicorn 0.52.0、requests 2.34.2。

### 第 4 步：跑一次爬虫，产出数据

```bash
sudo -u booksvc /opt/book-insight/app/projects/book-insight/.venv/bin/python crawl_books.py --limit 5
```

预期输出（节选）：

```text
INFO crawl_books 开始采集: https://books.toscrape.com/
INFO crawl_books 完成: 5 本，数据已写入 data/books.db
```

`data/books.db` 出现在 `/opt/book-insight/app/projects/book-insight/data/`（练习站明确允许抓取；限速参数保持默认，遵守 robots 与频率礼仪）。

### 第 5 步：最小 FastAPI 应用

`sudo -u booksvc nano /opt/book-insight/app/projects/book-insight/main.py`：

```python
#!/usr/bin/env python
"""book-insight 最小 API：把 data/books.db 以 JSON 形式提供。

SQL 一律参数绑定（? 占位符），禁止字符串拼接——本仓库硬性规范。
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

DB_PATH = Path(__file__).resolve().parent / "data" / "books.db"
app = FastAPI(title="book-insight API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="database not ready")
    return {"status": "ok"}


@app.get("/api/books")
def list_books(
    keyword: str = Query(default="", max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, object]]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="database not ready")
    sql = (
        "SELECT title, price, rating, in_stock FROM books "
        "WHERE title LIKE ? ORDER BY id LIMIT ?"
    )
    params: tuple[object, ...] = (f"%{keyword}%", limit)   # 参数绑定，用户输入永不拼接
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {"title": r[0], "price": r[1], "rating": r[2], "in_stock": r[3]}
        for r in rows
    ]
```

规范落实：`?` 占位符 + params 元组传参，`keyword` 即使用户输入 `' OR 1=1 --` 也只是普通字符串，不构成注入（反面案例警示见第 8 章 8.6 节，逐字对比）。

### 第 6 步：systemd 服务文件（复用第 4 章模板）

`sudo nano /etc/systemd/system/book-insight.service`：

```ini
[Unit]
Description=Book Insight API (FastAPI + uvicorn)
After=network.target

[Service]
Type=simple
User=booksvc
Group=booksvc
WorkingDirectory=/opt/book-insight/app/projects/book-insight
ExecStart=/opt/book-insight/app/projects/book-insight/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

与第 4 章 pydemo 的差异只有三处，都是「换内核」级别的修改：`User/Group` 换成专用服务用户；`ExecStart` 用 **venv 内的 uvicorn 绝对路径**（不激活 venv 的正确姿势，见 7.4.3）；`Environment=PYTHONUNBUFFERED=1` 关掉 stdout 缓冲，日志实时进 journal。启动与验收：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now book-insight
systemctl status book-insight
curl -s http://127.0.0.1:8000/health
curl -s "http://127.0.0.1:8000/api/books?limit=2"
```

预期输出：

```text
{"status":"ok"}
[{"title":"A Light in the Attic","price":51.77,"rating":5,"in_stock":22},{"title":"Tipping the Velvet","price":53.74,"rating":1,"in_stock":20}]
```

### 第 7 步：发布更新流程

把第 6 章的 `deploy.sh` 里 `APP_DIR` 指到 `/opt/book-insight/app`、`SERVICE` 改为 `book-insight` 即可：git pull → `uv sync`（或 uv pip install）→ `systemctl restart` → curl 健康检查。此后「发新版本」就是一条命令的事。

## 7.8 Windows/macOS 与 Ubuntu 的环境差异提示

本地开发、服务器部署，两边环境差异有四类高频坑：

| 差异点 | 本地（macOS/Windows） | Ubuntu 服务器 | 部署注意 |
|---|---|---|---|
| 换行符 | Windows 编辑器可能写 CRLF | 期望 LF | 编辑器统一 LF；见第 6 章坑表 |
| Python 版本 | 3.14（本地 jjyv） | 24.04 自带 3.12 | 用 uv 锁定/指定版本对齐，别凭感觉 |
| 路径与大小写 | macOS 默认不区分大小写 | ext4 严格区分 | `import Data` vs `data` 本地能过、服务器炸 |
| 系统库依赖 | macOS 有 brew 生态 | 需要 apt 装编译依赖 | 装 psycopg2/lxml 前先 `apt install build-essential python3-dev libpq-dev` |

最后一条展开说：纯 Python 的包（requests、fastapi）无需编译；含 C 扩展的包（lxml、psycopg2、pillow）若没有预编译 wheel，需要在服务器上现场编译，前提是装好 apt 侧的编译工具与开发头文件。报错形如 `error: command 'gcc' failed` 时，第一反应就是「缺 apt 侧依赖」，查该包官方文档的安装前置即可。

## 常见坑与排查（Troubleshooting）

| 报错/现象 | 原因 | 解决办法 |
|---|---|---|
| `externally-managed-environment` | 对系统 Python 直接 pip install | 建 venv/uv 环境；工具用 pipx；理解后绕开，不用 --break-system-packages |
| venv 激活了但 `pip` 装到全局 | 用了 `sudo pip`（sudo 重置 PATH） | venv 内绝不 sudo；`which pip` 确认指向 `.venv/bin/pip` |
| systemd 启动报 `ModuleNotFoundError: No module named 'fastapi'` | ExecStart 用了系统 python/uvicorn，没用 venv 内绝对路径 | 改成 `.venv/bin/uvicorn`；`sudo -u booksvc .venv/bin/python -c "import fastapi"` 验证 |
| 服务用户跑脚本报 `Permission denied` | 目录属主/权限没给 booksvc | `chown -R booksvc:booksvc /opt/book-insight`；代码目录不给写权限更佳 |
| `uv: command not found`（systemd/cron 里） | 非交互 shell 没有 `~/.local/bin` | unit 里写全路径 `Environment=PATH=...` 或直接用 venv 内绝对路径 |
| `error: command 'gcc' failed` | 缺编译工具链/头文件 | `apt install build-essential python3-dev` 及该包要求的 -dev 包 |
| 服务器跑出的数据与本地不一致 | Python 版本或依赖版本漂移 | uv.lock 精确同步；`pip freeze` 对比两端 |
| 重启服务器后服务没起来 | 只 start 没 enable | `systemctl enable book-insight`（第 4 章的坑，高频复发） |

## 动手练习

1. **三种安装路线各走一遍**：同一台服务器上分别用 deadsnakes 装 3.14、用 `uv python install 3.12`、跑 `pipx install httpie`，用 `python3.14 --version`、`uv python list`、`http --version` 验收。
   <details><summary>提示</summary>三种工具互不干扰是重点体会：apt 的在 /usr/bin，uv 的在 ~/.local，pipx 的在 ~/.local/pipx。</details>
2. **解剖 venv**：创建后执行 `ls -l .venv/bin/`、`cat .venv/pyvenv.cfg`、`which python3`，把三份输出与 7.4.1 的原理对照着讲给自己听。
   <details><summary>提示</summary>pyvenv.cfg 里的 home 指向系统解释器目录——「软链接 + 独立 site-packages」的直接证据。</details>
3. **完成 book-insight 部署并验收**：走完 7.7 全部 7 步，验收标准：`systemctl is-enabled book-insight` 为 enabled；kill 掉 uvicorn 进程后 5 秒内服务自动恢复；`/api/books?keyword=light` 返回过滤结果。
   <details><summary>提示</summary>kill 后 `sleep 5` 再 status，观察 Main PID 变化——第 4 章 Restart=on-failure 的实战确认。</details>
4. **给项目补 uv.lock**：在开发机 `uv init` 式地把 `pyproject.toml` 与 `uv.lock` 建起来并提交进仓库，然后到服务器把部署流程切换成 `uv sync --frozen`。
   <details><summary>提示</summary>对照 7.5.3 姿势二；切换后故意改坏 uv.lock 里一个版本号，观察 `uv sync --frozen` 拒绝执行——这就是「锁定」的含义。</details>

## 小结与自检清单

- [ ] 我能向别人解释 PEP 668 拦截的原因，以及 venv/pipx/apt 三种正解的分工
- [ ] 我会用 deadsnakes 或 uv 安装指定版本 Python，二者互不冲突
- [ ] 我能说出 venv 的三件事（软链接解释器/独立 site-packages/PATH 前置）
- [ ] 我知道 systemd 服务里不用 activate，而是 venv 内绝对路径
- [ ] 我掌握 uv 的安装与三种姿势，理解 pyproject.toml 与 uv.lock 的分工
- [ ] **projects/book-insight 已在我服务器上以 systemd 服务运行，kill 进程能自愈**
- [ ] 我的 API 代码全部参数绑定，没有一处字符串拼 SQL
- [ ] 我了解本地与 Ubuntu 的四类环境差异，知道 C 扩展包要配 apt 编译依赖

## 延伸阅读

- [PEP 668 原文](https://peps.python.org/pep-0668/)——externally-managed-environment 机制的原始定义。
- [Python venv 官方文档](https://docs.python.org/zh-cn/3/library/venv.html)——venv 模块的官方说明（有中文版）。
- [uv 官方文档](https://docs.astral.sh/uv/)——安装、项目模式、锁文件语义的权威参考。
- [FastAPI 官方文档：部署](https://fastapi.tiangolo.com/deployment/concepts/)——uvicorn 与进程模型、安全性的官方建议。
- [uvicorn 官方文档](https://www.uvicorn.org/deployment/)——生产部署参数（workers、绑定地址）说明。
- [pip 官方文档：配置](https://pip.pypa.io/en/stable/topics/configuration/)——换源与配置文件层级的权威说明。
