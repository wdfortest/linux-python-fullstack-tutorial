# 第 02 章 · Ubuntu 服务器实战

> 10 篇 · 约 4,300 行 · 主线 Ubuntu 24.04 LTS（26.04 LTS 新一代一并介绍）
> 建议总学习时长：约 3 周；强烈建议配一台真实的云服务器/虚拟机

从拿到一台裸服务器，到能把 Python 项目安全地部署上线并长期运维。

## 目录

| # | 文档 | 内容一句话 | 关键产出 |
|---|---|---|---|
| 01 | [Ubuntu 安装与远程连接](01-Ubuntu安装与远程连接.md) | 版本选择、三种获取途径、SSH 密钥、**安全加固清单** | 一台加固过的服务器 |
| 02 | [文件系统与常用命令](02-文件系统与常用命令.md) | FHS、文件操作、权限模型、查找、管道与重定向 | 熟练命令行 |
| 03 | [用户与进程管理](03-用户与进程管理.md) | 用户组、sudoers、ps/top/kill、端口占用排查 | — |
| 04 | [软件包管理 apt 与系统服务 systemd](04-软件包管理apt与系统服务systemd.md) | apt 全套、systemctl、journalctl、**手写 service**、timer 与 cron | 自定义服务 |
| 05 | [网络配置与防火墙](05-网络配置与防火墙.md) | ip/ss、UFW 完全指南、云安全组双层、curl 实用参数 | 排障组合拳 |
| 06 | [Shell 脚本基础与自动化](06-Shell脚本基础与自动化.md) | 语法速成、`set -euo pipefail`、三个实战脚本 | 自动化脚本 |
| 07 | [Python 环境部署（venv-uv-多版本）](07-Python环境部署(venv-uv-多版本).md) | PEP 668 报错解法、venv 原理、uv 现代工作流、项目部署路径 | 服务器 Python 环境 |
| 08 | [MySQL 部署与数据库运维](08-MySQL部署与数据库运维.md) | 安装加固、utf8mb4、远程访问安全、mysqldump 定时备份 | 生产级数据库 |
| 09 | [Nginx 安装与反向代理](09-Nginx安装与反向代理.md) | sites-available 机制、**FastAPI 反代逐行配置**、certbot HTTPS | 公网可访问 |
| 10 | [生产部署清单与运维 Monitor](10-生产部署清单与运维Monitor.md) | 30+ 项上线 Checklist、5 个故障演练、回滚策略、完整上线时间线 | 上线能力 |

## 学完你能做到

- 把一台裸服务器变成「SSH 密钥登录 + 防火墙 + fail2ban + 自动更新」的安全基座
- 用 systemd 让任何 Python 服务常驻自启，用 journalctl 快速定位日志
- 把本教程实战项目（book-insight）完整部署到公网并配置 HTTPS（第 10 章有全命令时间线）

## 与前后的衔接

第 01 章的 SSH 密钥在这里天天用；第 07/09 章是实战项目[部署篇](../07-final-project/05-测试CI与部署上线.md)的直接依赖。

← 返回 [总目录](../../README.md)
