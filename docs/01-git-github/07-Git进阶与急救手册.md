# 7 · Git 进阶与急救手册

> 本章配套代码：`projects/git-lab/rescue-drill.sh`（一键制造「误删分支 + 误回退」急救演练现场）
> 建议学习时长：约 3.5 小时

## 学习目标

学完本章，你应该能够：

- 用 `git reflog` 找回误删分支、误 reset 丢弃的提交，并解释它为什么总能做到。
- 熟练区分 `reset` 三种模式对 HEAD、暂存区、工作区的不同影响（表驱动）。
- 用 `cherry-pick` 把某个提交摘到另一分支（hotfix 场景）。
- 用 `git bisect` 二分定位「哪个提交引入了 bug」，并会用 `--run` 自动化。
- 判断 submodule / worktree / LFS 各自的适用场景，并能说出「什么时候别用」。
- 遇到「误提交敏感信息」「误删分支」「乱码」等事故时，按急救速查表处置。

## 7.1 前置知识 / 本章地位

依赖[第 01 章](01-Git核心概念与安装配置.md)的对象模型（1.4 节：为什么提交永不丢失）、[第 02 章](02-Git日常操作完全指南.md)的撤销决策图与 [rebase 黄金法则](03-分支完全指南.md)。前几章讲「怎么不出事」，本章讲「出了事怎么办」——它建立在第 01 章那个关键事实上：**commit 对象一旦创建就持续存在于 `.git` 的对象库中，直到被垃圾回收**，而 reflog 正是访问这些「孤儿提交」的索引。

## 7.2 reflog：你的后悔药

### 7.2.1 原理：HEAD 的移动日志

`git reflog` 记录的是「HEAD 指针的每一次移动」——提交、切换、reset、合并……每一步都留下一行，默认保留 90 天。分支删了、reset 扔了，**只要 reflog 里还有那行记录，对应的提交就摸得着**。

在练习仓库制造一次事故并自救（全程真实输出）：

```bash
$ git log --oneline -3
```

预期输出示例：

```text
5073e09 (HEAD -> main) feat: v3
b881a4f feat: v2
79a2d3c feat: v1
```

手滑回退太远（本意只想 reset 一步，多打了一个 `~1`）：

```bash
$ git reset --hard HEAD~1
HEAD is now at b881a4f feat: v2
$ git log --oneline -2
b881a4f (HEAD -> main) feat: v2
79a2d3c feat: v1
```

`feat: v3` 从分支上消失了。看 reflog：

```bash
$ git reflog
```

预期输出（逐行是 HEAD 的移动史，从新到旧）：

```text
b881a4f HEAD@{0}: reset: moving to HEAD~1
5073e09 HEAD@{1}: commit: feat: v3
b881a4f HEAD@{2}: commit: feat: v2
79a2d3c HEAD@{3}: commit (initial): feat: v1
```

逐段解释：`HEAD@{N}` 表示「HEAD 往前数 N 次移动之前的位置」。`HEAD@{0}` 是现在的位置（reset 之后），`HEAD@{1}` 是 reset 之前——**v3 就在那里**。恢复：

```bash
$ git reset --hard HEAD@{1}
HEAD is now at 5073e09 feat: v3
$ git log --oneline -3
5073e09 (HEAD -> main) feat: v3
b881a4f feat: v2
79a2d3c feat: v1
```

写法上更稳的是直接用哈希 `git reset --hard 5073e09`——`HEAD@{n}` 依赖「你再做一次操作之前」的时序，哈希不依赖。

### 7.2.2 案例：找回误删分支

误删了还没合并的 feature 分支（`-D` 绕过了保护）。运行配套脚本生成演练现场：

```bash
cd /Users/jjy/Documents/linux学习与实战/projects/git-lab
./rescue-drill.sh /tmp/git-rescue-demo
cd /tmp/git-rescue-demo
```

脚本删除了 `feature/important-work`（上面有 2 个提交）。恢复三步：

```bash
$ git reflog | head -5
```

预期输出示例：

```text
a1b2c3d (HEAD -> main) HEAD@{0}: reset: moving to HEAD~2
d218520 HEAD@{1}: commit: feat: 报表导出功能
8c9d0e1 HEAD@{2}: commit: feat: 用户统计模块
a1b2c3d HEAD@{3}: reset: moving to HEAD@{1}
...
```

（哈希为示例，你的必不同。）找到被删分支尖端提交的哈希后，**原地重建分支**：

```bash
$ git branch feature/important-work d218520
$ git branch -v
* main                   a1b2c3d feat: 初始化
  feature/important-work d218520 feat: 报表导出功能
```

分支回来了——因为「删分支」只删了 41 字节的指针文件，提交本身一直在。想看看被删分支的历史再决定，可以用 `git log --oneline d218520 -3`；确认无价值就不必重建，让它等垃圾回收即可。

两条注意事项：

1. **reflog 只在本地仓库有效**——它记录的是你本机的 HEAD 移动，同事的仓库里没有你的记录。误删发生在别人 clone 的仓库时，让对方在自己机器上跑 reflog。
2. 未提交过的工作区内容（从没 add/commit）不在任何保护范围内。reflog 救的是「进过对象库」的东西。

## 7.3 reset 三模式深入

[第 02 章](02-Git日常操作完全指南.md)给出了速查表，这里给完整的机制视图。`git reset <target>` 做三件事，模式决定做到第几步：

1. 移动当前分支指针到 target（三种模式都做）；
2. 用 target 的快照重置暂存区（`--mixed` 起做）；
3. 用 target 的快照重置工作区（只有 `--hard` 做）。

| 影响对象 | `--soft` | `--mixed`（默认） | `--hard` |
|---|---|---|---|
| HEAD / 分支指针 | 移动 | 移动 | 移动 |
| 暂存区 | 不动 | 重置为 target | 重置为 target |
| 工作区 | 不动 | 不动 | **重置为 target** |
| 丢弃的提交还能找回吗 | 能（reflog） | 能（reflog） | 已提交部分能；**未提交改动永久丢失** |
| 典型场景 | 撤销 commit，重新组织暂存 | 撤销 commit，从头选内容 | 对齐到某个快照，本地未提交的脏东西全不要 |

三种模式各自的「reset 后 status 长相」：

- `--soft`：所有改动显示在 `Changes to be committed`（全在暂存区）。
- `--mixed`：所有改动显示在 `Changes not staged`（全在工作区）。
- `--hard`：`nothing to commit, working tree clean`（干净得像 target 时刻）。

与兄弟命令的边界：

- `git restore`（第 02 章）：只动单个文件的工作区/暂存区，**不动历史**；reset 动指针。
- `git revert`：生成反向提交，**不改历史**，共享分支安全；reset 改写「分支指向的历史」，仅限私有分支（rebase 黄金法则同理）。
- `git reset --hard` 前的保险动作：`git stash push -u` 或至少 `git branch backup-yyyymmdd`——给「当前状态」留个 41 字节的锚点，成本趋近于零。

## 7.4 cherry-pick：把某个提交摘到当前分支

场景：hotfix 分支上修了个线上 bug，但那个分支还要继续开发到下周，而线上补丁等不了——把这一个提交「摘」到 main。

```bash
$ git switch main
$ git cherry-pick hotfix-1.0.1    # 参数可以是分支名（取其尖端提交）、提交哈希或区间
```

预期输出（真实格式）：

```text
[main 9d23fd6] fix: 修复 f.txt 计算错误
 Date: Wed Nov 4 00:14:45 2026 +0800
 1 file changed, 1 insertion(+)
```

注意：cherry-pick 创建的是**内容相同的新提交**（新父提交 → 新哈希），机制与 rebase 的单提交版完全一致。这带来两条使用纪律：

1. **摘完记得在来源分支做记录**（如 `git log --oneline` 对照或提交信息注明 `cherry picked from <哈希>`），否则将来合并两个分支时同一改动会出现两份「哈希不同、内容相同」的提交，可能触发假冲突。
2. cherry-pick 同样可能冲突，处理流程与[第 03 章](03-分支完全指南.md)合并冲突一致：改文件 → `git add` → `git cherry-pick --continue`；放弃用 `--abort`。

GitHub PR 页面也内置了「cherry-pick 到另一分支」按钮（创建反向 PR 的形式），本质相同。

## 7.5 bisect：二分定位引入 bug 的提交

场景：某个功能在 v1.0.0（练习仓库打了 tag 的提交）时还好好的，现在坏了。中间隔了几十个提交，逐个 checkout 人肉排查太慢——Git 自带二分器。

前提准备一个「判定脚本」：退出码 0 表示好、1 表示坏。以练习仓库为例（`check.sh` 检查计算结果里是否含 bug 标记）：

```bash
$ git bisect start HEAD v1.0.0     # 起点两个锚：当前是坏(HEAD)，v1.0.0 是好
```

预期输出（Git 立即切到中点提交并告诉你还剩几步）：

```text
Bisecting: 1 revision left to test after this (roughly 1 step)
[d3e6e402117bb82d1b85cc999ecdf3322cd06c31] commit 3
```

此时 HEAD 处于游离态（第 03 章 3.4 节），你在中点提交上测试：

```bash
$ ./check.sh && git bisect good || git bisect bad
```

预期输出（中点是好的，Git 继续二分）：

```text
Bisecting: 0 revisions left to test after this (roughly 0 steps)
[7cba81f09c256d0442306206beee0ed1886f96a9] commit 4
```

再测一次，锁定：

```text
7cba81f09c256d0442306206beee0ed1886f96a9 is the first bad commit
commit 7cba81f09c256d0442306206beee0ed1886f96a9
Author: 张三 <zhangsan@example.com>
Date:   Wed Nov 4 00:14:27 2026 +0800

    commit 4

 calc.txt | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
```

**「第一个坏提交」连同它的作者、时间、diff 一次给出**——破案。收尾回主线（bisect 会一直停在游离态，必须显式重置）：

```bash
$ git bisect reset
Previous HEAD position was 7cba81f commit 4
Switched to branch 'main'
```

测试可自动化时一步到位（每次二分自动跑脚本，`run` 子命令自动 good/bad）：

```bash
$ git bisect start HEAD v1.0.0
$ git bisect run ./check.sh
```

预期输出与手工流程等价，最后同样打印 `is the first bad commit` 并附 `bisect found first bad commit`。全程只需 log2(N) 次判定：100 个提交的区间 7 步出结果。两个锚点（好/坏提交）务必先确认可靠，锚错了全盘皆错。

## 7.6 worktree：同时检出多个分支

切分支会整体换掉工作区——如果你正在跑一个长期测试，中途切走再切回，状态就断了。`git worktree` 让**同一个仓库**同时检出多个分支到多个目录：

```bash
$ git worktree add ../hotfix-wt -b hotfix/urgent
```

预期输出：

```text
Preparing worktree (new branch 'hotfix/urgent')
HEAD is now at c5b08c7 init
```

验证（两个目录共享同一个 `.git` 对象库，各自的分支互不干扰）：

```bash
$ git worktree list
```

预期输出：

```text
/private/tmp/gitlab-test/wtdemo        c5b08c7 [main]
/private/tmp/gitlab-test/wtdemo-hotfix c5b08c7 [hotfix/urgent]
```

日常用途：一边在 main 跑长任务，一边在另一目录救火；或同时对比两个版本的行为。用完清理：`git worktree remove ../hotfix-wt`。注意一个分支同一时刻只能被一个 worktree 检出（Git 会直接拒绝重复检出）。

## 7.7 submodule 基础

### 7.7.1 是什么、什么时候用

submodule 让一个仓库把**另一个 git 仓库**作为子目录引用，主仓库只记录「子仓库地址 + 固定指向它的某个提交」（记录为 `gitlink`，`git ls-files --stage` 中模式号 `160000`）。适用场景：项目依赖一个**独立演进的仓库**且必须锁版本，如共享的算法库、内部分离的文档站。

添加与使用（真实输出；注意 Git 2.38.1 起为防中间人攻击，本地路径子模块需显式放行 file 协议，远程 HTTPS/SSH 地址无此问题）：

```bash
$ git -c protocol.file.allow=always submodule add /tmp/gitlab-test/sublib libs/mylib
Cloning into '/private/tmp/gitlab-test/submain/libs/mylib'...
done.
```

主仓库多出两个东西：`.gitmodules` 文件与 gitlink 条目：

```ini
[submodule "libs/mylib"]
	path = libs/mylib
	url = /tmp/gitlab-test/sublib
```

克隆含子模块的仓库后，子目录默认是**空壳**，需再初始化：

```bash
$ git submodule update --init --recursive
Submodule path 'libs/mylib': checked out '9f83867f61b8667bb52d540acd8eee6bfe213344'
```

（本教程的模块划分用**同一仓库多目录**（`projects/`）而非 submodule，正是为了避开这些额外步骤。）

### 7.7.2 什么时候别用

- 团队 Git 经验不足（子模块的「更新三连」`fetch → submodule update` 极易被忘，排查成本高）。
- 子仓库频繁演进、需要经常同步最新（submodule 的本质是锁版本，逆着它的天性用）。
- 只是「想复用几个文件」——复制文件或用包管理器（pip 依赖）更简单。

业界共识：submodule 能不用就不用；确需引用外部代码，优先考虑包管理器。

## 7.8 Git LFS 简讲

Git 对文本 diffs 效率极高，但**大二进制文件**（模型权重、数据集、视频）会让 `.git` 膨胀、clone 变慢——每个克隆都要拉全量历史。Git LFS（Large File Storage）的原理：仓库里只存一个**指针文件**（文本，几十字节），真实文件内容托管在 LFS 服务器上，检出时按需下载。

```bash
# 安装后初始化（本教程撰写环境未预装，macOS: brew install git-lfs；以官方文档为准）
git lfs install
# 声明哪些文件走 LFS（写入 .gitattributes，随仓库提交）
git lfs track "*.psd" "*.onnx"
git add .gitattributes
git add model.onnx        # 提交流程不变
```

预期输出（`git lfs track` 执行后）：

```text
Tracking "*.psd"
Tracking "*.onnx"
```

GitHub 对免费 LFS 有存储与带宽配额，超出需付费——公共仓库不适合放大型数据集，练习阶段遵守本仓库 `.gitignore` 的「可再生大文件不入库」约定即可。

## 7.9 急救速查表

### 7.9.1 事故速查

| 事故 | 现场症状 | 处置 |
|---|---|---|
| 误删分支 | `git branch` 里没了 | `git reflog` 找尖端提交哈希 → `git branch <名> <哈希>`（7.2.2） |
| 误 reset --hard 丢提交 | `git log` 少了一截 | `git reflog` 找 reset 前的 `HEAD@{n}` → `git reset --hard HEAD@{n}`（7.2.1） |
| 误 commit（信息错/文件多） | 刚提交还没 push | `git commit --amend`（改信息）；`git reset --soft HEAD~1` 重来 |
| 误 commit 且已 push | 历史已共享 | **不要 reset**，用 `git revert`（第 02 章 2.4.4） |
| 合并搞砸 | merge 进行中一团乱 | 未完成：`git merge --abort`；已完成未 push：`git reset --hard ORIG_HEAD` |
| rebase 中途反悔 | 停在重放半程 | `git rebase --abort` |
| 误 stash drop | 存档没了 | `git fsck --unreachable` 找悬空提交，`git branch <名> <哈希>`（进阶，谨慎） |
| 终端中文乱码 / 文件名转义 | `\346\226\207` 字样 | 文件名：`core.quotepath false`；终端：确认 locale 为 UTF-8 |

### 7.9.2 误提交敏感信息（最重要的事故处置）

把密钥/密码/token 提交进了 Git，正确处置顺序是：

1. **立刻作废泄露的凭证（rotate）**——这是第一优先级，永远排在任何 Git 操作之前。理由：仓库可能已被 fork、被 CI 缓存、被他人 clone，**只要泄露成立，就按已泄露处理**，历史清理只是善后。
2. 换新密钥并更新使用处（环境变量、`.env`，不进 Git；本仓库红线见 [.gitignore 解读](02-Git日常操作完全指南.md)）。
3. 评估是否需要清理历史：私有仓库且从未共享 → 改密码后可从简；公开仓库或已推送 GitHub → 用工具重写历史：

```bash
# git filter-repo（官方推荐的现代工具；pip install git-filter-repo）
git filter-repo --path .env --invert-paths     # 从全部历史中抹除 .env
# 或 BFG Repo-Cleaner（java -jar bfg.jar --delete-files .env）
```

4. 重写历史后**强推 + 通知所有协作者重新 clone**（因为哈希全变，属共享分支改写历史的最重场景）。
5. 向 GitHub 请求清除缓存视图（官方 Support，针对公开仓库残留）。

> 预防永远优于急救：`.env` 进 `.gitignore`、提供 `.env.example` 模板（本仓库的现行做法）、CI 里加密钥扫描（第 08 章可集成 gitleaks 等工具，以官方文档为准）。

## 常见坑与排查（Troubleshooting）

| 报错现象 | 原因 | 解决办法 |
|---|---|---|
| `git reflog` 里找不到目标提交 | 操作太久已过保留期，或从未提交过 | 提交期内的记录才有；未提交内容无解 |
| bisect 后忘了 reset，一直在游离态提交 | bisect 会停在测试提交上 | 养成「bisect 完立即 `git bisect reset`」的肌肉记忆 |
| `fatal: transport 'file' not allowed` | Git 2.38.1+ 禁止本地路径作为克隆源（含 submodule） | `-c protocol.file.allow=always`（仅本地练习用；生产用远程地址） |
| cherry-pick 后同改动在两分支各一份 | 摘取后来源分支未清理 | 合并前在来源分支 rebase/删除已摘提交 |
| worktree 里切分支被拒 | 分支已被另一个 worktree 检出 | `git worktree list` 查占用；先 remove 或换分支 |
| submodule 目录是空的 | clone 后未初始化子模块 | `git submodule update --init --recursive` |
| LFS 文件 clone 下来是指针文本 | 未安装 LFS 或未 `git lfs pull` | `git lfs install && git lfs pull` |
| filter-repo 后 remote 丢失 | 该工具出于安全默认移除 remote | 重新 `git remote add`（第 04 章） |

## 动手练习

### 练习 1：rescue-drill 全流程自救

运行 `rescue-drill.sh`，在不看 7.2.2 正文的情况下，仅凭 `git reflog` 与 `git branch` 完成两个任务：找回 `feature/important-work` 分支、恢复 main 上被 reset 掉的提交。

验收标准：`git log --oneline main` 包含脚本制造的全部提交；`git branch` 中出现重建的分支；全程未使用脚本内嵌的答案。

<details>
<summary>提示</summary>

reflog 从新到旧读，先定位「最后一次正常操作」；两个任务各对应一段移动记录。卡住可先 `git log --oneline --all --graph` 全景观察。
</details>

### 练习 2：三模式对照实验

构造 1 个提交 + 未暂存改动 + 已暂存改动各一份，依次在三个副本仓库中分别执行三种 reset 模式（各回到 HEAD~1），记录三种 `git status` 的差异。

验收标准：能用 7.3 表格逐格验证三份 status 的观察结果，并说出「--hard 后那份未提交改动为什么找不回」。

<details>
<summary>提示</summary>

三种模式各复制一份仓库（`cp -r`）避免互相污染；--hard 前给当前状态打个 `git branch backup` 锚点再删掉，体验 7.3 的「保险动作」。
</details>

### 练习 3：bisect 实战

在练习仓库制造「多个提交、最新版坏了」的场景（如把某个函数改成抛异常并提交多次），写 `check.sh`（用 `python -I` 跑断言，退出码 0/1），然后 `git bisect start HEAD <good锚点>` + `git bisect run ./check.sh` 全自动定位。

验收标准：工具报告的「first bad commit」与你自己记录的引入点一致；结束后执行了 `git bisect reset`。

<details>
<summary>提示</summary>

check.sh 里运行 Python 请用 `python3 -I path/to/script.py`（隔离模式），不要直接 import 工作目录里的模块。锚点选「确定没坏的最早提交」。
</details>

### 练习 4：worktree 并行实验

`git worktree add` 检出两个分支到两个目录，在各自目录提交不同文件，回主目录验证 `git log --all --oneline --graph` 能同时看到两串提交。

验收标准：`git worktree list` 两行以上；两个目录 `git status` 各自干净、分支互不串。

<details>
<summary>提示</summary>

两个 worktree 操作同一个对象库，A 目录的提交在 B 目录 `git log` 立即可见——这是「共享 .git」的直观证明。
</details>

## 小结与自检清单

- [ ] 我能解释 reflog 记录什么、保留多久、为什么它能救回已删除的历史。
- [ ] 我亲手完成过一次「误删分支找回」，并知道该工具只在本地仓库有效的边界。
- [ ] 我能背出 reset 三模式各自动到「三步」中的第几步，以及 --hard 的唯一不可逆点。
- [ ] 我知道 cherry-pick 产生新哈希，及其带来的「重复提交」纪律。
- [ ] 我跑通过一次 bisect（手工或 `--run`），知道为什么要先确认好/坏锚点。
- [ ] 我能对「共享算法库锁版本」「并行救火」「大模型文件」分别选出 submodule / worktree / LFS，并说出各自的「别用时机」。
- [ ] 我记住敏感信息泄露的第一反应是 rotate 凭证，而不是修 Git 历史。

## 延伸阅读

- [Pro Git 中文版第 7 章「Git 工具」](https://git-scm.com/book/zh/v2) —— bisect、submodule、worktree 的权威章节。
- [GitHub Docs：Removing sensitive data from a repository](https://docs.github.com/zh/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) —— 7.9.2 的官方处置流程，含 filter-repo 与 BFG 用法。
- [git-filter-repo 官方手册](https://github.com/newren/git-filter-repo) —— 历史重写的现代标准工具，比 filter-branch 安全得多。
- [Git LFS 官方文档](https://git-lfs.com/) —— 安装与配额说明。
- 下一章：[第 08 章 GitHub Actions 持续集成入门](08-GitHub Actions持续集成入门.md) —— 把「提交规范、测试、密钥扫描」交给机器自动把关。
