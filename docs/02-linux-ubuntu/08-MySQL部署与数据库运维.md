# 第 8 章 · MySQL 部署与数据库运维

> 本章配套代码：备份脚本 `~/scripts/backup_mysql.sh`（完整可运行，接第 6 章骨架）；演示库 `book_insight`；Python 对接脚本练习放 `/tmp/mysql-lab/`。
> 建议学习时长：约 4 小时

## 学习目标

学完本章，你能够：

1. 根据项目规模在 SQLite / MySQL / PostgreSQL 之间做出有依据的选型；
2. 在 Ubuntu 上安装 MySQL 8.0 并完成安全初始化（`mysql_secure_installation` 每一项都知道在改什么）；
3. 理解 auth_socket 与密码登录的原理，会建库（utf8mb4）、建用户、按最小化原则授权；
4. 配置「只本机监听 + SSH 隧道」的安全远程访问方式，并说明为什么不该把 3306 开到公网；
5. 部署带日期命名、自动清理的每日备份 cron，并用 mysqldump 演练一次完整恢复；
6. 用 pymysql 以**参数绑定**方式连接数据库，并识别 SQL 注入反例。

## 8.1 前置知识 / 本章地位

book-insight 目前用 SQLite（单文件、零部署），教学阶段足够。但当项目要「多个服务共享数据、并发写入、长期增长」时，就需要独立的数据库服务。本章把 MySQL 装进你的服务器、备好份、接上 Python——第 9 章 Nginx、第 10 章上线演练都会引用本章产物。

## 8.2 选型：SQLite vs MySQL vs PostgreSQL

| 维度 | SQLite | MySQL 8.0 | PostgreSQL |
|---|---|---|---|
| 形态 | 进程内库，一个文件 | 独立 C/S 服务 | 独立 C/S 服务 |
| 并发写入 | 单写者（WAL 缓解但有限） | 好 | 好 |
| 部署成本 | 零 | 中（服务+备份+加固） | 中 |
| 适合场景 | 教学、原型、单机小工具 | 常规生产 Web/业务库 | 复杂查询、JSON/地理、分析型 |
| 本教程用法 | book-insight 数据采集阶段 | 本章主角 | 建议了解，风格与 MySQL 大同小异 |

选型经验法则：**单进程、读多写少、数据在 GB 级以内 → SQLite 完全够用且更简单**；需要多服务共享/高并发写/成熟运维生态 → MySQL 或 PostgreSQL（二者都是优秀选择，PostgreSQL 在复杂类型与标准符合度上口碑更好，招聘市场两者并重）。本书以 MySQL 为主线（Ubuntu 生态中最常见的入门生产库），命令以 8.0 兼容写法为准（9.x 同样适用，个别参数以官方文档为准）。

## 8.3 安装与安全初始化

### 8.3.1 安装

```bash
sudo apt update
sudo apt install mysql-server -y
sudo systemctl enable --now mysql      # 开机自启 + 立刻启动（第 4 章的一步到位写法）
systemctl status mysql
```

预期输出（节选）：

```text
● mysql.service - MySQL 8.0 Database Server
     Loaded: loaded (/usr/lib/systemd/system/mysql.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-11-04 15:00:01 CST; 30s ago
   Main PID: 4821 (mysqld)
```

确认监听地址（本章后面要反复用到）：

```bash
sudo ss -tlnp | grep 3306
```

预期输出：

```text
LISTEN 0 151 127.0.0.1:3306  0.0.0.0:*  users:(("mysqld",pid=4821,fd=25))
```

注意监听在 `127.0.0.1`——Ubuntu 打包默认只监听本机，这是安全默认，后面 8.5 节讨论要不要改。

### 8.3.2 mysql_secure_installation 逐项解释

```bash
sudo mysql_secure_installation
```

这是交互式安全向导，逐项说明（以 MySQL 8.0 的提问顺序为准，个别顺序可能随版本变化）：

| 提问 | 建议回答 | 它在做什么 |
|---|---|---|
| VALIDATE PASSWORD COMPONENT? | N（学习期）或 Y（生产） | 安装密码强度校验组件，强制复杂密码。团队有密码规范时选 Y |
| 密码强度（若上一步 Y） | 按提示选 MEDIUM | 定义长度/字符类要求 |
| Remove anonymous users? | **Y** | 删除无用户名的匿名账户，收掉一个默认漏洞面 |
| Disallow root login remotely? | **Y** | 禁止 root 从非本机连接。root 只该走本机 |
| Remove test database? | **Y** | 删掉默认的 test 库与对应权限 |
| Reload privilege tables? | **Y** | 让以上改动立即生效 |

全部选完预期输出 `All done!`。

### 8.3.3 auth_socket：为什么 root 不用密码就能进

```bash
sudo mysql
```

预期直接进入 `mysql>` 提示符，**没有问任何密码**。这不是配置失误，是 Ubuntu 打包的默认设计：root 账户的认证插件是 **auth_socket**——它校验「发起连接的**操作系统用户**是不是 mysql 账户对应的系统用户」，所以只有 `sudo`（即系统 root）能以数据库 root 身份连本机库。效果：

- 免去 root 密码的保管（没有密码可泄露）；
- 非系统 root 的进程/用户**不可能**冒充数据库 root；
- 副作用：`mysql -u root`（不带 sudo）必然失败，报 `Access denied`——这是正常现象。

业务应用**不使用** root，改用密码登录的普通用户（8.4 节），root 仅留给管理员运维。

## 8.4 建库、建用户与最小化授权

### 8.4.1 为什么是 utf8mb4 而不是「utf8」

MySQL 里的 `utf8` 历史上是**残缺实现**：最多 3 字节，存不了 emoji 与部分生僻字（完整 UTF-8 需要 4 字节）。4 字节的正确实现叫 **utf8mb4**（mb4 = most bytes 4）。所以新库一律显式 `CHARACTER SET utf8mb4`——用户名里有个 emoji 就把写入报成 `Incorrect string value`，是 MySQL 史上最著名的坑。

### 8.4.2 建库与建用户（在 sudo mysql 里执行）

```sql
-- 建库：字符集与排序规则显式声明，不依赖服务器默认值
CREATE DATABASE book_insight
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 建用户：只允许本机连接（@'localhost'），密码用占位符替换
CREATE USER 'bookapp'@'localhost' IDENTIFIED BY '<your-db-password>';

-- 最小化授权：只授 book_insight 一个库的常用 DML 权限
GRANT SELECT, INSERT, UPDATE, DELETE ON book_insight.* TO 'bookapp'@'localhost';
FLUSH PRIVILEGES;   -- MySQL 8.0 中 GRANT 已自动生效，此句为习惯性保险
```

要点：

- `utf8mb4_unicode_ci` 是跨语言排序更准确的通用校对集（MySQL 8.0 默认的 `utf8mb4_0900_ai_ci` 亦可，团队统一即可）；
- **授权最小化**：只给业务必需的四类 DML。不要给 `ALL PRIVILEGES`，更不要给 `ON *.*`——应用被拖库时的损失边界由此决定。需要建表再单独 `GRANT CREATE ON book_insight.*`；
- `'bookapp'@'localhost'` 限定只能本机连。将来上第二台应用服务器再按需 `'bookapp'@'10.0.0.%'`（内网网段），永远不要 `'%'`；
- 引号注意：MySQL 里标识符用反引号、字符串用单引号，用户名的 `'user'@'host'` 两段都要引。

验证：

```bash
mysql -u bookapp -p -h 127.0.0.1 book_insight
```

输入密码后执行 `SELECT USER(), CURRENT_USER();` 预期返回 `bookapp@localhost`。

### 8.4.3 用户管理与密码策略

```sql
-- 改密码（MySQL 8.0 写法）
ALTER USER 'bookapp'@'localhost' IDENTIFIED BY '<new-db-password>';

-- 改认证插件（如需从旧 caching_sha2_password 换 mysql_native_password 兼容老驱动时）
ALTER USER 'bookapp'@'localhost'
  IDENTIFIED WITH caching_sha2_password BY '<your-db-password>';

-- 锁定/解锁账户（离职或疑似泄露时先锁再查）
ALTER USER 'bookapp'@'localhost' ACCOUNT LOCK;
ALTER USER 'bookapp'@'localhost' ACCOUNT UNLOCK;

-- 查看已有用户与权限
SELECT user, host FROM mysql.user;
SHOW GRANTS FOR 'bookapp'@'localhost';
```

密码策略在 8.3.2 选过 Y 的话，由 validate_password 组件强制；查看其状态：`SHOW VARIABLES LIKE 'validate_password%';`。密码只放 `.env`/环境变量，**绝不写进代码与 git**（呼应仓库密钥红线，第 7 章 `.env` 方案通用）。

## 8.5 远程访问：bind-address 与 SSH 隧道

### 8.5.1 原则先行

MySQL 配置文件在 `/etc/mysql/` 层级（主配置 `my.cnf` 引入 `conf.d/` 与 `mysql.conf.d/`），监听地址在 `mysql.conf.d/mysqld.cnf`：

```bash
grep -n "bind-address" /etc/mysql/mysql.conf.d/mysqld.cnf
```

预期输出：

```text
bind-address            = 127.0.0.1
```

改成 `0.0.0.0` 再配合安全组放行 3306，就能从任何地方直连——**本教程明确不建议这么做**：公网 3306 等于把数据库暴露给全网扫描器（撞库、漏洞利用、勒索删除都是真实高频事件）。即使 MySQL 8 默认强密码认证，「少一个暴露面」永远是对的。

### 8.5.2 推荐方案：保持只本机 + SSH 隧道

本机 GUI 工具（如 DBeaver、Navicat、DataGrip）想连服务器上的库时，走 **SSH 隧道**：连接配置里填 SSH 主机信息，数据库地址填 `127.0.0.1:3306`——工具经 SSH 登录服务器后，从服务器本机转连 3306，流量全程加密，3306 对公网保持不可见。各 GUI 工具的 SSH 标签页都支持此模式，纯命令行验证：

```bash
# 本地执行：把本地 13306 转发到服务器的 127.0.0.1:3306
ssh -N -L 13306:127.0.0.1:3306 myserver
# 另开终端，验证经隧道可连：
mysql -h 127.0.0.1 -P 13306 -u bookapp -p book_insight
```

`-N` 只转发不执行远程命令，`-L 本地端口:目标:目标端口` 是转发定义。**什么时候才真要改 bind-address？** 仅当存在第二台内网应用服务器必须直连数据库时：改绑到内网网卡（`bind-address = 10.0.0.5`，即服务器内网 IP）、`CREATE USER ...@'10.0.0.%'` 限内网网段、安全组只对内网放行 3306——这三件事缺一不可。具体参数语义以 MySQL 官方文档为准。

## 8.6 备份与恢复：mysqldump

### 8.6.1 三种粒度

```bash
# 单库备份（--single-transaction：InnoDB 下获得一致性快照且不锁表）
mysqldump -u bookapp -p --single-transaction book_insight > book_insight.sql

# 全库备份
mysqldump -u root -p --single-transaction --all-databases > all.sql

# 单表备份
mysqldump -u bookapp -p book_insight books > books.sql

# 生产标配：直接管道进 gzip（体积降 80%+）
mysqldump -u bookapp -p --single-transaction book_insight | gzip > book_insight.sql.gz
```

`-p` 后不加空格紧跟密码可直接传（`-p'<your-db-password>'`），但**密码进 shell 历史与进程列表有泄露风险**，交互场景就分开写，脚本里用 `--defaults-extra-file`（见 8.6.2 脚本）。

### 8.6.2 定时备份脚本（完整可运行）

`~/scripts/backup_mysql.sh`（接第 6 章 6.7 例一的思路，落成 MySQL 版）：

```bash
#!/usr/bin/env bash
# 每日 MySQL 备份：文件名带日期、gzip 压缩、保留 7 天
set -euo pipefail

DB_NAME="book_insight"
BACKUP_DIR="/home/ubuntu/backups/mysql"
KEEP_DAYS=7
STAMP="$(date +%F_%H%M)"
OUT="${BACKUP_DIR}/${DB_NAME}_${STAMP}.sql.gz"

# 凭据放受保护的独立配置文件，不进代码、不进命令行
CRED_FILE="/home/ubuntu/.mybackup.cnf"
if [[ ! -f "$CRED_FILE" ]]; then
    echo "[backup] 缺少凭据文件 $CRED_FILE" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "[backup] start $(date '+%F %T') db=$DB_NAME"
mysqldump --defaults-extra-file="$CRED_FILE" \
          --single-transaction --routines --triggers \
          "$DB_NAME" | gzip > "$OUT"

# 生成后校验非空（防「备份成功」了 0 字节文件的假象）
if [[ ! -s "$OUT" ]]; then
    echo "[backup] 备份文件为空，疑似失败: $OUT" >&2
    exit 1
fi

find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +"$KEEP_DAYS" -print -delete
echo "[backup] done $(date '+%F %T') file=$OUT size=$(du -h "$OUT" | cut -f1)"
```

凭据文件 `~/.mybackup.cnf`（`chmod 600`，属主你自己）：

```ini
[client]
user=bookapp
password=<your-db-password>
host=127.0.0.1
```

注册 cron（第 4 章五字段：每天 3 点）：

```bash
chmod +x ~/scripts/backup_mysql.sh
crontab -e
```

```text
0 3 * * * /home/ubuntu/scripts/backup_mysql.sh >> /home/ubuntu/backups/mysql/backup.log 2>&1
```

### 8.6.3 恢复演练（不看一次恢复，不算会备份）

```bash
# 解压并恢复到同名库
gunzip < backups/mysql/book_insight_2026-11-04_0300.sql.gz | mysql -u bookapp -p book_insight

# 恢复到新库（更安全的演练姿势，不碰生产库）
mysql -u bookapp -p -e "CREATE DATABASE book_insight_restore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
gunzip < backups/mysql/book_insight_2026-11-04_0300.sql.gz | mysql -u bookapp -p book_insight_restore
mysql -u bookapp -p -e "SELECT COUNT(*) FROM book_insight_restore.books;"
```

**验收标准：恢复后 `COUNT(*)` 与原库一致**。把这条验证写进第 10 章上线清单——「有备份」与「备份可恢复」是两回事，未经演练的备份等于没有。

## 8.7 基础运维：看库、看执行计划、开慢查询日志

```sql
SHOW DATABASES;                  -- 看所有库
USE book_insight;
SHOW TABLES;                     -- 看库内表
DESCRIBE books;                  -- 看表结构
SHOW CREATE TABLE books\G        -- 看建表语句（含字符集/索引，\G 竖排输出）
SHOW VARIABLES LIKE 'character_set_server';
```

### EXPLAIN 初见

给将来优化 SQL 打底——EXPLAIN 展示「这条 SQL 打算怎么执行」：

```sql
EXPLAIN SELECT title, price FROM books WHERE title LIKE '%light%';
```

预期输出（列有取舍）：

```text
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
| id | select_type | table | type | possible_keys | key  | key_len | ref  | rows | Extra       |
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
|  1 | SIMPLE      | books | ALL  | NULL          | NULL | NULL    | NULL |  500 | Using where |
+----+-------------+-------+-------+---------------+------+---------+------+------+-------------+
```

两个先学会看的列：`type`——`ALL` 是全表扫描（数据大时是警讯），`ref`/`range` 说明走了索引；`key`——实际用上的索引名。入门结论：**看到大表 `type=ALL` 且 `rows` 很大，优先考虑给 WHERE/ORDER BY 的列建索引**。深入优化超出本章范围，遇实际慢查询再查官方手册。

### 慢查询日志

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

追加：

```ini
slow_query_log          = 1
slow_query_log_file     = /var/log/mysql/slow.log
long_query_time         = 1
```

```bash
sudo mkdir -p /var/log/mysql && sudo chown mysql:mysql /var/log/mysql
sudo systemctl restart mysql
sudo mysql -e "SHOW VARIABLES LIKE 'slow_query_log%';"
```

执行超过 1 秒的语句会记录到 `slow.log`，用 `sudo tail -f /var/log/mysql/slow.log` 观察。注意改配置文件需重启生效（运行时临时开启用 `SET GLOBAL slow_query_log = 'ON';`，重启后失效），属主不对会导致日志写不出来——上面的 chown 就是防这个。

## 8.8 与 Python 对接：pymysql 与参数绑定

### 8.8.1 安装与连接

```bash
mkdir -p /tmp/mysql-lab && cd /tmp/mysql-lab
uv venv && source .venv/bin/activate
uv pip install pymysql
```

`conn_test.py`（凭据从环境变量读取，呼应 `.env` 方案）：

```python
#!/usr/bin/env python
"""pymysql 连接测试：凭据走环境变量，绝不硬编码。"""
from __future__ import annotations

import os

import pymysql

conn = pymysql.connect(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ.get("DB_NAME", "book_insight"),
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)
with conn:
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS v, DATABASE() AS db")
        print(cur.fetchone())
```

```bash
DB_USER=bookapp DB_PASSWORD='<your-db-password>' python conn_test.py
```

预期输出：

```text
{'v': '8.0.4x', 'db': 'book_insight'}
```

### 8.8.2 参数绑定：硬规范

**凡 SQL 里出现外部输入（用户参数、爬虫数据、URL query），一律参数绑定，禁止字符串拼接**。pymysql 的占位符是 `%s`：

```python
# 正确：占位符 %s + 参数元组。值由驱动转义，任何输入都只是数据
def search_books(cur: pymysql.cursors.DictCursor, keyword: str) -> list[dict[str, object]]:
    sql = "SELECT id, title, price FROM books WHERE title LIKE %s LIMIT %s"
    cur.execute(sql, (f"%{keyword}%", 20))     # 注意 LIKE 的通配符写在参数值里
    return cur.fetchall()
```

下面是**反面案例，仅用于识别，禁止在任何代码中出现**：

> **【危险】SQL 注入反例（禁止模仿）**
>
> ```python
> # 危险！把用户输入直接拼进 SQL 字符串——禁止这样做
> keyword = request.query_params.get("keyword", "")
> sql = "SELECT id, title FROM books WHERE title LIKE '%" + keyword + "%'"   # 反例
> ```
>
> 攻击者传 `keyword=' UNION SELECT user(), version() -- `，拼出的 SQL 就变成攻击者书写的语句：可越权读任意表（含 mysql.user）、可构造删库语句。参数绑定下同样的输入只会被当作一个普通字符串去匹配书名——这就是「数据与代码分离」的含义。仓库评审中见到拼接 SQL 一律打回。

批量插入同样绑定：`cur.executemany("INSERT INTO books(title, price) VALUES (%s, %s)", rows)`。连接管理建议：短脚本「即开即关」如上；长期服务用连接池或框架 ORM（SQLAlchemy 2.0 风格，本仓库数据分析与后端章节会统一讲解）。

## 常见坑与排查（Troubleshooting）

| 报错/现象 | 原因 | 解决办法 |
|---|---|---|
| `Access denied for user 'root'@'localhost'` | Ubuntu 的 root 走 auth_socket | 用 `sudo mysql` 进入；业务应用用普通密码用户 |
| `ERROR 1698 (28000): Access denied for user 'root'@'localhost'`（不带 sudo 时） | 同上 | 同上，属预期行为 |
| 写入 emoji 报 `Incorrect string value: '\xF0\x9F...'` | 库/表/连接字符集是残缺 utf8 | 三层都确认 utf8mb4：建库、建表、pymysql 的 charset 参数 |
| `Can't connect to MySQL server on '<外网IP>'` | 服务只监听 127.0.0.1（默认） | 这是安全默认；改走 SSH 隧道，勿轻易改 bind-address |
| `Host 'x.x.x.x' is not allowed to connect` | 用户是 @'localhost'，无远程权限 | 按需建 `'user'@'内网网段'`，不要 `'%'` |
| 备份文件 0 字节但 cron 显示成功 | 管道中 mysqldump 失败被 gzip 吞掉 | 脚本里 `-s` 判空 + `pipefail`（本章脚本已内置） |
| `ERROR 1044 (42000): Access denied ... to database` | 用户权限不是最小化给够了 | `SHOW GRANTS` 核对，按需补该库的对应权限 |
| 慢日志不增长 | 配置没重启生效或日志文件属主错 | `SHOW VARIABLES LIKE 'slow_query%'` 核对；chown mysql:mysql |
| `error: command 'gcc' failed`（装驱动时） | 缺编译依赖 | `sudo apt install build-essential python3-dev default-libmysqlclient-dev pkg-config`，或换纯 Python 的 pymysql |

## 动手练习

1. **完整走一遍安装与授权**：安装 MySQL → secure installation（按 8.3.2 表格逐项选）→ 建 `book_insight` 库（utf8mb4）→ 建 bookapp 最小授权 → 用 bookapp 连入验证 `SHOW GRANTS`。
   <details><summary>提示</summary>验收标准：`mysql -u bookapp -p` 能进、`SHOW DATABASES` 只看到 book_insight 和 information_schema、对 mysql 库的任何读写被拒绝。</details>
2. **备份-破坏-恢复闭环**：手动触发 backup_mysql.sh → 在库里故意 `DELETE FROM books LIMIT 1;` → 用该备份恢复到 `book_insight_restore` → 比对两个库的 `COUNT(*)`。
   <details><summary>提示</summary>这是「演练出来的备份可信度」练习；注意恢复用的是 --defaults-extra-file 凭据或交互输密码。</details>
3. **SSH 隧道远程管理**：在你本地机器建隧道连服务器 MySQL，用 GUI 工具或命令行查 `SHOW TABLES`，全程确认 `ss -tlnp | grep 3306` 仍只有 127.0.0.1。
   <details><summary>提示</summary>`ssh -N -L 13306:127.0.0.1:3306 myserver`；GUI 里主机填 127.0.0.1 端口 13306。</details>
4. **注入对照实验**：在 /tmp/mysql-lab 分别实现 8.8.2 的正确版与反例版查询，用 `keyword=' UNION SELECT user(), 1 -- ` 各试一次，对比返回结果，把现象写进笔记。
   <details><summary>提示</summary>绑定版返回 0 行（把攻击串当书名匹配）；反例版返回数据库用户名——亲眼见过才真正敬畏。实验完立刻删除反例代码。</details>

## 小结与自检清单

- [ ] 我能按项目规模给出 SQLite/MySQL/PostgreSQL 的选型理由
- [ ] 我安装的 MySQL 处于 enabled+running，且监听在 127.0.0.1
- [ ] 我知道 auth_socket 的原理，管理员走 sudo mysql、应用走密码用户
- [ ] 我的库用 utf8mb4，能解释为什么「utf8」存不了 emoji
- [ ] 用户权限是最小化 DML，host 限定 localhost/内网网段，绝无 '%'
- [ ] 3306 没有出现在安全组与 UFW 的放行列表里，远程用 SSH 隧道
- [ ] 每日备份 cron 在跑，备份带日期、gzip 压缩、保留 7 天，且**我演练过恢复**
- [ ] 我的 Python 代码全部参数绑定，能当场指出拼接 SQL 的注入路径
- [ ] 我会看 EXPLAIN 的 type/key 列，慢查询日志已开启

## 延伸阅读

- [MySQL 8.0 官方手册（中文）](https://dev.mysql.com/doc/refman/8.0/zh/)——安装、账户管理、备份恢复的权威参考（官方中文版）。
- [MySQL 备份与恢复类型](https://dev.mysql.com/doc/refman/8.0/en/backup-types.html)——mysqldump/物理备份/快照的策略对比。
- [mysqldump 手册页](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)——--single-transaction 等关键参数的精确语义。
- [Ubuntu Server 文档：MySQL](https://documentation.ubuntu.com/server/how-to/databases/install-mysql/)——Ubuntu 打包默认行为（含 auth_socket）的官方说明。
- [OWASP SQL 注入速查表](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)——参数绑定为何有效的权威论述。
- [PyMySQL 官方文档](https://pymysql.readthedocs.io/)——connect 参数、paramstyle 与示例。
