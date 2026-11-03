"""02 章 lab：requests 完整抓取 quotes.toscrape.com 全部 10 页名言。

目标站点：quotes.toscrape.com（Scrapy 官方维护的爬虫练习站，明确欢迎抓取）。
采集内容：每条名言的正文、作者、标签，共 10 页约 100 条。
产出：data/quotes.json（全量数据）、data/quotes_page1.html（第 1 页原始 HTML，供 03 章 lab 练习解析）。

运行方式（在仓库根目录或本目录均可）：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/02_requests_quotes.py
"""

import json
import re
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# 全局约定：每个爬虫脚本都应该在开头写清这四件事
# ---------------------------------------------------------------------------
BASE_URL = "https://quotes.toscrape.com"
# 1. User-Agent 标明教育用途，不伪装成浏览器（对练习站尤其要诚实）
HEADERS = {
    "User-Agent": "crawler-lab-edu/1.0 (Python tutorial; educational use only)",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
# 2. 请求间隔 >= 0.3s，做礼貌的爬虫（politeness delay）
DELAY_SECONDS = 0.5
# 3. 超时必须显式设置，绝不让脚本无限等待
TIMEOUT = 10
# 4. 输出目录：始终写到本脚本同级的 data/ 下
DATA_DIR = Path(__file__).resolve().parent / "data"


def fetch_with_retry(session: requests.Session, url: str, max_retries: int = 3) -> requests.Response:
    """带重试的 GET 封装：网络抖动、临时 5xx 时自动退避重试。

    为什么需要它：单次请求失败就崩溃的爬虫，跑不了 10 分钟。
    退避（backoff）让重试间隔逐次变长，避免在服务器抖动时火上浇油。
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()  # 4xx/5xx 直接抛异常，交给重试逻辑
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = 0.5 * attempt  # 指数退避的简化版：0.5s, 1.0s, 1.5s
                print(f"  [retry] 第 {attempt} 次请求 {url} 失败（{exc}），{wait}s 后重试")
                time.sleep(wait)
    raise RuntimeError(f"重试 {max_retries} 次后仍失败：{url}") from last_exc


def parse_page(html: str) -> list[dict]:
    """从一页 HTML 中抽取名言列表（02 章用正则做轻量解析，03 章换成 BeautifulSoup）。"""
    quotes: list[dict] = []
    # 每个 .quote 块包含：span.text、small.author、若干 a.tag
    for block in re.findall(r'<div class="quote".*?</div>', html, flags=re.S):
        text_m = re.search(r'<span class="text"[^>]*>(.*?)</span>', block, flags=re.S)
        author_m = re.search(r'<small class="author"[^>]*>(.*?)</small>', block, flags=re.S)
        tags = re.findall(r'<a class="tag" href="[^"]*">(.*?)</a>', block)
        if not (text_m and author_m):
            continue  # 结构不符预期的块直接跳过，不让单条脏数据毁掉整页
        quotes.append(
            {
                "text": text_m.group(1).replace("&ldquo;", "").replace("&rdquo;", "").strip(),
                "author": author_m.group(1).strip(),
                "tags": [t.strip() for t in tags],
            }
        )
    return quotes


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    session = requests.Session()  # 复用 TCP 连接，10 页共享一个连接池

    all_quotes: list[dict] = []
    url: str | None = BASE_URL + "/page/1/"
    pages = 0

    # “下一页”翻页模式：跟着 li.next 走，不硬编码页数——站点加页时脚本不用改
    while url:
        resp = fetch_with_retry(session, url)
        pages += 1
        page_quotes = parse_page(resp.text)
        all_quotes.extend(page_quotes)
        print(f"第 {pages} 页 {url} -> {len(page_quotes)} 条名言")

        if pages == 1:
            # 留一份原始 HTML 给 03 章 lab 做离线解析练习
            (DATA_DIR / "quotes_page1.html").write_text(resp.text, encoding="utf-8")

        # 找“下一页”链接（rel=next）
        next_m = re.search(r'<li class="next">\s*<a href="([^"]+)"', resp.text)
        url = BASE_URL + next_m.group(1) if next_m else None
        time.sleep(DELAY_SECONDS)

    result = {
        "source": BASE_URL,
        "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(all_quotes),
        "quotes": all_quotes,
    }
    out_path = DATA_DIR / "quotes.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n共 {pages} 页 {len(all_quotes)} 条名言 -> {out_path}")


if __name__ == "__main__":
    main()
