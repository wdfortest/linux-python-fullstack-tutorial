"""middlewares.py：下载中间件示例——UA 轮换。

下载中间件位于 Engine 和 Downloader 之间，能改写每一个出站请求。
这里演示最简单也最常用的一种：给每个请求随机挑一个 User-Agent。

注意：本仓库的红线是“标明教育用途、诚实标识”，所以 UA 池里的每一项
都写明 educational use，而不是伪装成真实浏览器去欺骗目标站点。
"""

import secrets

EDUCATIONAL_USER_AGENTS = [
    "book-scrapy-edu/1.0 (Scrapy tutorial; educational use only)",
    "crawler-lab-edu/1.0 (Python tutorial; educational use only)",
    "crawler-lab-edu/1.0 (student exercise; educational use only)",
]


class RandomUserAgentMiddleware:
    """每个请求出发前随机挑选一个教育用途 User-Agent。"""

    def __init__(self, user_agents: list[str]):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):
        # from_crawler 是中间件的标准入口：从 settings 读配置、接线信号
        return cls(user_agents=crawler.settings.getlist("EDUCATIONAL_USER_AGENTS", EDUCATIONAL_USER_AGENTS))

    def process_request(self, request, spider):
        request.headers["User-Agent"] = secrets.choice(self.user_agents)
        return None  # 返回 None 表示“继续走正常流程”
