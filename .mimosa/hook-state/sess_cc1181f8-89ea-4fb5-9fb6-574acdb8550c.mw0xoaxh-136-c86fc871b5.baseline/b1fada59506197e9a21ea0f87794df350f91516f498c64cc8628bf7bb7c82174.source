"""items.py：声明采集的数据结构。

Item 相当于“数据的合同”：Spider 只负责往里填字段，
清洗、校验、存储交给后面的 Pipeline，各组件职责分离。
"""

import scrapy


class BookItem(scrapy.Item):
    # 一本图书的完整画像。字段名与详情页的一一对应，便于排查漏采
    upc = scrapy.Field()        # 国际标准产品码，全站唯一 -> 用作去重键
    title = scrapy.Field()      # 书名
    category = scrapy.Field()   # 所属分类（面包屑导航第二级）
    price = scrapy.Field()      # 价格（浮点，已去掉货币符号）
    rating = scrapy.Field()     # 评分（1-5 的整数，来自 star-rating 类名）
    in_stock = scrapy.Field()   # 是否有货（布尔）
    stock_qty = scrapy.Field()  # 库存数量（"In stock (5 available)" 中的 5，缺货记 0）
    url = scrapy.Field()        # 详情页地址
