# git-lab：Git 章节配套练习仓库

本目录是 `docs/01-git-github/` 八章的配套练习脚本集合。脚本只做两件事：
**生成带真实历史的练习仓库**和**制造需要你用 Git 技能自救的事故现场**。
它们不修改本教程仓库的任何文件，所有产物默认落在 `~/` 或 `/tmp/` 下。

## 脚本清单

| 脚本 | 用途 | 对应章节 |
|---|---|---|
| `setup-practice-repo.sh` | 一键生成带 6 个提交、含标签与 .gitignore 的计算器项目练习仓库 | [第 01 章](../../docs/01-git-github/01-Git核心概念与安装配置.md)（练习 4）、[第 02 章](../../docs/01-git-github/02-Git日常操作完全指南.md)、[第 03 章](../../docs/01-git-github/03-分支完全指南.md)、[第 06 章](../../docs/01-git-github/06-Commit规范与团队工程实践.md) |
| `merge-conflict-setup.sh` | 生成两个分支对同一行做不同修改的冲突现场（停在合并前一刻） | [第 03 章](../../docs/01-git-github/03-分支完全指南.md)（练习 3） |
| `rescue-drill.sh` | 制造「误删分支 + 误 reset」双重事故现场，供 reflog 自救演练 | [第 07 章](../../docs/01-git-github/07-Git进阶与急救手册.md)（练习 1） |

## 用法

```bash
# 1. 基础练习仓库（默认生成到 ~/git-lab-practice，可用参数指定其他位置）
./setup-practice-repo.sh
./setup-practice-repo.sh /tmp/my-practice

# 2. 冲突演练现场（默认 ~/git-conflict-demo）
./merge-conflict-setup.sh
cd ~/git-conflict-demo && git merge feature/add-farewell   # 合并即触发冲突

# 3. 急救演练（默认 ~/git-rescue-demo）
./rescue-drill.sh
cd ~/git-rescue-demo && git reflog
```

## 脚本约定

- 所有脚本幂等：目标目录已存在时会拒绝执行，先手工删除再重跑。
- 练习仓库的提交信息遵循教程第 06 章的 Conventional Commits 规范，历史本身即教材。
- 脚本生成的是**本地普通仓库**（无远程）；推到你自己的 GitHub 是第 04 章的练习。
- 急救与冲突脚本会在输出里印出任务说明，答案在对应章节正文，先自己动手再看。

## 自检

跑完 `setup-practice-repo.sh` 后，以下命令应有对应输出：

```bash
cd ~/git-lab-practice
git log --oneline --graph --all --decorate   # 6 个以上提交
git tag                                       # v1.0.0
git check-ignore -v .env                      # 命中 .gitignore 规则
```
