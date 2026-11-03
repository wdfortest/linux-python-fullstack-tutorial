# 第 6 章 · Shell 脚本基础与自动化

> 本章配套代码：三个实战脚本建议保存到服务器 `~/scripts/`（`backup_dir.sh`、`check_service.sh`、`deploy.sh`），练习的临时文件放 `/tmp/shell-lab/`；它们会直接被第 8 章的定时备份与第 10 章的上线演练引用。
> 建议学习时长：约 5 小时

## 学习目标

学完本章，你能够：

1. 解释 shebang 与两种执行方式（`bash x.sh` vs `./x.sh`）的区别；
2. 正确使用变量与三种引号，写出含命令替换 `$(...)` 的表达式；
3. 用 `if`（含 `[ ]` 与 `[[ ]]`、`-f -d -z`、字符串与数字比较）和 `for/while` 完成分支与循环；
4. 在脚本开头统一写上 `set -euo pipefail`，并能逐个字母解释它防了什么错；
5. **独立写出三个生产级脚本**：按日期批量备份、服务健康检查自愈、一键部署骨架。

## 6.1 前置知识 / 本章地位

前五章你已经在终端敲过上百条命令。Shell 脚本就是把「人肉敲的命令序列」固化成文件——它是**服务器自动化的第一生产力**：备份、部署、健康检查、日志清理，全是几十行的 bash。

对 Python 开发者说句公道话：复杂逻辑用 Python 写更清晰，**shell 脚本的定位是「粘合系统命令」**——它调用 systemctl、curl、mysqldump 这些系统工具比 Python 的 subprocess 直接得多，也是服务器上人人能读懂的公共语言。本教程后续章节的运维脚本全部用 bash，达到「够用且健壮」即可，不追求炫技。

前置：第 2 章的管道/重定向/权限、第 4 章的 systemctl，本章直接使用。

## 6.2 shebang 与执行方式

### 6.2.1 第一个脚本

```bash
mkdir -p /tmp/shell-lab && cd /tmp/shell-lab
nano hello.sh
```

```bash
#!/usr/bin/env bash
# 我的第一个脚本
echo "hello, $(whoami) on $(hostname)"
```

第一行 `#!/usr/bin/env bash` 叫 **shebang**：`#!` 后面跟解释器路径。内核执行脚本时读这一行，把文件交给指定解释器。用 `/usr/bin/env bash` 而不是写死 `/bin/bash`，是为了让脚本在 PATH 里找 bash、跨发行版可移植（macOS 与 Ubuntu 都适用，本仓库项目脚本也统一这样写）。

### 6.2.2 两种执行方式的本质区别

```bash
bash hello.sh      # 方式一：把文件当参数传给 bash，新开一个子进程解释
chmod +x hello.sh  # 方式二：赋予执行位
./hello.sh         #        直接执行，由 shebang 决定解释器
```

两种方式都会**新开一个子 shell** 运行，因此有两条重要推论：

1. 脚本里 `cd` 改变的目录、定义的变量，**不会影响**你的当前终端；
2. 方式二更「正规」：`./hello.sh` 对脚本作者的表达是「这是一个可执行程序」，且 shebang 生效。给脚本补执行位是 `chmod +x`（第 2 章）最常见的用途。

第三种容易踩坑的方式：`source hello.sh`（或 `. hello.sh`）——**在当前 shell 里**逐行执行，变量和 `cd` 会污染当前终端，一般只用于加载配置类文件（如 `source ~/.bashrc`）。

## 6.3 变量、引号与命令替换

### 6.3.1 变量基本法

```bash
name="book-insight"        # 赋值：等号两边【绝不能有空格】
echo "$name"               # 使用：$name 或 ${name}
echo "项目目录: /opt/${name}"   # ${} 花括号在紧跟其他字符时必需
```

`name = "x"`（带空格）会报 `command not found`——bash 把 `name` 当成了命令。这是从 Python 过来最常犯的错。

只读与环境变量：

```bash
readonly APP_VERSION="1.0.0"    # 只读变量，再次赋值报错
echo "$HOME $USER $PATH"        # 环境变量已内置
```

约定：脚本内部变量小写，**导出的环境变量、常量全大写**。

### 6.3.2 引号三规则（重点）

| 写法 | 行为 | 例子 |
|---|---|---|
| 双引号 `"..."` | **变量会展开**，保留空格 | `echo "目录是 $HOME"` |
| 单引号 `'...'` | **一切按字面**，不展开任何东西 | `echo '$HOME'` → `$HOME` |
| 反引号 `` `...` `` | 命令替换（旧写法，**已被 `$(...)` 取代**） | 尽量不用 |

黄金法则：**涉及变量的字符串一律用双引号**。不加引号时，含空格的值会被拆成多个词（word splitting）、通配符会被展开——第 2 章 `rm -rf` 事故的根源之一就在这：

```bash
DIR="/tmp/my dir"
rm -rf $DIR/app      # 灾难：被拆成 rm -rf "/tmp/my" 和 "dir/app"
rm -rf "$DIR/app"    # 正确
```

### 6.3.3 命令替换 $(...)

把命令的**标准输出**捕获成一个值：

```bash
today=$(date +%F)                 # 2026-11-04
count=$(ls /var/log/*.log 2>/dev/null | wc -l)
echo "今天是 $today，日志文件 $count 个"
commit=$(git -C /opt/book-insight rev-parse --short HEAD)   # 当前 commit 短哈希，部署脚本记录版本用
```

旧写法反引号 `` `date +%F` `` 功能相同，但嵌套时需转义、极易看错，新代码一律 `$(...)`。

### 6.3.4 位置参数与特殊变量

脚本接收参数的方式：

```bash
#!/usr/bin/env bash
echo "脚本名: $0"
echo "第 1 个参数: ${1:-<未提供>}"     # :- 提供默认值，防止未传参时空值扩散
echo "参数个数: $#"
echo "全部参数: $@"
```

```bash
bash args.sh alpha beta
```

预期输出：

```text
脚本名: args.sh
第 1 个参数: alpha
参数个数: 2
全部参数: alpha beta
```

必传参数的强校验写法：`: "${1:?用法: $0 <必须参数>}"`——缺参直接报错退出（见 6.6 实战脚本）。

## 6.4 条件判断

### 6.4.1 if 的骨架与 [ ] 与 [[ ]]

```bash
if [ "$count" -gt 10 ]; then
    echo "日志偏多"
elif [ "$count" -eq 0 ]; then
    echo "没有日志"
else
    echo "日志数量正常"
fi
```

语法硬规则：`[` 其实是一个命令（test 的别名），所以**方括号内侧必须有空格**；字符串变量**必须带引号**（空字符串不加引号会让 `[` 少一个参数而报错）。

双中括号 `[[ ]]` 是 bash 的增强版判断（不是 POSIX 兼容，但服务器脚本都是 bash，放心用）：变量**不需要**引号也不会拆词、支持 `&&` `||`、支持正则匹配：

```bash
if [[ $file == *.log && -s $file ]]; then   # 文件名以 .log 结尾且非空
    echo "$file 是非空日志"
fi
if [[ "$url" =~ ^https:// ]]; then          # =~ 正则匹配
    echo "https 地址"
fi
```

本书脚本统一用 `[[ ]]`，但仍给变量加引号以保持习惯一致。

### 6.4.2 常用判断符速查

| 类别 | 写法 | 含义 |
|---|---|---|
| 文件 | `-f $path` | 存在且是普通文件 |
| | `-d $path` | 存在且是目录 |
| | `-e $path` | 存在（不分类型） |
| | `-s $path` | 存在且非空 |
| | `-x $path` | 可执行 |
| 字符串 | `-z "$s"` | 空字符串（zero） |
| | `-n "$s"` | 非空字符串 |
| | `"$a" = "$b"` / `"$a" != "$b"` | 相等 / 不等 |
| 数字 | `-eq -ne -gt -ge -lt -le` | 等/不等/大于/大于等于/小于/小于等于 |

数字比较也可以用算术式：`(( count > 10 ))`，双括号内是 C 风格算术，无需 `$` 前缀。

### 6.4.3 按命令成败分支：if 直接接命令

bash 的 if 判断的核心是「退出码是否为 0」——**不只是 test，任何命令都行**：

```bash
if curl -fsS --max-time 5 http://127.0.0.1:8000/health > /dev/null; then
    echo "服务健康"
else
    echo "服务异常"
fi
if grep -q "ERROR" "$log"; then    # -q 不输出只返回成败
    echo "发现错误"
fi
```

这是 shell 与 Python 哲学的差异点：bash 用「退出码」当布尔值，0 为真。记住它，6.6 的健康检查脚本就水到渠成。

## 6.5 循环与函数

### 6.5.1 for 与 while

```bash
# for：遍历列表
for svc in nginx book-insight; do
    systemctl is-active --quiet "$svc" && echo "$svc 运行中" || echo "$svc 已停止"
done

# for：按范围/步进
for i in {1..3}; do echo "第 $i 次重试"; done

# while：逐行读文件（最不易出错的姿势：while read 放在重定向右侧）
while IFS= read -r line; do
    echo "处理: $line"
done < urls.txt

# 无限循环 + sleep：轮询守护的雏形
while true; do
    date +%T
    sleep 5
done
```

`IFS= read -r` 的两个修饰：`IFS=` 防止行首尾空白被吞，`-r` 防止反斜杠被转义——逐行读文件的标准模板，照抄即可，深究见 `help read`。注意变量作用在子 shell 的问题：`cat file | while read ...` 管道右侧是子 shell，循环内改的变量出循环就丢；用上面的 `done < file` 重定向写法则在当前 shell，无此坑。

### 6.5.2 函数与 exit code

```bash
log() {
    echo "[$(date '+%F %T')] $*" >> "$LOG_FILE"
}

check_port() {                  # 函数内可用 $1 $2 接参数（与脚本级 $1 互不干扰）
    local port="$1"             # local：变量只在函数内有效，好习惯
    ss -tln | grep -q ":${port} "
}

if check_port 8000; then
    log "8000 端口有人监听"
fi
```

函数名即命令，`check_port 8000` 的返回值就是函数内最后一个命令的退出码；要显式返回用 `return 0/1`（0 成功）。

**脚本级退出码**：`exit 0` 成功、`exit 1` 失败。cron、systemd、CI 都靠退出码判断你的脚本成败，**脚本必须对失败诚实**：

```bash
if [[ ! -f "$CONF" ]]; then
    echo "缺少配置文件 $CONF" >&2    # 错误信息走 stderr（>&2）
    exit 1
fi
```

上一条命令的退出码存在 `$?`：

```bash
curl -fsS --max-time 3 http://127.0.0.1:8000/ > /dev/null
echo "退出码: $?"      # 0 或非 0
```

## 6.6 set -euo pipefail：防呆三件套（重点）

脚本第一行 shebang 之下，永远先写：

```bash
set -euo pipefail
```

它由三个独立开关组成，每个都堵一类「静默失败」：

- **`-e`（errexit）**：任何命令失败（退出码非 0）立即终止脚本。没有它，bash 默认「失败了继续跑下一行」——第 1 步 mkdir 失败，后面照样往不存在的目录写文件，等发现时已写入半途垃圾。注意例外：`if`/`while` 条件中的命令、`&&`/`||` 链中非末位的失败不会触发退出，正好符合直觉。
- **`-u`（nounset）**：使用**未定义变量**立即报错退出。没有它，`$CONFIG_PATH` 打错成 `$CONFIG_PATCH` 会静默变成空字符串，逻辑悄悄走偏——这是最难排查的一类 bug。
- **`-o pipefail`**：让管道的退出码取「**第一个失败者**」。默认情况下管道退出码只看最后一个命令：`grep "关键行" app.log | wc -l` 里 grep 失败（没匹配）时默认返回 wc 的 0，`-e` 根本不知道前面错了；pipefail 补上这个洞。

三件套不是 bash 默认行为的原因是历史兼容，但**新脚本没有理由不开**。本书所有脚本（包括后续章节）都以此开头。两个配套技巧：

```bash
# 1) 明确允许失败的命令，写清兜底，避免 -e 误杀：
grep -q "obsolete" "$CONF" || true      # 预期可能不匹配，不算失败
systemctl is-active --quiet myapp || systemctl restart myapp

# 2) 用 trap 在退出时收尾（无论成功失败都会执行）：
trap 'echo "脚本结束于 $(date +%T)"' EXIT
```

## 6.7 实战脚本三例（完整可运行）

### 例一：批量备份目录并按日期命名

需求：把 `/opt/book-insight/data`（含 SQLite 库）备份到 `~/backups/`，文件名带日期，自动清理 7 天前的旧备份。

`~/scripts/backup_dir.sh`：

```bash
#!/usr/bin/env bash
# 批量备份目录并按日期命名，保留最近 7 天
set -euo pipefail

# ---- 可调参数 ----
SRC_DIR="/opt/book-insight/data"           # 要备份的目录
BACKUP_ROOT="/home/ubuntu/backups"         # 备份存放根目录
KEEP_DAYS=7                                # 保留天数
# -----------------

if [[ ! -d "$SRC_DIR" ]]; then
    echo "[backup] 源目录不存在: $SRC_DIR" >&2
    exit 1
fi

STAMP="$(date +%F_%H%M)"                   # 2026-11-04_0300
DEST="${BACKUP_ROOT}/data_${STAMP}.tar.gz"
mkdir -p "$BACKUP_ROOT"

echo "[backup] 开始: $SRC_DIR -> $DEST"
tar -czf "$DEST" -C "$(dirname "$SRC_DIR")" "$(basename "$SRC_DIR")"
echo "[backup] 完成: $(du -h "$DEST" | cut -f1)"

# 清理过期备份
find "$BACKUP_ROOT" -name "data_*.tar.gz" -mtime +"$KEEP_DAYS" -print -delete
echo "[backup] 已清理 ${KEEP_DAYS} 天前的旧备份"
```

要点：`tar -czf` 打包压缩（`-C` 指定从父目录打包，压缩包内路径不带绝对前缀，解压更可控）；`find -print -delete` 删除前先打印删除了谁，留审计痕迹。手动跑一次：

```bash
chmod +x ~/scripts/backup_dir.sh
~/scripts/backup_dir.sh
```

预期输出：

```text
[backup] 开始: /opt/book-insight/data -> /home/ubuntu/backups/data_2026-11-04_0312.tar.gz
[backup] 完成: 1.2M
[backup] 已清理 7 天前的旧备份
```

### 例二：服务健康检查自愈脚本

需求：curl 探活，失败则重启 systemd 服务并记日志——cron 每分钟跑一次（第 4 章 4.6.3 的姿势）。

`~/scripts/check_service.sh`：

```bash
#!/usr/bin/env bash
# 用法: check_service.sh <健康检查URL> <systemd服务名>
# 失败则重启服务并写 syslog（journalctl -t healthcheck 查看）
set -euo pipefail

: "${1:?用法: $0 <URL> <服务名>}"
: "${2:?缺少服务名}"
URL="$1"
SERVICE="$2"
TAG="healthcheck"

# 探活：-f 让 curl 在 HTTP>=400 时退出码非 0；--max-time 防止挂死
if curl -fsS --max-time 5 "$URL" > /dev/null 2>&1; then
    exit 0                                  # 健康，安静退出（cron 里成功就该安静）
fi

logger -t "$TAG" "探活失败: $URL，正在重启 $SERVICE"
echo "[healthcheck] $(date '+%F %T') 探活失败: $URL，重启 $SERVICE" >> "${HOME}/logs/healthcheck.log"

# systemctl restart 需要 root：本脚本由 sudo crontab 调度，
# 或为当前用户配置 sudoers 白名单（见第 3 章 sudoers.d 示例）
sudo systemctl restart "$SERVICE"
sleep 3

if curl -fsS --max-time 5 "$URL" > /dev/null 2>&1; then
    logger -t "$TAG" "重启成功: $SERVICE"
else
    logger -t "$TAG" "重启后仍异常: $SERVICE，请人工介入"
    exit 1
fi
```

要点：`: "${1:?...}"` 缺参即死，防呆三件套的补刀；`logger` 把事件写进 syslog，`journalctl -t healthcheck` 随时可查，比裸文件日志更规范；重启后再探一次，区分「自愈成功」与「需要人工」。注册 cron（`sudo crontab -e`，用 root 跑免 sudo 密码问题）：

```text
* * * * * /home/ubuntu/scripts/check_service.sh http://127.0.0.1:8000/ pydemo
```

### 例三：一键部署脚本骨架

需求：拉最新代码 → 重建虚拟环境依赖 → 重启服务，一条命令完成发布（第 7 章会填入 uv 细节，第 10 章扩展为多版本发布）。

`~/scripts/deploy.sh`：

```bash
#!/usr/bin/env bash
# 一键部署骨架：git pull -> 更新依赖 -> systemd 重启 -> 健康检查
set -euo pipefail

APP_DIR="/opt/book-insight"
SERVICE="book-insight"
HEALTH_URL="http://127.0.0.1:8000/health"
LOG="/home/ubuntu/logs/deploy.log"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

cd "$APP_DIR"

log "1/4 记录当前版本"
OLD_COMMIT="$(git rev-parse --short HEAD)"
log "   当前: $OLD_COMMIT"

log "2/4 拉取代码"
git fetch --all --prune
git reset --hard origin/main
NEW_COMMIT="$(git rev-parse --short HEAD)"
if [[ "$OLD_COMMIT" == "$NEW_COMMIT" ]]; then
    log "   已是最新 ($NEW_COMMIT)，继续执行依赖与服务刷新"
fi

log "3/4 同步依赖（uv，见第 7 章）"
# uv sync --frozen          # 有 uv.lock 时用冻结模式，保证依赖与锁定一致
# 若暂未引入 uv，用 venv + pip 的等价两行：
# "$APP_DIR/.venv/bin/pip" install -r requirements.txt

log "4/4 重启服务并健康检查"
sudo systemctl restart "$SERVICE"
sleep 3
if curl -fsS --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
    log "部署成功: $OLD_COMMIT -> $NEW_COMMIT"
else
    log "部署后健康检查失败！请立即检查: journalctl -u $SERVICE -n 50"
    exit 1
fi
```

要点：每次发布记录新旧 commit（出问题能立刻知道「上了什么版本」）；健康检查失败时 exit 1 并指路 journalctl，让失败可追查；`sudo systemctl restart` 同样依赖 sudoers 白名单或以 root 调度。这 60 行骨架覆盖了部署脚本的全部骨架关节，第 10 章在此基础上加「发布目录 + 软链接」升级成可回滚的蓝绿方案。

### 6.7.4 shellcheck：脚本静态检查

写完脚本，用 shellcheck 扫一遍——它专抓 bash 的经典暗坑（未加引号的变量、被掩盖的失败、无用 cat 等）：

```bash
sudo apt install shellcheck -y
shellcheck ~/scripts/deploy.sh
```

预期输出（有问题时，示例）：

```text
In deploy.sh line 12:
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
        ^-- SC2086: Double quote to prevent globbing and word splitting.
```

每条提示都带 Wiki 链接解释为什么。**把 shellcheck 当脚本的 pytest**：CI 里跑、零警告再上线。本书脚本的写法（引号、set 三件套、绝对路径）基本就是对 shellcheck 规则的提前遵守。

## 常见坑与排查（Troubleshooting）

| 报错/现象 | 原因 | 解决办法 |
|---|---|---|
| `command not found` 但命令明明存在 | 赋值时等号两边有空格；或 PATH 缺失（cron 环境） | 去空格；cron 里用绝对路径 |
| `[: missing ]` 或 `unary operator expected` | 方括号内侧缺空格；变量为空且未加引号 | `[ "$x" = "y" ]`；变量恒加双引号 |
| 脚本手动能跑，cron 里不行 | cron 的 PATH/环境变量极简 | 脚本内全部绝对路径，自设 PATH；先手动以 `env -i` 模拟 |
| Windows 编辑过的脚本报 `$'\r': command not found` | CRLF 换行符 | `sed -i 's/\r$//' 脚本`；编辑器设 LF |
| `-e` 下脚本莫名中断 | 预期失败的命令没兜底 | 失败是预期时接 `|| true` 或放进 if 条件 |
| 管道失败但脚本继续跑 | 没开 pipefail，退出码只看最后一个命令 | `set -euo pipefail` |
| 循环里改的变量出了循环就丢 | 管道右侧是子 shell | 改用 `done < file` 重定向写法 |
| `sudo` 在脚本里卡住要密码 | 非交互环境无法输密码 | sudoers 白名单精确放行（第 3 章）或用 root crontab |

## 动手练习

1. **改造备份脚本**：给 `backup_dir.sh` 加参数支持——`backup_dir.sh <源目录>`，不传参时报错退出并打印用法；再让 KEEP_DAYS 可被第 2 个参数覆盖。
   <details><summary>提示</summary>用 `: "${1:?...}"` 校验；第 2 参数用 `KEEP_DAYS="${2:-7}"`（:- 默认值语法）。</details>
2. **健壮性对照实验**：复制一份去掉 `set -euo pipefail` 的 deploy.sh，故意把 APP_DIR 改错，观察两个版本各自「失败到哪一步」——体会三件套的价值。
   <details><summary>提示</summary>无三件套版本会带着错误路径继续跑完并「假成功」。对照两份输出，把体会写进笔记。</details>
3. **写一个「日志摘要」脚本**：`log_digest.sh <日志文件>` 输出该文件今天新增的 ERROR 行数、出现次数最多的三个错误消息。
   <details><summary>提示</summary>核心流水线 `grep ERROR "$1" | sort | uniq -c | sort -rn | head -3`；先用 shellcheck 自检。</details>
4. **接入 cron 并验收**：把 check_service.sh 挂上 cron 每分钟执行，人为 `sudo systemctl stop pydemo`，等两分钟，验证服务被自动拉起且 `journalctl -t healthcheck` 有完整记录。
   <details><summary>提示</summary>用 `sudo crontab -e` 注册；验收标准：stop 后服务在 2 分钟内恢复 active，日志里有「探活失败→重启成功」两条。</details>

## 小结与自检清单

- [ ] 我能解释 shebang 与 `bash x.sh` / `./x.sh` / `source x.sh` 三种执行的区别
- [ ] 赋值等号两边我不留空格，涉及变量的字符串我恒用双引号
- [ ] 我用 `$(...)` 做命令替换，给脚本传参用 `$1`/`$#` 并做缺参校验
- [ ] 我会在 `[[ ]]` 里用 -f/-d/-z 和数字比较，并用 if 直接判断命令成败
- [ ] 我知道管道内循环是子 shell 的坑，逐行读文件用 `done < file`
- [ ] **我新写的每个脚本第一行都是 `set -euo pipefail`，并能逐项解释它防的错**
- [ ] 我写脚本时给错误信息走 stderr、给失败诚实 exit 1
- [ ] 我写完脚本会跑 shellcheck，三个实战脚本我都能脱稿写出来
- [ ] 我知道脚本进 cron 前要先手动跑通、全程绝对路径、输出落日志

## 延伸阅读

- [Bash 官方参考手册（GNU）](https://www.gnu.org/software/bash/manual/bash.html)——set 选项、参数展开等语法的权威出处。
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)——工业界 shell 风格的参考标杆（何时用/不用 shell 的判断尤其值得读）。
- [ShellCheck 用户手册](https://www.shellcheck.net/)——在线版与规则 Wiki 入口，每条警告都有详细解释。
- [Advance bash-scripting Guide（TLDP）](https://tldp.org/LDP/abs/html/)——进阶技巧大全（偏深，按需查阅）。
- [man7：bash 内建命令](https://man7.org/linux/man-pages/man1/bash.1.html)——read/trap/local 等内建行为的精确定义。
