#!/usr/bin/env bash
# rescue-drill.sh —— 制造「误删分支 + 误 reset」双重事故现场（第 07 章练习 1 用）
#
# 用法：
#   ./rescue-drill.sh [目标目录]
#   目标目录默认 ~/git-rescue-demo；目录已存在时拒绝执行。
#
# 产物：一个发生了两场"事故"的仓库：
#   1. 分支 feature/important-work（含 2 个提交）被 -D 强删；
#   2. main 被 reset --hard 回退 2 个提交。
# 你的任务：只用 git reflog 与 git branch，把两样都找回来。
# 解法见 docs/01-git-github/07-Git进阶与急救手册.md 的 7.2 节（先自己动手）。
set -euo pipefail

TARGET="${1:-$HOME/git-rescue-demo}"

if [ -e "$TARGET" ]; then
    echo "错误：目标目录已存在：$TARGET" >&2
    exit 1
fi

mkdir -p "$TARGET"
cd "$TARGET"

git init -q
git config user.name  "${GIT_LAB_NAME:-练习者}"
git config user.email "${GIT_LAB_EMAIL:-practice@example.com}"

# 基线
echo "git rescue drill" > README.md
git add -A
git commit -q -m "chore: 初始化演练仓库"

# 重要分支：2 个提交
git switch -q -c feature/important-work
echo "def stats(): return 'user stats module'" > stats.py
git add -A
git commit -q -m "feat: 用户统计模块"
echo "def export(): return 'report csv'" > export.py
git add -A
git commit -q -m "feat: 报表导出功能"

# 回 main，制造另外 2 个提交
git switch -q main
echo "docs line 1" > notes.txt
git add -A
git commit -q -m "docs: 记录使用说明"
echo "docs line 2" >> notes.txt
git commit -q -am "docs: 补充第二条说明"

# ============ 事故开始 ============
# 事故 1：手滑强删了还有未合并提交的分支
git branch -D feature/important-work >/dev/null

# 事故 2：手滑把 main 回退了 2 个提交（--hard 连工作区一起抹）
git reset -q --hard HEAD~2

echo
echo "事故现场已就绪：$TARGET（当前状态并不健康）"
echo
git log --oneline --graph --all
echo
echo "任务一：找回被删的 feature/important-work 分支（它的 2 个提交还在对象库里）。"
echo "任务二：把 main 恢复到包含全部 4 个提交。"
echo
echo "允许使用的工具：git reflog、git branch、git reset。"
echo "答案在 docs/01-git-github/07-Git进阶与急救手册.md 7.2 节——先自己动手再看。"
