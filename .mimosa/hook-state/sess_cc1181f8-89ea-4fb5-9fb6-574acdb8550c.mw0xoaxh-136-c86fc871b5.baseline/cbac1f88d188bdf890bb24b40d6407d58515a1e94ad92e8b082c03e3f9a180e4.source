"""book_scrapy：Scrapy 框架教程项目，目标站点 books.toscrape.com（明确欢迎抓取的练习站）。

抓取范围：全站 1000 本图书（书名 / 分类 / 价格 / 评分 / 库存 / UPC），
经 Item Pipeline 去重后写入 SQLite（projects/crawler-lab/data/books.db），
同时经 FEEDS 导出 JSON（projects/crawler-lab/data/books.json）。

运行（必须在本目录下执行，scrapy 依赖 scrapy.cfg 定位 settings）：
    source ~/opt/jjyv/bin/activate
    cd projects/crawler-lab/book_scrapy
    scrapy crawl books
"""
