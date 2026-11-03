"""settings.py：Scrapy 项目的所有开关集中在这里。

写作规范提醒：ROBOTSTXT_OBEY、DOWNLOAD_DELAY 这类“礼貌开关”不是可选项，
是本仓库爬虫教程的硬性规范，读者不得关闭。
"""

from pathlib import Path

# data/ 目录位于 crawler-lab/ 下（settings.py 往上数三级）
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

BOT_NAME = "book_scrapy"

SPIDER_MODULES = ["book_scrapy.spiders"]
NEWSPIDER_MODULE = "book_scrapy.spiders"

# ------------------------------------------------------------------
# 礼貌与合规（硬性规范，不得调低）
# ------------------------------------------------------------------
# 遵守 robots.txt。本站 robots.txt 返回 404，按 RFC 9309 语义等于“无限制”，
# 但开关必须开着：换到任何真实站点时它就是第一道合规防线。
ROBOTSTXT_OBEY = True

# 同一域名两次请求之间的最小间隔（秒）。0.3 是练习站的底线。
DOWNLOAD_DELAY = 0.3

# 并发请求数。对单一站点，并发 8 + 延迟 0.3 已经足够快，不要开更高。
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# AutoThrottle：根据响应速度自动调节延迟，目标并发 2 意味着“下游大概率同时只有 2 个请求在飞”。
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.3
AUTOTHROTTLE_MAX_DELAY = 5.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# 超时（秒），防止个别请求挂住整个队列
DOWNLOAD_TIMEOUT = 20

# ------------------------------------------------------------------
# 身份标识
# ------------------------------------------------------------------
# 教育用途 UA。真实项目里请填你的联系方式，站点管理员遇到问题可以找到你。
USER_AGENT = "book-scrapy-edu/1.0 (Scrapy tutorial; educational use only)"

# ------------------------------------------------------------------
# 采集量控制与输出
# ------------------------------------------------------------------
# 保险丝：books.toscrape.com 全站恰好 1000 本书，达到 1000 条 Item 后自动停止，
# 防止规则配错导致无限抓取。
CLOSESPIDER_ITEMCOUNT = 1000

# FEEDS：把 Item 流同时导出一份 JSON（overwrite=True 每次重写）
FEEDS = {
    str(DATA_DIR / "books.json"): {
        "format": "json",
        "encoding": "utf-8",
        "overwrite": True,
        "indent": 2,
    }
}

# ------------------------------------------------------------------
# 中间件与管线
# ------------------------------------------------------------------
DOWNLOADER_MIDDLEWARES = {
    # 400 的位置紧跟默认 UserAgentMiddleware 之后，可以覆盖它的值
    "book_scrapy.middlewares.RandomUserAgentMiddleware": 400,
}

ITEM_PIPELINES = {
    "book_scrapy.pipelines.SQLitePipeline": 300,
}

# ------------------------------------------------------------------
# 卫生与杂项
# ------------------------------------------------------------------
# 本站不需要登录态，关闭 Cookie 既是礼貌也避免无谓的状态
COOKIES_ENABLED = False
# 关闭 telnet 调试端口：默认打开的 6023 端口是个不必要的安全面
TELNETCONSOLE_ENABLED = False
# 关闭响应缓存（调试时可以临时打开）
HTTPCACHE_ENABLED = False

LOG_LEVEL = "INFO"

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
