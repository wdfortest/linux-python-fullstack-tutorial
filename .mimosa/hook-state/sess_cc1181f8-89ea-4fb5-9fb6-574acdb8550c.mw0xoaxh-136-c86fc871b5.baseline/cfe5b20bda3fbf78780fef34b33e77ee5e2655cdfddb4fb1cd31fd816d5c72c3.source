"""spiders/books.py：全站抓取 books.toscrape.com 的 CrawlSpider 示例。

CrawlSpider 用 Rule 声明“哪些链接跟进、哪些链接解析”，
翻页与跨类目跳转全部交给 LinkExtractor，Spider 代码里不用手写循环。
"""

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from book_scrapy.items import BookItem

# 详情页 star-rating 类名 -> 数字评分
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(CrawlSpider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    rules = (
        # 规则 1：分类列表页（含分页 page-N.html）——只跟进链接，不产出 Item。
        # /catalogue/category/books_1/ 是“全部图书”总分类，也要纳入。
        Rule(
            LinkExtractor(allow=(r"/catalogue/category/books/", r"/catalogue/category/books_1/")),
            follow=True,
        ),
        # 规则 2：图书详情页（/catalogue/<slug>/index.html，且排除 category 路径）
        # 交给 parse_book 解析；follow=False 表示详情页里不再继续扩散。
        Rule(
            LinkExtractor(
                allow=r"/catalogue/[^/]+/index\.html",
                deny=r"/catalogue/category/",
            ),
            callback="parse_book",
            follow=False,
        ),
    )

    def parse_book(self, response: scrapy.http.Response):
        """解析一本图书的详情页，产出 BookItem。"""
        # 数据清洗放在 Spider 层：让 Item 一产出就是“干净形状”
        price_text = response.css("p.price_color::text").get("")
        rating_word = response.css("p.star-rating::attr(class)").re_first(r"star-rating (\w+)")
        stock_text = response.xpath(
            '//th[contains(text(), "Availability")]/following-sibling::td/text()'
        ).get("")
        # "In stock (5 available)" -> 5；缺货页是 "In stock" 或 "Out of stock"
        qty = "".join(ch for ch in stock_text if ch.isdigit()) or "0"

        item = BookItem()
        item["upc"] = response.xpath('//th[text()="UPC"]/following-sibling::td/text()').get()
        item["title"] = response.css("div.product_main h1::text").get()
        # 面包屑：Home / Books / <分类名>，倒数第二个 li 就是分类
        item["category"] = response.css("ul.breadcrumb li a::text")[-1].get()
        item["price"] = float(price_text.replace("£", "").strip()) if "£" in price_text else None
        item["rating"] = RATING_MAP.get(rating_word, 0)
        item["in_stock"] = "in stock" in stock_text.lower()
        item["stock_qty"] = int(qty)
        item["url"] = response.url
        yield item
