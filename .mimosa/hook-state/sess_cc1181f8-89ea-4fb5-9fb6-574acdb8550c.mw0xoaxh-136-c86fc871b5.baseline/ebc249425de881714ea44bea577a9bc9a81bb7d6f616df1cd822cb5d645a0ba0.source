"""03 章 lab：用 BeautifulSoup + lxml 解析已下载的 quotes 页面（离线，不发请求）。

输入：data/quotes_page1.html（由 02_requests_quotes.py 下载）。
内容：soup 对象模型、find/find_all、CSS 选择器 select、属性/文本提取、
父子兄弟导航、正则配合。全部操作都基于同一份 HTML，方便对照结果。

运行：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/03_parse_bs4.py
"""

import re
from pathlib import Path

from bs4 import BeautifulSoup

HTML_PATH = Path(__file__).resolve().parent / "data" / "quotes_page1.html"


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    # ---------- 1. 用 lxml 引擎构建 soup ----------
    soup = BeautifulSoup(html, "lxml")
    print("页面 <title>:", soup.title.string)

    # ---------- 2. find / find_all：按标签与属性定位 ----------
    first_quote = soup.find("div", class_="quote")            # 第一条名言的容器
    print("\nfind(class_='quote') 的 author:",
          first_quote.find("small", class_="author").string)

    all_quotes = soup.find_all("div", class_="quote")          # 本页全部名言
    print("find_all 计数:", len(all_quotes))
    # 按任意 HTML 属性匹配（无 class 可用时用 attrs 字典，如 schema.org 的 itemprop）
    authors = soup.find_all(attrs={"itemprop": "author"})
    print("按 itemprop 属性找到作者数:", len(authors))

    # ---------- 3. CSS 选择器 select：与 find_all 等价但更贴近前端习惯 ----------
    print("\nselect('span.text') 计数:", len(soup.select("span.text")))
    # 组合选择器：容器内的第一个作者
    print("select 容器内作者:", soup.select_one("div.quote small.author").string)
    # 属性选择器：href 以 /author/ 开头的链接
    print("属性选择器作者链接数:", len(soup.select('a[href^="/author/"]')))

    # ---------- 4. 属性提取与文本提取 ----------
    q0 = all_quotes[0]
    tag_link = q0.select_one("a.tag")
    print("\n第一条名言：")
    print("  get_text(strip=True):", q0.select_one("span.text").get_text(strip=True)[:50], "...")
    print("  ['href'] 取属性:", tag_link["href"])
    print("  .get() 容错取属性:", tag_link.get("title", "(无 title 属性时的默认值)"))
    print("  attrs 字典:", {k: v for k, v in tag_link.attrs.items() if k in ("href", "class")})

    # ---------- 5. 父子兄弟导航 ----------
    author_small = q0.find("small")
    print("\n导航演示：")
    print("  .parent 是包裹层:", author_small.parent.name,        # span（“by <small>”的包裹层）
          "| .find_parent('div') 才是容器:", author_small.find_parent("div")["class"])
    print("  .next_sibling 跳过换行符:", repr(author_small.next_sibling)[:20], "...")
    print("  .find_next_sibling('a') 找到下一元素:", author_small.find_next_sibling("a")["href"])
    print("  容器内直接文本子节点数:", len(list(q0.children)))

    # ---------- 6. 与正则配合：re 参数直接作用于标签/属性 ----------
    rating_divs = soup.find_all(class_=re.compile(r"^quote$"))   # class 正则匹配
    print("\nre 配合 find_all 计数:", len(rating_divs))
    authors = {a.string for a in soup.find_all("small", string=re.compile(r"^[A-Z]"))}
    print("本页作者集合大小:", len(authors))

    # ---------- 7. 对比：XPath（lxml）只做一次演示，详见正文 ----------
    import lxml.html
    tree = lxml.html.fromstring(html)
    # 坑：/ 是“直接子节点”，small 外面套着一层 span，直接写 /small 会扑空
    child_axis = tree.xpath('//div[@class="quote"]/small[@class="author"]/text()')
    descendant = tree.xpath('//div[contains(@class,"quote")]//small[@class="author"]/text()')
    print("XPath 子轴 /small 结果数（扑空）:", len(child_axis))
    print("XPath 后代轴 //small 结果数:", len(descendant), "| 第一个:", descendant[0])


if __name__ == "__main__":
    main()
