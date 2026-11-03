# 第 05 章 · ECharts 数据可视化

> 5 篇 · 配套代码：`projects/echarts-lab/`（全部页面可直接打开，或 `python -m http.server 8060` 预览）
> ECharts 6.1.0（配置面与 5.x 基本一致）

从零基础四步法，到能独立交付一张可联动、可响应式的深色数据大屏。

## 目录

| # | 文档 | 内容一句话 | lab 页面 |
|---|---|---|---|
| 01 | [ECharts 快速上手](01-ECharts快速上手.md) | 选型对比、四步法、option 心智模型、三大新手坑 | `01_quick_start.html` |
| 02 | [常用图表类型详解](02-常用图表类型详解.md) | 选型决策树、6 类高频图的关键配置与「不适用」边界 | `charts.html`（6 图一页） |
| 03 | [异步数据与 API 对接](03-异步数据与API对接.md) | 五步加载流程、CORS、轮询去重与暂停、契约先行 | `03_async_data.html`（模拟成功/失败/轮询） |
| 04 | [Dashboard 设计：布局与联动](04-Dashboard设计-布局与联动.md) | 三级版式、F 型动线、connect 与事件过滤联动、深色配色规范 | `04_dashboard_layout.html` |
| 05 | [进阶：主题、动画、性能与生态](05-进阶(主题-动画-性能-Vue集成-pyecharts).md) | registerTheme、10 万点三板斧、Vue3 集成、pyecharts 路线 | `05_theme_and_perf.html` |

## 学完你能做到

- 独立完成「选型 → 布局 → 数据对接 → 联动 → 性能」的完整可视化交付
- 能看懂并改进第 07 章实战项目的大屏（[ECharts 大屏实战](../07-final-project/04-ECharts大屏实战.md)）

## 本地预览方法

```bash
cd projects/echarts-lab
python -m http.server 8060
# 浏览器打开 http://127.0.0.1:8060/01_quick_start.html 等
```

所有页面均内置 CDN 兜底（jsdelivr 不可达自动切 npmmirror）。

← 返回 [总目录](../../README.md)
