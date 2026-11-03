"""08 章 lab：asyncio + httpx 异步并发抓取 quotes.toscrape.com 全部 10 页。

并发纪律（本章核心）：
- asyncio.Semaphore(5)：同时在飞的请求最多 5 个；
- 每个请求完成后 sleep 0.3s：保证对同一站点的请求间隔 >= 0.3s；
- 并发是“少占你的时间”，限速是“少占服务器的时间”，两者必须同时做。

运行：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/08_async_httpx.py
"""

import asyncio
import json
import re
import time
from pathlib import Path

import httpx

BASE_URL = "https://quotes.toscrape.com"
HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (async tutorial; educational use only)"}
DELAY_SECONDS = 0.3   # 每个请求之后的礼貌间隔
MAX_CONCURRENCY = 5   # 信号量：同时进行的请求数上限
DATA_DIR = Path(__file__).resolve().parent / "data"


async def fetch_page(client: httpx.AsyncClient, sem: asyncio.Semaphore, page: int) -> str:
    """抓一页：先抢信号量，再请求，再限速。三步都不能省。"""
    async with sem:                      # 最多 5 个协程同时进入
        resp = await client.get(f"{BASE_URL}/page/{page}/", headers=HEADERS)
        resp.raise_for_status()
        await asyncio.sleep(DELAY_SECONDS)  # 限速发生在每个请求之后
        return resp.text


def parse_page(html: str) -> list[dict]:
    quotes = []
    for block in re.findall(r'<div class="quote".*?</div>', html, flags=re.S):
        text_m = re.search(r'<span class="text"[^>]*>(.*?)</span>', block, flags=re.S)
        author_m = re.search(r'<small class="author"[^>]*>(.*?)</small>', block, flags=re.S)
        tags = re.findall(r'<a class="tag" href="[^"]*">(.*?)</a>', block)
        if text_m and author_m:
            quotes.append({
                "text": text_m.group(1).replace("&ldquo;", "").replace("&rdquo;", "").strip(),
                "author": author_m.group(1).strip(),
                "tags": [t.strip() for t in tags],
            })
    return quotes


async def main() -> None:
    start = time.time()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    async with httpx.AsyncClient(timeout=10) as client:   # AsyncClient 内部管理连接池
        # 一次性提交 10 个协程，由事件循环 + 信号量共同调度
        tasks = [fetch_page(client, sem, p) for p in range(1, 11)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    pages, all_quotes, errors = 0, [], []
    for page, result in enumerate(results, start=1):
        if isinstance(result, Exception):
            errors.append((page, result))       # 异常被 gather 原样带回，不炸整个批次
            print(f"第 {page} 页失败: {result}")
        else:
            page_quotes = parse_page(result)
            all_quotes.extend(page_quotes)
            pages += 1

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "quotes_async.json"
    out.write_text(
        json.dumps({"source": BASE_URL, "count": len(all_quotes), "quotes": all_quotes},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"成功 {pages}/10 页，共 {len(all_quotes)} 条名言 -> {out}")
    if errors:
        print(f"失败页: {errors}")
    print(f"总耗时 {time.time() - start:.1f}s（串行需约 10×(0.3+网络) 秒）")


if __name__ == "__main__":
    asyncio.run(main())
