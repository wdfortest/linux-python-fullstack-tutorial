#!/usr/bin/env bash
# setup-practice-repo.sh —— 一键生成 Git 章节的练习仓库
#
# 用法：
#   ./setup-practice-repo.sh [目标目录]
#   目标目录默认 ~/git-lab-practice；目录已存在时拒绝执行（幂等保护）。
#
# 产物：一个含 6 个提交、1 个附注标签、完整 .gitignore 的 Python 计算器项目。
# 提交信息遵循 docs/01-git-github/06-Commit规范与团队工程实践.md 的规范。
set -euo pipefail

TARGET="${1:-$HOME/git-lab-practice}"

if [ -e "$TARGET" ]; then
    echo "错误：目标目录已存在：$TARGET" >&2
    echo "请先删除或指定其他目录，例如：./setup-practice-repo.sh /tmp/git-practice-2" >&2
    exit 1
fi

mkdir -p "$TARGET"
cd "$TARGET"

git init -q
git config user.name  "${GIT_LAB_NAME:-练习者}"
git config user.email "${GIT_LAB_EMAIL:-practice@example.com}"

# ---------- 提交 1：项目骨架 + .gitignore ----------
mkdir -p src tests
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
# 环境变量（绝不提交密钥）
.env
.env.*
!.env.example
# 测试与缓存
.pytest_cache/
.coverage
EOF

cat > .env.example <<'EOF'
# 复制本文件为 .env 并填入真实值；.env 已被 .gitignore 忽略
APP_ENV=dev
EOF

cat > README.md <<'EOF'
# git-lab 练习项目：计算器

docs/01-git-github/ 各章练习用仓库。
EOF
git add -A
git commit -q -m "chore: 初始化项目结构与 .gitignore"

# ---------- 提交 2：核心功能 ----------
cat > src/calculator.py <<'EOF'
"""练习用计算器模块。"""


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b + 1  # FIXME: 练习仓库故意埋的偏差，留给 fix 提交
EOF
git add -A
git commit -q -m "feat: 实现加减法运算"

# ---------- 提交 3：测试 ----------
cat > tests/test_calculator.py <<'EOF'
"""calculator 的练习测试集。"""
from src.calculator import add, subtract


def test_add():
    assert add(1, 2) == 3


def test_subtract():
    assert subtract(5, 3) == 2  # 提交 5 之前会失败，属练习设计
EOF
git add -A
git commit -q -m "test: 补充加减法单元测试"

# ---------- 提交 4：修 bug ----------
sed -i.bak 's/return a - b + 1  # FIXME: 练习仓库故意埋的偏差，留给 fix 提交/return a - b  # 修复偏差/' src/calculator.py
rm -f src/calculator.py.bak
git add -A
git commit -q -m "fix(calculator): 修复减法运算多加 1 的偏差"

# ---------- 提交 5：新功能 + 打标签 ----------
cat >> src/calculator.py <<'EOF'


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b
EOF
git add -A
git commit -q -m "feat: 支持乘除法并对除零抛出 ValueError"
git tag -a v1.0.0 -m "发布 1.0.0：四则运算可用"

# ---------- 提交 6：文档（最后一个，练 blame/show 用） ----------
cat >> README.md <<'EOF'

## 功能

- add / subtract / multiply / divide（除零抛 ValueError）
- 除零行为自 v1.0.0 起生效
EOF
git add -A
git commit -q -m "docs(readme): 补充功能说明与除零行为"

# ---------- 验收信息 ----------
echo
echo "练习仓库已生成：$TARGET"
echo
git log --oneline --graph --all --decorate
echo
git tag
echo
echo "下一步：cd $TARGET 后按 docs/01-git-github/ 各章动手练习操作。"
