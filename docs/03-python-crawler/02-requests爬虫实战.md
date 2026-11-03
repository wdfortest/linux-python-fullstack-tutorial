# 第 2 章 · requests 爬虫实战

> 本章配套代码：`projects/crawler-lab/02_requests_quotes.py`
> 建议学习时长：约 4 小时

## 学习目标

学完本章，你能够：

1. 用 requests 完成带 headers、timeout、重试的规范 GET 请求，并解释每一项为什么必须存在；
2. 现场识别并修复 `resp.encoding` 编码坑（本章用 books.toscrape.com 做真实演示）；
3. 用 Session 复用连接、用封装函数处理网络抖动与临时 5xx；
4. 抓取 JSON API 并解释它与 HTML 采集在解析上的差别；
5. 掌握两种分页模式（URL 规律遍历 vs 跟随「下一页」链接），并完成一个可复现的全站采集：quotes.toscrape.com 全部 10 页 100 条名言，落盘为 JSON。

## 2.1 前置知识 / 本章地位

第 1 章建立了 HTTP 与网页结构的心智模型；本章开始动手写采集代码。requests 是 Python 爬虫事实上的标准库（官方口号「HTTP for Humans」），它把第 1 章讲的报文细节都封装成了参数——但封装不等于不用懂，**encoding、timeout、重试这些「开关背后的语义」恰恰是初学者与熟练者的分水岭**。

版本事实（撰写时实测，以官方仓库为准）：Python 3.14.0 + requests 2.34.2，环境即仓库 `jjyv` venv。本章实战目标仍是 `quotes.toscrape.com`（第 1 章的两个练习站之一，明确欢迎抓取），所有代码遵循全篇合规约定：UA 标明教育用途、请求间隔 ≥ 0.3s、只抓公开页面——法律细节第 6 章专章展开。

## 2.2 最小可用爬虫：一个 GET 的完整参数

```python
import requests

HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (educational use only)"}

resp = requests.get(
    "https://quotes.toscrape.com/page/1/",
    headers=HEADERS,   # 表明身份（本仓库规范：教育用途，不伪装浏览器）
    params={"tag": "love"},          # 查询参数，等价于拼在 URL 上的 ?tag=love
    timeout=10,        # 超时必设，绝不无限等待
)
resp.raise_for_status()          # 4xx/5xx 抛异常，别把错误页当数据解析
print(resp.status_code, resp.url)  # resp.url 是最终 URL（重定向后）
print(len(resp.text), "字符")
```

预期输出：

```text
200 https://quotes.toscrape.com/tag/love/page/1/
8466 字符
```

三个参数的取舍逻辑，每一条都对应真实事故：

- **`timeout` 必设**：requests 默认**没有超时**。服务器挂起时，你的爬虫会卡死在那一个请求上，脚本级任务表现为「永远不结束」，工程级任务表现为「队列堆积」。设 10 秒是采集型请求的常见取值；
- **`raise_for_status()` 必调**：404 页面也带 HTML 正文，不抛异常的话你会把「页面不存在」当数据存进库里，错误会在解析层才暴露，排查成本翻倍；
- **`headers` 至少给 UA**：不带 UA 的请求（UA 为 `python-requests/x.x`）在真实站点上是最容易被识别拦截的形态。本仓库的规范更进一步：UA 里写明教育用途，**诚实地告诉服务器你是谁**——第 6 章会讲为什么伪装反而是风险。

`params` 的价值：自动做 URL 编码（空格变 `%20`、中文按 UTF-8 编码）。手拼查询串是注入乱码与编码 bug 的高发地。

## 2.3 encoding 坑：books.toscrape.com 真实演示

这是本教程最有教学价值的一个真实坑。requests 拿到响应后要解码字节才能给出 `resp.text`，解码用哪个编码？它的查找顺序是：

1. HTTP 响应头 `Content-Type` 里的 `charset=...`；
2. 没有的话，对 `text/*` 类型按 HTTP 规范默认 **ISO-8859-1**（requests 遵循了这个老规范）；
3. 只有当你显式调用 `resp.content.decode(某编码)` 或设置 `resp.encoding` 才会改变。

而 books.toscrape.com 的响应头**不带 charset**（HTML `<meta charset="UTF-8">` 里倒是声明了，但 requests 不看 HTML 内容来猜）。于是一个完全正常的服务器返回了 UTF-8 字节，requests 用 ISO-8859-1 去解——`£`（UTF-8 两字节 `0xC2 0xA3`）被拆成两个字符，显示为 `Â£`。实测复现：

```python
import requests

HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (educational use only)"}
r = requests.get("https://books.toscrape.com/", headers=HEADERS, timeout=10)
print("r.encoding:", r.encoding)
price_line = [l for l in r.text.splitlines() if "price_color" in l][0]
print(price_line.strip()[:50])

r2 = requests.get("https://books.toscrape.com/", headers=HEADERS, timeout=10)
r2.encoding = "utf-8"  # 按 HTML 内 <meta charset="UTF-8"> 声明修正
price_line2 = [l for l in r2.text.splitlines() if "price_color" in l][0]
print(price_line2.strip()[:50])
```

预期输出（撰写时实测）：

```text
r.encoding: ISO-8859-1
<p class="price_color">Â£51.77</p>
<p class="price_color">£51.77</p>
```

三种修复方式与取舍：

| 方式 | 写法 | 适用 |
|---|---|---|
| 显式指定 | `r.encoding = "utf-8"` | 已知站点编码（推荐，快且无歧义） |
| 自动检测 | `r.encoding = r.apparent_encoding`（基于 charset 检测） | 编码未知的站点，有计算开销 |
| 用字节自己解 | `html = r.content.decode("utf-8")` | 需要把字节交给 lxml 等下游时 |

排查口诀：**看到 `Â`、`ã€`、`æ` 这类「每个汉字后面跟一个奇怪字符」的乱码，第一反应就是 encoding 猜错了**。quotes.toscrape.com 不踩这个坑（它的响应头带 `charset=utf-8`），这也是本章实战选它的原因之一——第 3 章 lab 离线解析这份 HTML 时不需要分心处理编码。

## 2.4 Session 复用与重试封装：能跑 10 分钟的爬虫

### 2.4.1 为什么要 Session

每次 `requests.get()` 都新建一个连接（TCP 握手 + TLS 握手），抓 10 页就是 10 次完整握手。`requests.Session()` 在多次请求间**复用底层 TCP 连接**（HTTP keep-alive），还自动保留 Cookie——第 1 章讲的会话原理在这里落地。用法只是把模块级函数换成实例方法：

```python
session = requests.Session()
resp = session.get(url, headers=HEADERS, timeout=10)  # 之后所有请求都走这个 session
```

### 2.4.2 重试封装：退避（backoff）不是可选项

网络抖动、临时 502 是长任务的日常。单次失败就崩溃的爬虫跑不了 10 分钟；无脑立即重试则会在服务器抖动时火上浇油。标准做法是**有限次数 + 递增间隔的重试**：

```python
import time
import requests

TIMEOUT = 10

def fetch_with_retry(session: requests.Session, url: str,
                     headers: dict, max_retries: int = 3) -> requests.Response:
    """带重试的 GET：网络抖动、临时 5xx 时自动退避重试。"""
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = 0.5 * attempt      # 简化退避：0.5s -> 1.0s -> 1.5s
                time.sleep(wait)
    raise RuntimeError(f"重试 {max_retries} 次后仍失败：{url}") from last_exc
```

设计要点：

- 捕获 `requests.RequestException`（所有 requests 异常的基类），连接错误、超时、HTTP 错误一网打尽；
- 退避间隔**递增**，给服务器恢复的时间；
- 重试耗尽后**抛异常而不是返回 None**——让调用方明确知道失败，而不是拿到一个 None 在解析层莫名其妙地炸；
- 注意 429 不在此列：收到 429 说明对方明确要求你慢下来，正确响应是**大幅降低频率或停止**，而不是「等 1 秒再试」。

（生产级项目可直接用 `urllib3.util.Retry` 配合 `requests.adapters.HTTPAdapter`，语义相同、配置更细；手写版的价值在于看清机制。）

## 2.5 JSON API 采集

不是所有数据都在 HTML 里。第 1 章讲的 Network 面板找接口，找到后采集反而更简单——响应是结构化 JSON，不需要解析器。requests 一行适配：

```python
resp = session.get("https://quotes.toscrape.com/api/quotes?page=1",
                   headers=HEADERS, timeout=10)
resp.raise_for_status()
data = resp.json()          # Content-Type: application/json 时直接得到 dict/list
print(data.keys())
```

要点：

- 先用 `resp.headers["Content-Type"]` 确认是 JSON，再用 `.json()`；
- `.json()` 内部就是 `json.loads(resp.text)`，解析失败（响应其实是 HTML 错误页）会抛 `json.JSONDecodeError`——这通常意味着接口路径错了或被重定向了；
- 采集 JSON 接口同样要遵守频率礼仪：接口只是「另一种页面」，不因为它是数据就抓得更凶。

## 2.6 两种分页模式

### 模式 A：URL 规律遍历

页码有明确规律时（`/page/1/`、`/page/2/`……）用 `for` 循环硬遍历。优点是简单、可用 `itertools` 控制数量；缺点是**硬编码了「站点长什么样」的假设**——站点哪天改成每页 20 条、总页数变了，脚本不会自己发现。

### 模式 B：跟随「下一页」链接（推荐）

每一页 HTML 里都有指向下一页的链接，跟着走直到没有为止：

```python
import re

next_m = re.search(r'<li class="next">\s*<a href="([^"]+)"', html)
url = BASE_URL + next_m.group(1) if next_m else None   # 没有下一页时 url 变 None，循环结束
```

优点：**翻页逻辑跟着站点结构走**，站点加页、减页、改每页条数都不用改脚本；到达最后一页时自然停止，不会多请求一次 404。这是比「猜页数」更符合爬虫伦理的做法——不会向不存在的页码发请求。

用 BeautifulSoup 找「下一页」的写法（第 3 章展开选择器）：`soup.select_one("li.next a")`，取 `["href"]` 即可。

## 2.7 【实战】抓取 quotes.toscrape.com 全部 10 页

完整脚本在 `projects/crawler-lab/02_requests_quotes.py`，把本章所有要素组装起来：Session 复用、重试封装、模式 B 翻页、0.5s 礼貌间隔、正则轻量解析（第 3 章会换成 BeautifulSoup 重写解析部分）、落盘 JSON，并顺手保存第 1 页原始 HTML 供第 3 章 lab 离线练习。

结构上值得注意的三个决定（脚本内注释也有说明）：

1. **四件套写死在开头**：BASE_URL、HEADERS（教育用途 UA）、DELAY_SECONDS=0.5、TIMEOUT=10——每个爬虫脚本都应能一眼看出这四个约定；
2. **解析函数容忍脏数据**：`parse_page` 里结构不符预期的块直接 `continue` 跳过，单条脏数据不会毁掉整页采集；
3. **产出双份数据**：`data/quotes.json`（全量数据，供第 4 章存储练习）与 `data/quotes_page1.html`（原始 HTML，供第 3 章解析练习）。

运行（在仓库根目录）：

```bash
source ~/opt/jjyv/bin/activate
python projects/crawler-lab/02_requests_quotes.py
```

预期输出（撰写时实测，10 页约 10 秒——0.5s 间隔 × 10 页是主要开销）：

```text
第 1 页 https://quotes.toscrape.com/page/1/ -> 10 条名言
第 2 页 https://quotes.toscrape.com/page/2/ -> 10 条名言
第 3 页 https://quotes.toscrape.com/page/3/ -> 10 条名言
第 4 页 https://quotes.toscrape.com/page/4/ -> 10 条名言
第 5 页 https://quotes.toscrape.com/page/5/ -> 10 条名言
第 6 页 https://quotes.toscrape.com/page/6/ -> 10 条名言
第 7 页 https://quotes.toscrape.com/page/7/ -> 10 条名言
第 8 页 https://quotes.toscrape.com/page/8/ -> 10 条名言
第 9 页 https://quotes.toscrape.com/page/9/ -> 10 条名言
第 10 页 https://quotes.toscrape.com/page/10/ -> 10 条名言

共 10 页 100 条名言 -> /Users/jjy/Documents/linux学习与实战/projects/crawler-lab/data/quotes.json
```

验收 JSON 产出（注意引号是站点的智能引号 `“”`，UTF-8 落盘无乱码）：

```bash
python -c "
import json
data = json.load(open('projects/crawler-lab/data/quotes.json'))
print(data['count'], data['source'])
print(json.dumps(data['quotes'][0], ensure_ascii=False)[:120])
"
```

预期输出：

```text
100 https://quotes.toscrape.com
{"text": "“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”", "author": "Albert
```

### 补充：代理参数与并发预告

requests 通过 `proxies` 参数支持代理（`{"https": "http://127.0.0.1:7890"}`），适用场景是**你的网络环境需要出网代理**，而不是「换 IP 躲限制」——把代理当反爬对抗工具属于第 6 章要划红线的范畴，本教程不展开。至于「抓得更快」的正确姿势（异步并发 + 信号量限速），第 8 章整章讨论：并发是你自己的效率，限速是对服务器的礼貌，两者必须同时做。

## 2.8 POST 与表单登录（练习站演示）

quotes.toscrape.com 的 `/login` 页面是官方为练习表单交互准备的（第 7 章 Selenium 也会用它）。用 requests 模拟登录的四步：**GET 登录页（拿表单结构与 CSRF token）→ POST 凭据（连同 token）→ 检查 POST 结果 → 用同一个 Session 访问需登录的页面**。第 1 章 1.3.4 讲的 Cookie/Session 原理在这里变成一行代码——**Session 对象自动保存并回传 Cookie**。

先看一个真实的失败尝试（值得复现一次）：只提交用户名密码，**不带 CSRF token**：

```python
import requests

HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (educational use only)"}
s = requests.Session()   # 登录态必须存活在同一个 Session 里

s.post("https://quotes.toscrape.com/login",
       data={"username": "demo_user", "password": "demo_password"},
       headers=HEADERS, timeout=10)
home = s.get("https://quotes.toscrape.com/", headers=HEADERS, timeout=10)
print("Logout" in home.text)          # False:登录没成功,而且没有任何报错!
```

预期输出：

```text
False
```

没有异常、状态码正常，但登录就是没生效——这类「静默失败」是模拟登录的头号坑。原因是练习站也实现了 **CSRF 防护**：服务器在 GET 登录页时把一个随机 token 同时放进表单（隐藏的 `<input name="csrf_token">`）和你的 Session Cookie；POST 时必须把这个 token 原样带回，服务器核对「表单里的 token 与 Cookie 里的是同一个」才受理。**核对失败不会报错，只是把你送回登录页重渲染**（观察 `r.url` 停在 `/login` 不跳转，就是失败信号）。

完整正确版本：

```python
import re
import requests

HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (educational use only)"}
s = requests.Session()   # GET 与 POST 必须同一个 Session(token 存在 Cookie 里)

# 1. GET 登录页:服务器把 csrf_token 同时放进表单和 session Cookie
login_page = s.get("https://quotes.toscrape.com/login", headers=HEADERS, timeout=10)
login_page.raise_for_status()
csrf = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text).group(1)
print("csrf_token 前 12 字符:", csrf[:12], "...")

# 2. POST 必须带回 csrf_token,否则服务器重渲染登录页(观察 URL 不跳转)
post_result = s.post(
    "https://quotes.toscrape.com/login",
    data={"csrf_token": csrf, "username": "demo_user", "password": "demo_password"},
    headers=HEADERS, timeout=10,
)
print("POST 最终 URL:", post_result.url, "| 状态:", post_result.status_code)

# 3. 同一 Session 访问首页,登录态生效
home = s.get("https://quotes.toscrape.com/", headers=HEADERS, timeout=10)
print("Logout in body:", "Logout" in home.text)
```

预期输出（撰写时实测，token 每次随机）：

```text
csrf_token 前 12 字符: twLexnuZidAm ...
POST 最终 URL: https://quotes.toscrape.com/ | 状态: 200
Logout in body: True
```

要点与边界：

- **字段名与隐藏字段从 HTML 来，不靠猜**：打开登录页源码找 `<input name="...">`，这正是第 1 章「先当人肉爬虫」的纪律；
- **CSRF 是正规流程，不是反爬对抗**：token 随表单下发、随表单回传，任何正常浏览器用户都在无意间完成这件事——模拟浏览器做的正常事，与破解（第 6 章边界）有本质区别；
- **验证失败看 `r.url` 与正文关键词**，不要只看状态码——302 跳回 `/` 才是成功信号，停在 `/login` 就是失败；
- **真实站点的登录往往更复杂**（验证码、JS 加密、二次验证），那些属于第 6 章划界的范畴；
- 练习站接受任意凭据，本例只证明「登录流程走通了」，不涉及任何真实账号。

## 2.9 Response 对象速查表

第 2 章用到过零散的属性，这里集中一次：

| 属性/方法 | 类型 | 说明 |
|---|---|---|
| `resp.status_code` | int | 状态码；`resp.ok` 是它的布尔版（4xx/5xx 为 False，**不抛异常**） |
| `resp.url` | str | 最终 URL（跟随重定向后） |
| `resp.headers` | 大小写不敏感字典 | 响应头；`resp.headers["Content-Type"]` |
| `resp.text` | str | 解码后的正文（encoding 坑所在，见 2.3） |
| `resp.content` | bytes | 原始字节（图片/文件下载、自己控制解码时用） |
| `resp.encoding` | str | `resp.text` 使用的解码编码，可赋值修正 |
| `resp.apparent_encoding` | str | charset 检测猜测的编码（兜底用） |
| `resp.json()` | dict/list | 正文按 JSON 解析 |
| `resp.raise_for_status()` | — | 4xx/5xx 抛 `requests.HTTPError` |
| `resp.history` | list | 重定向链上的中间响应（空列表表示无重定向） |
| `resp.elapsed` | timedelta | 请求耗时（监控慢请求的原始数据） |

记忆锚点：`text`（人读的字符串）、`content`（机器读的字节）、`json()`（结构化数据）三分天下；`ok` 与 `raise_for_status()` 的区别是「温和检查」与「硬失败」，封装层用后者（2.4.2 的理由）。

## 常见坑与排查（Troubleshooting）

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `resp.text` 出现 `Â£`、`æ` 类乱码 | 服务器没返回 charset，requests 默认 ISO-8859-1（2.3 节实测演示） | `r.encoding = "utf-8"` 或用 `r.content.decode("utf-8")` |
| 脚本卡住不动，不报错 | 没设 timeout，某个请求被服务器挂起 | 所有请求必设 `timeout`；排查已卡进程只能杀掉重跑 |
| `resp.json()` 抛 `JSONDecodeError` | 接口返回的是 HTML（路径错/被重定向） | 先看 `resp.url` 与 `resp.headers["Content-Type"]`；调接口前用浏览器验证 |
| 采集结果里有 404 页面的数据 | 忘了 `raise_for_status()`，错误页被当数据解析 | 封装层统一 `raise_for_status`，见 2.4.2 |
| 循环翻页死循环不停 | 「下一页」判断写反，最后一页又跳回第一页 | 打印 `url` 跟踪；用 `set` 记录已访问 URL 去重（第 8 章的断点续爬机制） |
| `Max retries exceeded with url` | 请求被拒或网络问题，重试耗尽 | 看底层异常（`SSLError`/`ConnectionError`）；降速；确认目标 URL 正确 |
| Windows 控制台打印中文报 `UnicodeEncodeError` | 控制台编码不是 UTF-8 | `chcp 65001` 或 `PYTHONIOENCODING=utf-8`；文件写入始终显式 `encoding="utf-8"` |
| 抓下来数量比预期少 | 解析函数对某类结构直接跳过（`continue`） | 统计「跳过数」并打日志，抽样对比原始 HTML |

## 动手练习

1. **复现 encoding 坑并写进注释**：运行 2.3 的演示代码，把你的实测输出贴进自己脚本的 docstring；再改用 `r.apparent_encoding` 修复，对比两种修复结果是否一致。
   <details><summary>提示</summary>apparent_encoding 基于 charset 检测，对这份 ASCII 为主的页面应同样得出 utf-8。已知编码时显式指定是更好的工程习惯。</details>
2. **给 lab 脚本加「跳过统计」**：修改 `parse_page`，统计结构不符被 `continue` 跳过的块数，正常情况下应为 0；再故意把 author 的正则改错一个字母，观察跳过数变成 10——这就是「静默丢数据」的可视化。
   <details><summary>提示</summary>加一个 skipped 计数器并在 main 里打印。观察点：错误没有暴露时数据悄悄变少，暴露后才可能被修复。</details>
3. **JSON API 版采集器**：不用 HTML 解析，改走 `quotes.toscrape.com/api/quotes?page=N` 接口抓全 10 页，产出与 `quotes.json` 同结构的数据，并用脚本对比两条路线的字段是否一致。
   <details><summary>提示</summary>接口返回的 tags 顺序与页面一致；对比时只比 text/author 集合即可（浮点与列表顺序都可能造成假差异）。</details>
4. **带退避的重试观测**：把 lab 的 `max_retries` 改成 2、给 URL 故意加一个错误域名前缀，观察重试日志与最终异常，然后恢复；确认异常信息里保留了原始原因（`from last_exc` 的作用）。
   <details><summary>提示</summary>RuntimeError 的 traceback 最后一行会显示 "The above exception was the direct cause"——异常链保住了根因。</details>

## 小结与自检清单

- [ ] 我写 GET 请求时默认带 headers/timeout/raise_for_status，并能说出三者缺一的真实事故
- [ ] 我能复现并解释 books.toscrape.com 的 encoding 坑，知道三种修复方式
- [ ] 我知道 Session 复用的两个好处（连接复用、Cookie 保留）
- [ ] 我会写有限次数、递增间隔的重试封装，并知道 429 应该降速而不是重试
- [ ] 我掌握了两种分页模式，理解「跟随下一页」为什么更稳、更礼貌
- [ ] 我成功运行了 lab，采集到 10 页 100 条名言并落盘 JSON，与文档预期输出一致
- [ ] 我理解代理的正当用途（出网）与不当用途（对抗式换 IP）的边界

## 延伸阅读

- [requests 官方文档：快速上手](https://requests.readthedocs.io/projects/cn/zh_CN/latest/user/quickstart.html)——官方中文文档，本章所有 API 的权威定义。
- [requests 官方文档：高级用法（Session 与超时）](https://requests.readthedocs.io/projects/cn/zh_CN/latest/user/advanced.html)——Session 机制、超时语义、代理配置的细节。
- [JSON 官方站点](https://www.json.org/json-zh.html)——JSON 语法规范，2.5 节数据结构的基础。
- [urllib3 Retry 文档](https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry)——生产级重试策略的官方实现，2.4.2 手写版的工程化替代。
- 上一章：[HTTP 与网页结构基础](01-HTTP与网页结构基础.md)；下一章：[HTML 解析（BeautifulSoup 与 lxml）](03-HTML解析(BeautifulSoup与lxml).md)。
