# 第 3 章 · HTML 解析（BeautifulSoup 与 lxml）

> 本章配套代码：`projects/crawler-lab/03_parse_bs4.py`
> 建议学习时长：约 3.5 小时

## 学习目标

学完本章，你能够：

1. 根据解析器对比表为项目选择 bs4+lxml 或纯 lxml，并说明理由；
2. 熟练使用 `find/find_all` 与 CSS 选择器 `select` 两套 API 定位节点，并知道它们各自适合什么场景；
3. 正确提取属性（`["href"]` 与 `.get()` 的差别）和文本（`get_text(strip=True)`），完成父子兄弟节点导航；
4. 用 `string=`/`class_=`/`attrs=` 参数配合正则做模糊匹配；
5. 写基础 XPath 表达式（后代轴、属性匹配、文本提取），理解 `/` 与 `//` 的本质区别；
6. 遇到「解析不到」时按排查表定位：编码问题、JS 渲染、选择器层级理解错。

## 3.1 前置知识 / 本章地位

第 2 章拿到了 HTML 字符串；本章把它变成结构化数据。解析是爬虫三段式（请求 → **解析** → 存储）的中间环节，也是改动最频繁的环节——请求逻辑稳定后，你的日常维护几乎都在改选择器。

本章主工具是 BeautifulSoup 4（下称 bs4）配 lxml 引擎，XPath 部分用纯 lxml。撰写时实测版本：beautifulsoup4 4.14.3 + lxml 6.1.1，安装 `pip install beautifulsoup4 lxml`（注意包名是 `beautifulsoup4`，导入名是 `bs4`，拼写不同是历史包袱）。

lab 全程离线运行：解析对象是第 2 章实战保存的 `data/quotes_page1.html`，不发任何网络请求，方便你反复实验。

## 3.2 解析器对比：先选引擎

bs4 本身只是「解析调度器」，真正干活的引擎可以换：

| 引擎 | 传入写法 | 速度 | 容错 | 依赖 | 本仓库选择 |
|---|---|---|---|---|---|
| html.parser | `BeautifulSoup(html, "html.parser")` | 慢 | 中 | Python 内置，零依赖 | 备选（无 lxml 环境时） |
| lxml（HTML） | `BeautifulSoup(html, "lxml")` | 快 | 好 | 需 `pip install lxml`（C 扩展） | **默认** |
| lxml-xml | `BeautifulSoup(xml, "lxml-xml")` | 快 | 严格 | 同上 | 解析 XML 时 |
| html5lib | `BeautifulSoup(html, "html5lib")` | 最慢 | 最好（模拟浏览器） | 需单独安装 | 极少数格式极端的页面 |

选择逻辑：**lxml 引擎是默认答案**（快 + 容错好）；html.parser 的存在价值是「零依赖兜底」；html5lib 只在页面 HTML 严重不规范、且解析结果必须与浏览器渲染一致时才考虑。另一个常见选择是**纯 lxml + XPath**（3.6 节）：速度与 bs4+lxml 相当，语法更紧凑，Scrapy 内部用的正是它。

## 3.3 BeautifulSoup 核心模型：soup、Tag、NavigableString

`BeautifulSoup(html, "lxml")` 返回的 `soup` 是一棵文档树，你会打交道的对象只有两种：**Tag**（标签节点）和 **NavigableString**（标签里的文本）。理解这一层，后面所有 API 都好记：

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup("<p class='a'>hello <b>world</b></p>", "lxml")
p = soup.p                  # 访问第一个 <p>，等价于 soup.find("p")
print(p.name)               # 'p'        —— Tag 的标签名
print(p["class"])           # ['a']      —— Tag 的属性（注意 class 返回列表！）
print(p.get_text())         # 'hello world' —— 深度优先拼接所有文本
print(p.b.string)           # 'world'    —— 唯一文本子节点时用 .string
```

三个易混点，现在记住能省掉未来一小时的调试：

1. **`class` 返回列表**（`['a']`）：因为一个标签可以有多个 class；
2. **`.string` 只在「标签内只有一个文本子节点」时有效**，节点里嵌了子标签就返回 `None`——这时用 `get_text()`；
3. **`.text` 与 `get_text()` 等价**，但显式调用方法可读性更好，本仓库统一用 `get_text()`。

## 3.4 find/find_all 与 select：两套定位 API 对照

### 3.4.1 对照表

两套 API 能做完全相同的事，选一套顺手的用到熟，另一套要能看懂：

| 需求 | find / find_all | select / select_one |
|---|---|---|
| 第一个匹配 | `soup.find("div", class_="quote")` | `soup.select_one("div.quote")` |
| 全部匹配（返回列表） | `soup.find_all("div", class_="quote")` | `soup.select("div.quote")` |
| 按标签 | `find_all("span")` | `select("span")` |
| 按 class | `find_all(class_="tag")` | `select(".tag")` |
| 按 id | `find_all(id="username")` | `select("#username")` |
| 后代组合 | `find("div").find("small")` | `select("div.quote small.author")` |
| 直接子代 | `find_all("a", recursive=False)` | `select("div.tags > a.tag")` |
| 按任意属性 | `find_all(attrs={"itemprop": "author"})` | `select('[itemprop="author"]')` |
| 属性前缀匹配 | `find_all(href=re.compile("^/author/"))` | `select('a[href^="/author/"]')` |
| 取属性 | `tag["href"]` / `tag.get("href")` | 同左（select 返回的也是 Tag） |

工程上的经验法则：

- **选择器结构简单、贴近前端知识** → `select`（CSS 选择器你在浏览器「检查」里可以直接验证：Elements 面板按 Ctrl/Cmd+F 搜索选择器，立刻知道命中几个）；
- **需要编程逻辑的过滤**（值范围、函数判断、多个条件组合）→ `find_all`，它接受lambda、正则、属性字典，表达力更强；
- **只需要一个结果**：用 `select_one`/`find`，返回 None 还是 Tag 要显式判断，比 `select(...)[0]` 抛 IndexError 优雅。

### 3.4.2 属性提取与文本提取

```python
tag_link = soup.select_one("a.tag")
tag_link["href"]                        # 属性存在时直接取（不存在抛 KeyError）
tag_link.get("title", "默认值")          # 属性可能缺失时用 .get，容错
tag_link.get_text(strip=True)           # strip=True 去掉首尾空白，采集文本的默认姿势
```

`["href"]` 与 `.get("href")` 的分工与第 2 章 `raise_for_status` 的逻辑一脉相承：**预期必有的字段用硬取（缺失即炸，暴露问题）；预期可缺的字段用软取（给默认值，不让单条脏数据毁掉整批）**。

## 3.5 导航与正则配合

### 3.5.1 父子兄弟导航

有时候目标节点「没有可用的 class」，只能靠相对位置导航。看 quotes 站的真实结构（回顾第 1 章）：

```html
<span>by <small class="author" itemprop="author">Albert Einstein</small>
<a href="/author/Albert-Einstein">(about)</a>
</span>
```

已知 `small.author`，要拿到它后面的 `(about)` 链接：

```python
author_small = quote.find("small")
author_small.parent                  # 包裹层 <span>（注意不是 div.quote 容器！）
author_small.find_parent("div")      # 沿祖先向上找第一个 div -> 容器 div.quote
author_small.next_sibling            # '\n' —— 换行符也是节点！（几乎总是第一个坑）
author_small.find_next_sibling("a")  # 跳过文本节点，找下一个 <a> 兄弟
len(list(quote.children))            # 直接子节点数（含换行符文本节点）
```

**`.next_sibling` 与 `.find_next_sibling()` 的区别是本章最重要的坑**：HTML 里标签之间的换行和空格是真实的文本节点，`next_sibling` 大概率返回 `'\n'`；`find_next_sibling("a")` 才是「找下一个 a 标签兄弟」的正确姿势。同理有 `.previous_sibling`/`.find_previous_sibling()`、`.next_element`/`.previous_element`（不分层级的文档流遍历）。

### 3.5.2 正则配合

`find_all` 的参数几乎都接受正则，适合「结构有规律但值不确定」的场景：

```python
import re

soup.find_all(class_=re.compile(r"^quote$"))                # class 精确匹配 quote（避开 quote-footer 之类）
soup.find_all("small", string=re.compile(r"^[A-Z]"))        # 文本以大写字母开头的 small
soup.find_all("a", href=re.compile(r"^/tag/"))              # href 指向标签页的链接
```

注意 `string=` 匹配的是**标签的完整文本**（等于做了一次全匹配的 re.search），想匹配「文本包含某词」要写 `re.compile(r"包含词")`。

## 3.6 lxml XPath 入门

XPath 是 XML/HTML 的路径查询语言，比 CSS 选择器多了「按文本找节点、按位置取值、向上找父节点」的能力。Scrapy 的响应对象直接支持（`response.xpath(...)`，第 5 章会用），值得现在入个门：

```python
import lxml.html

tree = lxml.html.fromstring(html)
tree.xpath('//title/text()')                                    # 标题文本 -> ['Quotes to Scrape']
tree.xpath('//div[@class="quote"]')                             # 属性匹配，注意 @
tree.xpath('//small[@class="author"]/text()')                   # 所有作者文本
tree.xpath('//a[contains(@href, "/author/")]/text()')           # contains() 模糊匹配
tree.xpath('//th[text()="UPC"]/following-sibling::td/text()')   # 找到 UPCell 后取相邻 td（books 详情页实战用）
```

**`/` 与 `//` 的区别是 XPath 第一坑**，lab 里有专门演示：`//div[@class="quote"]/small[@class="author"]` 结果为 0——因为 `/` 要求 small 是 div 的**直接子节点**，而真实 HTML 里 small 外面还套着一层 span。写成 `//small[...]`（文档任意位置）或 `//div[@class="quote"]//small[...]`（div 的**后代**）才能命中。与 3.5.1 的 `next_sibling` 坑并称「层级理解错误双雄」。

常用速查：`@attr` 取属性条件、`text()` 取文本、`position()` 位置（`//a[1]` 第一个）、`..` 父节点、轴语法 `following-sibling::`/`ancestor::`。

## 3.8 文本提取再进一步：多段文本与遍历

`get_text()` 的完整签名是 `get_text(separator, strip)`，两个参数专治「一段文字散落在多个标签里」的场景。看 books 详情页的库存信息结构（第 5 章实战要用）：

```html
<p class="instock availability">In stock (5 available)</p>
```

这类结构好办；麻烦的是文本被内联标签切碎的情形：

```python
from bs4 import BeautifulSoup

html = "<p>价格 <b>£51.77</b>，含税</p>"
soup = BeautifulSoup(html, "lxml")
print(soup.p.get_text())                 # 默认无分隔符
print(soup.p.get_text("|"))              # 标签边界插入分隔符
print(soup.p.get_text("|", strip=True))  # 分隔符 + 去首尾空白
```

预期输出：

```text
价格 £51.77，含税
价格 |£51.77|，含税
价格|£51.77|，含税
```

| 写法 | 行为 | 适用 |
|---|---|---|
| `get_text()` | 深度优先拼接全部文本（含空白） | 默认姿势 |
| `get_text(strip=True)` | 拼接并去每段首尾空白 | 采集单字段文本的标准姿势 |
| `get_text("|", strip=True)` | 段间插入分隔符 | 保留结构线索（稍后 `split("\|")` 还原） |
| `tag.stripped_strings` | 迭代器，逐段给出去空白后的文本 | 想自己控制拼接/过滤逻辑时 |

还有一个容易混的属性 `tag.strings`（所有文本子节点的迭代器）与 `tag.string`（唯一文本子节点时才非 None，见 3.3 节）。**文本被切碎时 `string` 返回 None**，这是「明明有字却取不到」的第三大来源（前两名是 3.5.1 的空白兄弟节点与 3.6 的 `/`、`//`）。

## 3.9 完整解析函数：从 HTML 到结构化数据

把本章知识组装成一个生产级的解析函数——它正是第 2 章 `parse_page` 的 BeautifulSoup 版本，直接可以替换进那个爬虫。先看代码，再讲四个设计点：

```python
from bs4 import BeautifulSoup

def parse_quotes(html: str) -> tuple[list[dict], int]:
    """解析 quotes 列表页。

    返回 (quotes, skipped)：skipped 是结构不符被跳过的块数。
    单条脏数据只跳过不崩溃——解析函数的第一纪律。
    """
    soup = BeautifulSoup(html, "lxml")
    quotes: list[dict] = []
    skipped = 0
    for q in soup.select("div.quote"):
        text_node = q.select_one("span.text")
        author_node = q.select_one("small.author")
        if text_node is None or author_node is None:
            skipped += 1                 # 结构不符:计数并跳过,绝不带病入库
            continue
        quotes.append({
            "text": text_node.get_text(strip=True).strip("“”"),
            "author": author_node.get_text(strip=True),
            "tags": [a.get_text(strip=True) for a in q.select("a.tag")],
        })
    return quotes, skipped
```

四个设计点（每一条都在防一种真实事故）：

1. **每层取值判 None**：`select_one` 可能返回 None（站点改版），先判再用——3.4.2 的「软取/硬取」分工在解析层的体现；
2. **skipped 计数返回给调用方**：让「静默丢数据」变成「可观测的指标」，调用方可以打日志或报警（第 8 章 8.7 的数据量断言就建立在它之上）；
3. **清洗就近做**：`strip("“”")` 去智能引号在解析层完成，下游拿到的就是干净字符串——与第 5 章「Item 一产出就是干净形状」同一原则；
4. **选择器从容器开始**：`div.quote` → 容器内再选，而不是全页散选——避免标签语义在不同区块复用时错采。

对它做一次冒烟验证（沿用第 2 章下载的离线 HTML）：

```bash
python -c "
from pathlib import Path
import sys; sys.path.insert(0, 'projects/crawler-lab')
from importlib import import_module
html = Path('projects/crawler-lab/data/quotes_page1.html').read_text(encoding='utf-8')
quotes, skipped = parse_quotes(html)   # 函数来自本节代码,或已并入你的 lab
print(len(quotes), skipped, quotes[0]['author'])
"
```

预期输出：

```text
10 0 Albert Einstein
```

## 3.10 【实战】运行 lab：一份 HTML，六种武器

`projects/crawler-lab/03_parse_bs4.py` 在**离线**状态下把本章全部知识点串成一次演示：同一份 `quotes_page1.html`，依次用 find/find_all、select、属性/文本提取、导航、正则、XPath 各解析一遍，输出可逐一对照。前置：先跑过第 2 章 lab（生成了输入文件）。

```bash
source ~/opt/jjyv/bin/activate
python projects/crawler-lab/03_parse_bs4.py
```

预期输出（撰写时实测）：

```text
页面 <title>: Quotes to Scrape

find(class_='quote') 的 author: Albert Einstein
find_all 计数: 10
按 itemprop 属性找到作者数: 10

select('span.text') 计数: 10
select 容器内作者: Albert Einstein
属性选择器作者链接数: 10

第一条名言：
  get_text(strip=True): “The world as we have created it is a process of o ...
  ['href'] 取属性: /tag/change/page/1/
  .get() 容错取属性: (无 title 属性时的默认值)
  attrs 字典: {'class': ['tag'], 'href': '/tag/change/page/1/'}

导航演示：
  .parent 是包裹层: span | .find_parent('div') 才是容器: ['quote']
  .next_sibling 跳过换行符: '\n' ...
  .find_next_sibling('a') 找到下一元素: /author/Albert-Einstein
  容器内直接文本子节点数: 7

re 配合 find_all 计数: 10
本页作者集合大小: 8

XPath 子轴 /small 结果数（扑空）: 0
XPath 后代轴 //small 结果数: 10 | 第一个: Albert Einstein
```

对照输出自查三个教学点：

1. 「容器内直接文本子节点数: 7」——不是 4（4 个子标签）也不是 3，因为**换行符文本节点都在**，这就是 3.5.1 说的坑的实锤；
2. 「本页作者集合大小: 8」——10 条名言 8 位作者，说明同页有重复作者（用了 `set`），聚合统计时常忘去重；
3. 「XPath 子轴 /small 结果数（扑空）: 0」——3.6 节 `/` 与 `//` 区别的实锤。

## 常见坑与排查（Troubleshooting）

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `soup.select_one(...)` 返回 None，浏览器里明明有 | 选择器基于渲染后 DOM 写的；或数据由 JS 渲染 | 先「查看源代码」确认节点真的在 HTML 里（第 1 章 1.5 节）；确实 JS 渲染走第 7 章 |
| `AttributeError: 'NoneType' object has no attribute 'text'` | 上一步 select/find 返回 None 还继续取属性 | 每层取值前判断 None；用 `tag.find("x")` 后再 `.get_text()` 的写法时尤其注意 |
| `.next_sibling` 拿到的是 `'\n'` | 标签间空白是真实文本节点 | 用 `find_next_sibling("tag")`，见 3.5.1 |
| `class_` 写成 `class` 报语法错 | class 是 Python 关键字 | bs4 用 `class_` 参数；或统一用 `select`/`attrs` |
| XPath 表达式 `//div/small` 结果为 0 | `/` 只匹配直接子节点，中间隔了层 span | 后代用 `//`，见 3.6；从最近的稳定容器逐层验证 |
| 文本里混着大量空白和换行 | HTML 缩进进了文本节点 | `get_text(strip=True)`；多段文本用 `get_text("|", strip=True)` 拼接 |
| bs4 解析比预期慢 | 用了 html.parser 或页面极大 | 换 lxml 引擎；只解析需要的片段（`BeautifulSoup(fragment)`） |
| 同一段代码昨天能跑今天选择器失效 | 站点改版 | 给解析函数加「命中数为 0 即告警」的保护（呼应第 8 章监控），别硬编码一次成功的选择器就不管了 |
| 解析中文乱码 | 上游 encoding 猜错（第 2 章 2.3 的坑传导下来） | 在请求层修复：`r.encoding = "utf-8"` 后再交给 bs4 |

## 动手练习

1. **两种 API 各写一遍**：基于 `quotes_page1.html`，分别用 find_all 和 select 完成同一个任务——提取全部 10 条名言的 (text, author, 标签列表)，两种写法的输出必须完全一致（用 `==` 验证）。
   <details><summary>提示</summary>find_all 路线：`q.find("span", class_="text")`；select 路线：`q.select_one("span.text")`。标签列表用列表推导处理每个容器。</details>
2. **XPath 强化训练**：用 lxml 完成三个任务——(a) 本页共多少个 `(about)` 链接；(b) 提取每个名言块 meta 标签的 `content` 属性（keywords）；(c) 找到 `li.next` 里 a 的 href。
   <details><summary>提示</summary>(a) `//a[text()="(about)"]`；(b) `//meta[@class="keywords"]/@content`；(c) `//li[@class="next"]/a/@href`。注意 @content 是属性不是 text()。</details>
3. **容错改造**：把 lab 的解析逻辑抽成一个 `parse_quotes(html) -> list[dict]` 函数，要求：任何一条名言解析失败只跳过该条并计数，函数末尾返回 (quotes, skipped)；构造一个破坏过的 HTML（删掉某个 author 标签）验证 skipped 计数。
   <details><summary>提示</summary>结构与第 2 章 parse_page 相同，只是把正则换成 bs4。skipped>0 时打日志——呼应「静默丢数据」教训。</details>
4. **books 详情页预习**：下载一个 books.toscrape.com 详情页（如 `https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html`）到本地，用 bs4 + XPath 各提取书名、价格、UPC、库存文案，为第 5 章 Scrapy 实战做热身。
   <details><summary>提示</summary>UPC 用 XPath 轴写法最顺：`//th[text()="UPC"]/following-sibling::td/text()`（第 5 章 spider 里就是这行）。价格记得处理 £ 与 encoding。</details>

## 小结与自检清单

- [ ] 我知道解析器怎么选：默认 bs4+lxml，零依赖兜底 html.parser，Scrapy 内部是 lxml+XPath
- [ ] 我能解释 class 属性返回列表、.string 的 None 陷阱、get_text(strip=True) 的默认姿势
- [ ] find/find_all 与 select/select_one 我都能用，知道各自的适用场景
- [ ] 我被（或将避免）next_sibling 返回换行符的坑教育过，知道 find_next_sibling 才是正解
- [ ] 我理解 XPath 的 / 与 // 区别，会用 @属性、text()、contains()、following-sibling:: 轴
- [ ] 我跑通了 lab，三处教学点（子节点数 7、作者集合 8、/small 扑空）都能解释原因
- [ ] 遇到「解析不到」时，我会先查渲染差异，再查编码，再逐层验证选择器

## 延伸阅读

- [BeautifulSoup 官方中文文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/)——find_all 与 select 全参数说明，3.4 节的权威展开。
- [lxml 官方文档：xpath 用法](https://lxml.de/xpathxslt.html)——纯 lxml 的 XPath 支持（英文），配合 XPath 教程阅读。
- [MDN：CSS 选择器](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_selectors)——select() 语法即 CSS 选择器，第 1 章已收藏过，本章真正用上。
- [XPath 语法（W3Schools 中文）](https://www.w3schools.cn/xml/xpath_syntax.asp)——轴与函数速查，入门友好。
- 上一章：[requests 爬虫实战](02-requests爬虫实战.md)；下一章：[数据存储（CSV / JSON / SQLite / MySQL）](04-数据存储(csv-json-SQLite-MySQL).md)。
