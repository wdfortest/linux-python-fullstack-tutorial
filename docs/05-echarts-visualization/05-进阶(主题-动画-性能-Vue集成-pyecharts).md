# 05.5 · 进阶：主题、动画、性能与生态

> 本章配套代码：`projects/echarts-lab/05_theme_and_perf.html`（10 万点实测渲染）
> 本地预览：`cd projects/echarts-lab && python -m http.server 8060` 后打开 `05_theme_and_perf.html`

## 学习目标

- 会用内置 dark 与 registerTheme 定制主题（JSON 结构）
- 掌握大数据量的三板斧：large、sampling、progressive + dataZoom
- 了解 Vue3/React 集成路径与 pyecharts 服务端生成方案
- 知道什么时候**不要**过度优化

## 5.5.1 主题

### 内置 dark（一行的事）

```js
echarts.init(dom, "dark");   // 第二参数即主题名
```

### registerTheme 自定义主题

```js
echarts.registerTheme("brand", {
  backgroundColor: "#111827",
  textStyle: { color: "#e5e7eb" },
  color: ["#38bdf8", "#a78bfa", "#fbbf24", "#34d399"],   // 分类色板
  title: { textStyle: { color: "#f9fafb" } },
  legend: { textStyle: { color: "#9ca3af" } },
});
echarts.init(dom, "brand");
```

主题 JSON 的结构与 option 同构——它就是「全局默认值」。本项目第 07 章大屏没有用整主题，而是把统一的 `baseOption()` 函数作为轻量主题（更灵活，可带运行时参数），两种路线都常见。

**注意**：主题必须在 init 时指定，不能事后切换；要切换就重建实例。5.x 注册过的主题在 6.x 中继续可用（6 的升级指南标注了少量视觉默认值变化，迁移成本极低）。

## 5.5.2 动画

```js
series: [{
  animationDuration: 600,          // 入场时长
  animationEasing: "cubicOut",     // 缓动曲线
}]
```

原则：**分析型图表动画要短**（300~600ms），监控大屏不要循环动画（除非是告警呼吸效果）。动画服务于「理解数据变化」，不是为了炫技。

## 5.5.3 大数据量三板斧（10 万点实测）

lab 05 在本机实测（Chrome，M 系列 Mac）：**10 万散点渲染仅约 48ms**，关键配置：

```js
series: [{
  type: "scatter",
  data: 十万个点,
  large: true,                 // ① 大数据模式（关闭逐点 hover 事件等）
  largeThreshold: 5000,
  symbolSize: 4,
  itemStyle: { opacity: 0.35 }, // ② 半透明叠加看出密度
  progressive: 20000,           // ③ 分批渲染，不阻塞主线程
  progressiveThreshold: 50000,
}],
dataZoom: [{ type: "inside" }, { type: "slider" }],   // ④ 缩放探查
```

决策顺序（先思考后配置）：

1. **真的需要 10 万点吗？**——展示用先抽样/聚合（第 07 章大屏只取 500 点抽样）；探索用再全量
2. 直方图/密度图往往比裸散点更能回答问题
3. 确需全量：large + progressive + dataZoom

折线/柱状同理：`sampling: "average"`/`"lttb"`（LTTB 降采样保留视觉形状）配 `dataZoom`。

## 5.5.4 与框架/生态集成

### Vue3 集成指引（约 30 行的最小封装）

```vue
<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import * as echarts from "echarts";

const el = ref(null);
let chart = null;

onMounted(() => {
  chart = echarts.init(el.value);
  chart.setOption({ /* ... */ });
  window.addEventListener("resize", chart.resize);
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", chart.resize);
  chart?.dispose();          // 组件卸载必须 dispose，否则内存泄漏
});
</script>
<template><div ref="el" style="width:100%;height:320px"></div></template>
```

要点只有三个：`ref` 容器、mounted 后 init、**unmount 前 dispose**。React 同理（useEffect + cleanup）。按需引入（`echarts/core` + 按图表注册）可显著减小打包体积，进阶路线参考官方「按需引入」文档。

### pyecharts 2.x（服务端生成）

Python 直接生成可交互 HTML 文件（适合不会前端的自动化报告场景）：

```python
from pyecharts.charts import Bar
bar = Bar()
bar.add_xaxis(["1星", "2星", "3星"])
bar.add_yaxis("数量", [226, 196, 203])
bar.render("report.html")   # 生成自包含 HTML（引 CDN）
```

| 路线 | 适用 | 代价 |
|---|---|---|
| 手写 JS + fetch API（本项目主路线） | 动态数据、大屏、前后端协作 | 要会一点 JS |
| pyecharts 渲染静态 HTML | 定时报告、邮件附件、无前端资源 | 定制联动/交互受限 |

## 常见坑与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| registerTheme 不生效 | init 之后才注册 | 注册在 init 前；或 init 时传主题名 |
| 10 万点页面卡死 | 没开 large/progressive | 三板斧；或先抽样 |
| 切 tab 回来图错位 | 容器尺寸变化未 resize | 监听可见性 + resize |
| Vue 路由切换后内存涨 | 实例未 dispose | onBeforeUnmount 里 dispose |
| dataZoom 拖动卡 | tooltip trigger 全量计算 | large 模式 + tooltip 精简 |

## 动手练习

1. 给 lab 05 的品牌主题加 `tooltip`/`axisPointer` 的全局样式。
2. 把 10 万点改成 LTTB 降采样到 2000 点，对比视觉差异（提示：sampling: "lttb"）。
3. 用 pyecharts 复刻第 07 章 KPI + 一张柱状图，生成 report.html 并浏览器打开。

## 小结与自检清单

- [ ] 会用 registerTheme 且知道它的时机限制
- [ ] 能说出大数据量三板斧及「先聚合后渲染」的决策顺序
- [ ] Vue/React 集成知道 init/dispose 的生命周期配对
- [ ] 能说清手写 JS 与 pyecharts 两条路线的取舍

## 延伸阅读

- [ECharts 6.0 特性导览](https://echarts.apache.org/handbook/zh/basics/release-note/v6-feature/)——Chord/Stock Charts/Matrix 等新图型在此
- [官方性能优化专题](https://echarts.apache.org/handbook/zh/best-practices/performance/)
