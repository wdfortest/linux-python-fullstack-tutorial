"""01 章 lab：用 requests 抓取并解读 robots.txt。

robots.txt 是站点对爬虫的“公开意愿声明”。本章两个练习站点都没有部署 robots.txt
（请求返回 404），按 RFC 9309 的语义：robots.txt 无法获取（404）等于“对本站无限制”。
这个脚本演示标准读法，换到任何站点都能用。

本脚本同时演示 SSRF 防护三件套（协议白名单 + 域名白名单 + 解析 IP 非私网校验）——
任何「根据输入发请求」的代码都应具备这三层校验，详见第 06 章合规讨论。

运行：
    source ~/opt/jjyv/bin/activate
    python projects/crawler-lab/01_fetch_robots.py
"""

import ipaddress
import socket

import requests
from urllib.parse import urlsplit, urljoin

# 严格白名单：本教程的爬虫实验只允许这两个练习站点（见第 06 章合规红线）
ALLOWED_HOSTS = {"quotes.toscrape.com", "books.toscrape.com"}
HEADERS = {"User-Agent": "crawler-lab-edu/1.0 (educational use only)"}


def assert_public_https(url: str) -> str:
    """SSRF 防护：协议白名单 + 域名白名单 + 解析 IP 检查。

    返回规范化后的 robots.txt 地址；不合规直接抛 ValueError。

    ⚠️ 真实环境现象（教学价值）：本脚本作者机器上开着 fake-IP 模式代理，
    外部域名会被解析到 198.18.0.0/15（RFC 2544 基准测试段，ipaddress 视为
    私网）。因此 IP 检查在此「降级为警告」；生产服务的 SSRF 防护必须**硬阻断**，
    且要防 DNS rebinding（先校验的 IP 与实际连接的 IP 可能不同）。
    """
    parts = urlsplit(url)
    if parts.scheme != "https" or (parts.hostname or "") not in ALLOWED_HOSTS:
        raise ValueError(f"目标不在白名单内: {url}")
    for family, _, _, _, sockaddr in socket.getaddrinfo(parts.hostname, 443):
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            print(f"   [SSRF 警告] {parts.hostname} 解析到非常规地址 {ip}（本机多为代理 fake-IP），生产环境应阻断")
            break
    return urljoin(url, "robots.txt")


def fetch_robots(base_url: str) -> None:
    """抓取并解读一个站点的 robots.txt。"""
    url = assert_public_https(base_url)
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"== {url} -> HTTP {resp.status_code}")

    if resp.status_code == 200:
        # 200：逐段解析 User-agent / Disallow / Allow / Crawl-delay / Sitemap
        agent = "*"
        for raw in resp.text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            field, _, value = line.partition(":")
            field, value = field.strip().lower(), value.strip()
            if field == "user-agent":
                agent = value
            elif field == "disallow":
                print(f"   [{agent}] Disallow: {value or '(空串=全站允许)'}")
            elif field == "allow":
                print(f"   [{agent}] Allow: {value}")
            elif field == "crawl-delay":
                print(f"   [{agent}] Crawl-delay: {value} 秒")
            elif field == "sitemap":
                print(f"   Sitemap: {value}")
        if agent == "*" and "Disallow" not in resp.text:
            print("   （没有任何 Disallow 规则）")
    elif resp.status_code == 404:
        # RFC 9309：robots.txt 返回 404 表示“无限制”，但仍需自觉限速、标明身份
        print("   404 -> 站点未部署 robots.txt，语义为「未声明限制」，并非「欢迎狂抓」")
    elif resp.status_code in (401, 403):
        # RFC 9309：401/403 表示“robots.txt 本身不可读”，保守解释为对本站全站不允许
        print("   401/403 -> 按 RFC 9309 应保守处理：视为不允许抓取")
    else:
        print("   其他状态码，按站点实际情况判断")
    print()


if __name__ == "__main__":
    for site in sorted(ALLOWED_HOSTS):
        fetch_robots(f"https://{site}")
