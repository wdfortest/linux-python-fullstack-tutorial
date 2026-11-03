#!/usr/bin/env bash
# merge-conflict-setup.sh —— 一键制造 merge 冲突现场（第 03 章练习 3 用）
#
# 用法：
#   ./merge-conflict-setup.sh [目标目录]
#   目标目录默认 ~/git-conflict-demo；目录已存在时拒绝执行。
#
# 产物：一个含两个分支的仓库。两个分支分别改了 app.txt 的同一行，
# 仓库停在「合并前一刻」，由你执行 git merge 触发并解决冲突。
# 解法见 docs/01-git-github/03-分支完全指南.md 的 3.5.3 节。
set -euo pipefail

TARGET="${1:-$HOME/git-conflict-demo}"

if [ -e "$TARGET" ]; then
    echo "错误：目标目录已存在：$TARGET" >&2
    exit 1
fi

mkdir -p "$TARGET"
cd "$TARGET"

git init -q
git config user.name  "${GIT_LAB_NAME:-练习者}"
git config user.email "${GIT_LAB_EMAIL:-practice@example.com}"

# 基线：两行文本
printf 'line1\nline2\n' > app.txt
git add -A
git commit -q -m "feat: 初始化 app.txt 两行文本"

# feature 分支：把第二行改成 feature 版本
git switch -q -c feature/add-farewell
printf 'line1\nline2\nline3-farewell\n' > app.txt
git commit -q -am "feat: feature 分支追加告别语一行"

# main 分支：独立地把第二行改成 main 版本（制造同区域分歧）
git switch -q main
printf 'line1\nline2-main\n' > app.txt
git commit -q -am "fix: main 分支润色第二行"

echo
echo "冲突现场已就绪：$TARGET"
echo
git log --oneline --graph --all
echo
echo "任务：在 main 分支执行  git merge feature/add-farewell，"
echo "然后按 docs/01-git-github/03-分支完全指南.md 3.5.3 节的四步流程解决冲突。"
echo "提示：git status 会把每一步该做什么写在提示里；git merge --abort 可随时重来。"
