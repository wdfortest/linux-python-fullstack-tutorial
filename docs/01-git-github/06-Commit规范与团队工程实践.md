# 6 · Commit 规范与团队工程实践

> 本章配套代码：`projects/git-lab/setup-practice-repo.sh`（练习仓库，其历史提交即按本章规范书写）
> 建议学习时长：约 3 小时

## 学习目标

学完本章，你应该能够：

- 说清提交信息为什么值得投入成本（用 `git blame` 场景回答「半年后谁看得懂」）。
- 按 Conventional Commits 写出 `type(scope): subject` 格式的提交信息，正确处理 breaking change。
- 用「原子性」标准判断一次改动该拆成几个提交。
- 给定一个版本变更，按 SemVer 规则判断主/次/修订号该进哪一位。
- 用 `git log` 生成 CHANGELOG 初稿，理解自动化维护的原理。
- 配置 `.gitattributes` 统一换行符与语言统计。

## 6.1 前置知识 / 本章地位

依赖[第 02 章](02-Git日常操作完全指南.md)（日常提交循环）与[第 05 章](05-团队协作实战（Issue-PR-CodeReview）.md)（PR 中提交被评审的现实场景）。本章把「会提交」升级为「提交得让团队和机器都能读懂」，是仓库自身践行的规范——本教程的 STYLE_GUIDE 第 8 节就是它的落点。

## 6.2 为什么提交信息重要：一次 blame 引发的事故复盘

场景：线上报告「书名解析偶尔漏字段」。你定位到嫌疑函数，开始追查：

```bash
$ git blame -L 42,48 src/crawler/parser.py
```

预期输出（格式真实，内容示例）：

```text
a3f81c2 (李四 2025-11-02 14:22:31 +0800 42) def parse_title(self, html):
a3f81c2 (李四 2025-11-02 14:22:31 +0800 43)     sel = html.css("h1::text")
9d23fd6 (王五 2026-01-15 09:10:04 +0800 44)     return sel[0].strip() if sel else ""
```

`git blame` 回答了「这一行是谁、在哪次提交写的」，但**真正的追问在这之后**：

```bash
$ git show 9d23fd6
```

如果这次提交的信息是 `update` 或 `修改`，你只得多读整个 diff 去猜意图；如果信息是 `fix(parser): 空标题时返回空串而非抛出 IndexError（#42）`，你十秒钟就知道：这是修空页崩溃的防御性改动，且能顺着 `#42` 找到完整来龙去脉。

提交信息是**写给未来读者的一次性投资**：写的人花一分钟，读的人省十分钟，而读的人正是半年后赶着救火的你自己。团队规模扩大后它还多一层价值——CHANGELOG 生成、版本号判断、变更检索，全都建立在规范信息之上（见 6.4 节）。

## 6.3 Conventional Commits 详解

### 6.3.1 格式

[Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 是目前最通行的提交信息规范，核心格式：

```text
<type>(<scope>): <subject>

[可选正文：解释为什么，而不是改了什么]

[可选 footer：BREAKING CHANGE、Issue 引用等]
```

实例：

```text
feat(crawler): 支持并发抓取多个分页

并发数默认 4，通过 SPIDER_CONCURRENCY 环境变量覆盖，
以降低对目标站点的请求压力（遵循 robots.txt 约束）。

Closes #17
```

### 6.3.2 type 全表

| type | 含义 | 产出版本影响（SemVer） |
|---|---|---|
| `feat` | 新功能 | 次版本 +1 |
| `fix` | 缺陷修复 | 修订号 +1 |
| `docs` | 仅文档变更 | 无 |
| `style` | 不影响代码含义的格式调整（空格、分号等） | 无 |
| `refactor` | 既非新增也非修复的代码改动 | 无 |
| `perf` | 提升性能的改动 | 无（通常按 fix 对待） |
| `test` | 补充/修正测试 | 无 |
| `build` | 影响构建系统或外部依赖（pip 依赖、Dockerfile） | 视情况 |
| `ci` | CI 配置变更（`.github/workflows`） | 无 |
| `chore` | 其他杂项（不改动源码与测试） | 无 |

注意 `style` 的歧义：它指**代码格式**而非「界面样式」——界面样式属于 `feat`。

### 6.3.3 scope

scope 是可选的**影响范围**名词，帮助快速定位：`feat(parser)`、`fix(db)`、`docs(git)`（本教程文档章节）。用团队共识的模块名，保持一致比罗列更全更重要。

### 6.3.4 breaking change：`!` 与 footer

不向后兼容的变更必须显式声明，两种写法（可并用）：

```text
refactor(api)!: 删除已废弃的 /v1/books 接口

BREAKING CHANGE: /v1/books 已移除，请迁移至 /v2/books。
迁移指引见 docs/migration.md。
```

- 标题里的 `!`：冒号前加感叹号，**一眼扫过 log 就能识别**破坏性变更。
- footer 的 `BREAKING CHANGE:` 段：详细说明影响与迁移方式。

机器可据此做两件事：判断版本号（下节）、自动生成 CHANGELOG（6.6 节）。这也是「规范要机器可读」的意义——**规范不是给人看的仪式感，是自动化的输入**。

### 6.3.5 本仓库的规范解读（STYLE_GUIDE 第 8 节）

本教程仓库 [`../../STYLE_GUIDE.md`](../../STYLE_GUIDE.md) 第 8 节规定了自己的落地版本：

> 格式：`type(scope): subject`，如 `docs(ubuntu): 新增 systemd 服务管理一章`；type ∈ `docs | feat | fix | chore | test | style | refactor`；中文 subject，50 字以内，不加句号。

与通用规范的差异与理由：

- **type 集合裁剪**：去掉了 `build`/`ci` 等（本仓库暂无构建系统与 Release 流程），少即是多——规范只保留团队真实用得上的项。
- **中文 subject**：本仓库面向中文读者，信息密度优先；英文规范源仍兼容，因为 type 前缀机器可读。
- **50 字以内、不加句号**：`git log --oneline` 一屏可读；句号与无句号混排会破坏列表视觉一致性。

你在本仓库练习提交时，请直接使用这条规范——仓库自身就是示范（例如 `docs(git): 新增分支完全指南一章`）。

## 6.4 提交粒度：一个 commit 一件事

**原子性（Atomicity）**：每个提交应当是一个完整、独立、可回退的最小变更单元。判断标准有三：

1. **可描述**：一条提交信息能说清全部改动（说不清 = 混了多件事）。
2. **可回退**：单独 revert 这个提交不会把项目搞坏，也不牵连其他功能。
3. **可评审**：diff 长度在他人愿意认真看的范围内（经验值：一次评审几百行以内）。

反面案例与拆法：

```text
# 一次改动：加了搜索功能 + 顺手修了 CSS 错位 + 更新了 README
# 错误做法：一个提交 "feat: 添加搜索"
# 正确拆分：
feat(search): 支持按书名模糊搜索
style(web): 修正搜索框在窄屏下的错位     # 与功能无关的顺手改动，独立提交
docs(readme): 补充搜索功能使用说明
```

`git add -p`（第 02 章 2.3.3）是落实拆分的工具：改动已经混在一起时，按块分别暂存、分别提交。**先拆分再提交**的成本远低于「历史混乱后想整理」——后者只能靠 interactive rebase（第 03 章 3.6.3）补救，且仅限私有分支。

## 6.5 语义化版本 SemVer

[语义化版本](https://semver.org/lang/zh-CN/) 规定版本号格式 `主版本.次版本.修订号`（major.minor.patch，如 `2.3.1`），递增规则：

| 位 | 何时 +1 | 含义 |
|---|---|---|
| 主版本 major | 有不兼容的 API 变更 | 用户需要改自己的代码才能升级 |
| 次版本 minor | 向后兼容的新功能 | 升级无风险，多了新能力 |
| 修订号 patch | 向后兼容的缺陷修复 | 升级无风险，问题更少 |

判断练习（先自己答，再看右列）：

| 变更 | 版本动作 |
|---|---|
| 修复 `parse_title` 的空指针崩溃 | `2.3.1 → 2.3.2`（patch） |
| 新增「按价格区间过滤」参数，旧调用不受影响 | `2.3.2 → 2.4.0`（minor） |
| `parse(html)` 的返回值从 list 改为生成器，调用方需改代码 | `2.4.0 → 3.0.0`（major！） |
| 0.x 阶段（`0.3.0`） | 0.x 常用于开发期，规则可放宽，以项目公告为准 |

与 Conventional Commits 的联动（commitlint 等工具的判断逻辑）：`feat` → minor，`fix`/`perf` → patch，含 `BREAKING CHANGE`（或 `!`）→ major。**版本号不再是拍脑袋，而是从提交历史推导出来的结论**。

发布时打上对应 tag（`git tag -a v2.4.0 -m "..."`，见第 02 章 2.8），tag 即是版本在历史中的坐标。

## 6.6 CHANGELOG 维护

### 6.6.1 手写骨架

`CHANGELOG.md` 放在仓库根目录，按版本倒序、面向**使用者**（不是开发者）描述：

```markdown
# Changelog

## [2.4.0] - 2026-11-04

### Added
- 爬虫支持并发抓取多个分页（#17）

### Fixed
- 空页响应时解析不再崩溃（#42）

## [2.3.2] - 2026-10-20

### Fixed
- 数据库连接池耗尽时自动重试
```

分类沿用 Keep a Changelog 约定：`Added / Changed / Deprecated / Removed / Fixed / Security`。

### 6.6.2 从 git log 半自动生成

规范提交的价值在此兑现——type 直接映射分类：

```bash
git log --pretty=format:"- %s (%h)" v2.3.2..HEAD
```

预期输出示例：

```text
- feat(crawler): 支持并发抓取多个分页 (a3f81c2)
- fix(parser): 空页响应时解析不再崩溃 (9d23fd6)
- docs(readme): 补充搜索功能使用说明 (77b1d0e)
```

人工把三行归入 Added / Fixed / 忽略（docs 不进 CHANGELOG），比从零回忆「这版改了啥」可靠得多。`gh release create v2.4.0 --generate-notes` 还能直接用 PR 列表生成发布说明（GitHub 原生功能，格式与手写风格不同，二选一即可）。想全自动可引入 `git-cliff` 等工具，以官方文档为准；初期手写 + log 辅助是更稳的起点。

## 6.7 .gitattributes 简讲

`.gitattributes`（仓库根目录，随仓库提交）为文件声明属性，与 `.gitignore`（管「忽略谁」）分工不同——它管「这些文件按什么规则处理」。两个高频用途：

### 6.7.1 换行符终结者

Windows 团队与 macOS/Linux 团队协作的经典冲突源：CRLF 与 LF。第 02 章的 autocrlf 是**个人机器级**配置，每人设置不同照样互相污染；`.gitattributes` 把规则**随仓库分发**，所有人一致：

```gitattributes
# 仓库内所有文本文件，入库一律 LF
* text=auto eol=lf

# Windows 脚本保持 CRLF
*.bat text eol=crlf
*.ps1 text eol=crlf

# 二进制文件绝不转换
*.png binary
*.db binary
```

`text=auto eol=lf`：Git 自动识别文本文件，检出和工作区统一用 LF（跨平台工具兼容性最好，Python/Docker/CI 均友好）。提交后需执行一次 `git add --renormalize .` 让存量文件按新规则重新入库。

### 6.7.2 语言统计与 diff 行为

GitHub 仓库首页的语言条形图按**字节数**统计，经常被误判（如把 vendored 的 JS 库算成 JavaScript 大头）。可在 `.gitattributes` 中标注：

```gitattributes
docs/*.md linguist-documentation      # 文档不计入语言统计
assets/*.min.js linguist-vendored     # 第三方库不计入
*.ipynb diff=jupyter                  # 为 notebook 指定 diff 驱动（示例）
```

`linguist-*` 属性由 GitHub 的 linguist 引擎识别，完整属性表以官方文档为准。

## 6.8 提交信息正反例对照

六组真实风格的对照，左侧请避免，右侧推荐：

| # | 反例 | 问题 | 正例 | 好在哪 |
|---|---|---|---|---|
| 1 | `update` | 零信息 | `fix(parser): 空标题时返回空串而非抛出 IndexError` | 读者不用看 diff 就知道改了什么行为 |
| 2 | `修复bug` | 「哪个 bug？」 | `fix(db): 连接池耗尽时自动重试并告警` | 指明模块与处理策略 |
| 3 | `加了新功能还有点优化` | 多件事混一提交，违反原子性 | 拆成 `feat(search): …` 与 `perf(parser): …` 两个提交 | 各自可回退、可评审 |
| 4 | `feat: 修改接口！！！` | 感叹号泛滥 + 未声明破坏性 | `refactor(api)!: 删除废弃的 /v1/books 接口` | `!` 是机器可读的破坏性信号，不是情绪 |
| 5 | `refactor: 重构代码` | 「重构」同义反复，无信息量 | `refactor(parser): 提取公共的 html 清洗逻辑到 utils` | 说清重构的手法与产物 |
| 6 | `fix: 修复 #42 提到的问题（详情见群聊）` | 关键信息在群聊里，档案断裂 | `fix(spider): 遵循 robots.txt 限速配置（Closes #42）` | 关联 Issue 让 PR/Issue 链路自洽 |

一条通用检验法：**把这条提交信息贴进 `git log --oneline` 的列表里，隔着一年看，你能否判断「这个提交能不能安全 revert」。**

## 常见坑与排查（Troubleshooting）

| 报错现象 | 原因 | 解决办法 |
|---|---|---|
| 团队规范形同虚设，总有人写 update | 只发文不设卡 | 接入 commitlint + CI 校验（配合第 08 章），机器把关 |
| `git commit --amend` 改了已推送的提交 | 忘记 amend 会换哈希 | 共享分支禁止 amend；只对未推送提交使用（第 02 章 2.4.5） |
| Windows 与 mac 互相「整文件」换行符改动 | 无 `.gitattributes`，依赖各自 autocrlf | 按 6.7.1 配置并 renormalize |
| CHANGELOG 与实际发布不符 | 事后凭记忆手写 | 用 6.6.2 的 log 生成法，或 PR 标签自动生成 |
| 版本号乱跳（minor 里混入 breaking） | 未联动提交 type | 建立「feat→minor、fix→patch、!→major」的发布检查清单 |
| `git log` 中文提交信息显示为转义码 | 终端编码问题 | 确认 `locale` 为 UTF-8；`core.quotepath false` 管文件名，管不到 log 内容 |
| 一个提交里混进了调试代码 | 提交前没 review 自己的 diff | 提交前 `git diff --staged` 过一遍，删除临时改动 |

## 动手练习

### 练习 1：给练习仓库的历史做体检

在练习仓库执行 `git log --pretty=format:"%h %s"`，逐条检查每个提交是否符合 6.3 格式与 6.4 原子性。

验收标准：输出一份三列清单（提交 / 是否合规 / 违反了哪条），练习仓库历史中应恰好有 1-2 个「故意留的瑕疵提交」供你抓出来。

<details>
<summary>提示</summary>

瑕疵通常长这样：`update files` 类零信息提交，或一个提交同时动功能与格式。抓不到时用 `git show --stat` 看每个提交动了几个文件、几个模块。
</details>

### 练习 2：拆分一个混合提交

在练习仓库一次修改三个文件（功能代码、格式缩进、README），先故意 `git add -A` 提交成一个混合提交，然后 `git reset --soft HEAD~1` 退回，用 `git add` 按文件拆成三个规范提交。

验收标准：`git log --pretty=format:"%s"` 出现三条符合规范的提交，`git show --stat` 确认每个提交只含一类文件。

<details>
<summary>提示</summary>

`reset --soft` 后所有改动回到暂存区，用 `git restore --staged <文件>` 把不需要的先移出，再逐个 add——这正是第 02 章撤销决策图的实战串联。
</details>

### 练习 3：SemVer 判定与打标

给定以下三次变更（按时间序）：修了一个数据空指针、新增导出 CSV 功能、删除了旧版 `parse_html()` 函数并要求调用方迁移。回答：三个版本号各是什么？并按本仓库规范写出三次提交信息与最终的 tag 命令。

验收标准：版本序列正确（patch → minor → major），tag 命令带 `-a -m` 且版本号含 `v` 前缀。

<details>
<summary>提示</summary>

第三次是 breaking change，提交信息要用 `!` 与 `BREAKING CHANGE:` footer（6.3.4）；major 升位时 minor/patch 归零。
</details>

### 练习 4：为你的仓库落一整套规范文件

在本教程仓库（你自己的副本）添加 `.gitattributes`（6.7.1 内容）、`CHANGELOG.md`（6.6.1 骨架），并按第 05 章练习 4 的方式提交推送（`chore(repo): ...`）。

验收标准：推送后在 GitHub 网页端确认语言统计未受新增文件干扰；CHANGELOG 首版内容与 `git log` 对得上。

<details>
<summary>提示</summary>

`git add --renormalize .` 若显示大量文件变更属正常（换行符统一化），确认 `git diff --stat` 里没有二进制文件即可。
</details>

## 小结与自检清单

- [ ] 我能用 `git blame` + `git show` 复盘任意一行代码的来历，并说清提交信息在其中扮演的角色。
- [ ] 我能默写 Conventional Commits 的格式与至少 6 个 type 的含义。
- [ ] 我知道 breaking change 的两种声明写法，以及它们如何驱动版本号判定。
- [ ] 我能用「可描述、可回退、可评审」三条标准判断提交粒度，并用 `add -p` 落实拆分。
- [ ] 我能对任意变更独立完成 SemVer 判定，并知道 `feat`/`fix`/`!` 与版本位的映射。
- [ ] 我能用 `git log --pretty=format:...` 生成 CHANGELOG 素材。
- [ ] 我的仓库已配好 `.gitattributes`，换行符规则随仓库分发。
- [ ] 我通过了 6.8 的六组对照检验，能做到「贴进 oneline 列表一年后仍可读懂」。

## 延伸阅读

- [Conventional Commits 1.0.0（中文）](https://www.conventionalcommits.org/zh-hans/v1.0.0/) —— 规范原文，含 FAQ 与示例集。
- [Keep a Changelog（中文）](https://keepachangelog.com/zh-CN/1.1.0/) —— CHANGELOG 分类与「为什么不靠记忆写」的论述。
- [语义化版本 2.0.0（中文）](https://semver.org/lang/zh-CN/) —— SemVer 官方规范，含边界情况判定。
- [GitHub Docs：Customizing how changed files appear on GitHub](https://docs.github.com/zh/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-how-changed-files-appear-on-github) —— linguist 属性官方说明。
- 下一章：[第 07 章 Git 进阶与急救手册](07-Git进阶与急救手册.md) —— 当规范救不了已经发生的事故时，reflog 与 bisect 出场。
