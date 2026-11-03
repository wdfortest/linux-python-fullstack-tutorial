# 第 01 章 · Git/GitHub 完全指南

> 8 篇 · 约 3,300 行 · 配套练习：`projects/git-lab/`
> 建议总学习时长：约 2 周（每天 1-2 篇，边读边练）

从「版本控制是什么」一路讲到「团队协作 + CI」，以本仓库自身为活教材。

## 目录

| # | 文档 | 内容一句话 | 配套 |
|---|---|---|---|
| 01 | [Git 核心概念与安装配置](01-Git核心概念与安装配置.md) | 对象模型、三区模型、安装与首次配置 | — |
| 02 | [Git 日常操作完全指南](02-Git日常操作完全指南.md) | add/commit/log/diff、撤销全景、.gitignore、stash、tag | git-lab |
| 03 | [分支完全指南](03-分支完全指南.md) | 分支本质、merge/rebase、冲突解决、团队分支策略 | git-lab |
| 04 | [远程仓库与 GitHub 入门](04-远程仓库与GitHub入门.md) | remote/push/fetch/pull、SSH 密钥、多账号、gh CLI | git-lab |
| 05 | [团队协作实战（Issue-PR-CodeReview）](05-团队协作实战（Issue-PR-CodeReview）.md) | Fork 工作流、PR 全流程、review 规范、分支保护 | — |
| 06 | [Commit 规范与团队工程实践](06-Commit规范与团队工程实践.md) | Conventional Commits、SemVer、CHANGELOG | — |
| 07 | [Git 进阶与急救手册](07-Git进阶与急救手册.md) | reflog 后悔药、reset 三模式、cherry-pick、bisect、误提交敏感信息 | — |
| 08 | [GitHub Actions 持续集成入门](08-GitHub%20Actions持续集成入门.md) | workflow 语法、本仓库真实 CI 逐行讲解、secrets、badge | 仓库 ci.yml |

## 学完你能做到

- 独立完成「写代码 → 提交 → 推送 → 处理冲突 → 发 PR → 合并」全流程
- 出事不慌：误 reset / 误删分支 / 误提交密钥都有标准急救路径
- 能读懂并配置一个 GitHub Actions CI（本仓库 `.github/workflows/ci.yml` 就是范例）

## 与后文的衔接

第 02 章把代码部署上服务器用 `git pull`；第 07 章实战项目的 CI 就是第 08 章的落地；全仓库的 commit 历史本身就是第 06 章规范的示范。

← 返回 [总目录](../../README.md)
