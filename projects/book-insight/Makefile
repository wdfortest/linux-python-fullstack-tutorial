.PHONY: crawl analyze serve test all

# book-insight 一键脚本（macOS/Linux）
# 用法示例：make crawl / make analyze / make serve / make test / make all

PY ?= python

crawl:            ## 重新全量采集图书数据（约几分钟）
	$(PY) crawler/crawl_books.py

analyze:          ## 生成 stats.json 与 matplotlib 图表
	$(PY) analysis/analyze.py

serve:            ## 启动 FastAPI + 大屏（http://127.0.0.1:8000/）
	$(PY) -m uvicorn api.main:app --reload

test:             ## 运行接口测试
	$(PY) -m pytest tests/ -v

all: crawl analyze test serve
