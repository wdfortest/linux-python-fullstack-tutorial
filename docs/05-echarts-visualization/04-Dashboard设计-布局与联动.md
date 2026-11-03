# 05.4 · Dashboard 设计：布局与联动

> 本章配套代码：`projects/echarts-lab/04_dashboard_layout.html`（静态数据版，直接打开即可）
> 实战版：第 07 章项目的大屏 [web/](../../projects/book-insight/web/)（真实 API 数据驱动）
> 本地预览：`cd projects/echarts-lab && python -m http.server 8060` 后打开 `04_dashboard_layout.html`

## 学习目标

- 掌握数据大屏的三级版式（KPI 行 → 主图区 → 次图网格）与 CSS Grid 实现
- 理解 F 型视觉动线在仪表盘上的应用
- 掌握图表联动的两种实现：`echarts.connect` 与事件监听过滤
- 建立深色大屏的配色与字号层次规范

## 5.4.1 大屏的两种形态

| 形态 | 目的 | 特征 |
|---|---|---|
| 分析报表（BI） | 帮人**理解**数据、做决策 | 图多而全，可交互过滤，读字为主 |
| 监控大屏 | 帮人**发现异常** | 字大图大、远距离可读、异常高亮、自动轮播 |

本项目的大屏属于前者（图书数据洞察），设计原则通用。

## 5.4.2 三级版式与视觉动线

```text
┌────────────────────────────────────────────┐
│ ① 标题区：名称 + 数据说明 + 刷新             │ ← 3 秒内知道「这是什么数据」
├──────┬──────┬──────┬──────┬──────┤
│ KPI  │ KPI  │ KPI  │ KPI  │ KPI  │ ← ② 核心指标行：5~6 张卡片，数字最大
├──────┴──────┼──────┴──────┤
│             │             │
│   主图区     │   次图区     │ ← ③ 图表网格：主图 2×2 或跨列，
│  (最重要)    │  (次要)      │    F 型动线：左上最重，右下最轻
├─────────────┴─────────────┤
│  底部：明细表 / 数据来源脚注               │
└────────────────────────────────────────────┘
```

用户扫视大屏是「先左上后右下」的 F 型动线，所以：**最重要的图放左上**（本项目：评分分布），装饰性/次要的放右下。

### CSS Grid 实现要点（实战版节选）

```css
.grid {
  display: grid; gap: 12px;
  grid-template-columns: repeat(4, 1fr);
  grid-template-areas:
    "rating  price    category catprice"
    "scatter scatter  category avail"
    "toplist toplist  toplist  toplist";
}
@media (max-width: 1100px) { /* 4列→2列 */ }
@media (max-width: 640px)  { /* →单列；KPI 5→2列 */ }
```

三个决定成败的细节：

1. **命名区域而非行号**：`grid-area` 语义化，调整布局只改 `grid-template-areas` 一处
2. **响应式降级**：4 列 → 2 列 → 单列；KPI 行同步降级，移动端依然可读
3. **图表容器显式高度**：`.chart { height: 280px }`——ECharts 容器无高度 = 白屏（第 1 篇讲过的第一大坑）

## 5.4.3 图表联动：两招

### 第一招：echarts.connect（tooltip/数据刷同步）

```js
echarts.connect([mainChart, sideChart, bottomChart]);
```

任意一图 hover，其余图的 tooltip 跟随联动——适合「同一批数据的两种视图」。一行代码，注意传入的是**数组**且实例已 init。

### 第二招：事件监听 + 数据过滤（更强大）

```js
mainChart.on("click", (params) => {
  const cat = params.name;                 // 用户点击的类目
  renderSide(cat);                          // 侧图只渲染该分类的趋势
  sideTitle.textContent = "折线 · " + cat + " 趋势";
});
```

点击主图类目 → 侧图与标题联动更新。这是「图表即过滤器」的思想：**让图代替下拉框**。

> lab 04 里两招都实现了：先 connect 同步 tooltip，再注册 click 联动，打开页面点一下主图条形即可体验。

## 5.4.4 深色大屏设计规范

### 配色体系

```text
背景层：#0f172a（页面）→ #1e293b（面板）→ #334155（描边）   ← 三级灰阶拉开层次
文字层：#e2e8f0（正文）/ #94a3b8（次要）                    ← 不要用纯白/纯灰
强调色：#38bdf8（主）/ #a78bfa（次）/ #fbbf24（警示数字）    ← 饱和度一致
语义色：#34d399 在售(绿) / #fb7185 缺货(红)                  ← 全站固定
```

要点：深色背景上**避免纯黑纯白**；分类色板全局统一（第 07 章把色板定义为 `PALETTE` 常量，所有图共用）；同一页面强调色不超过 2 种。

### 字号层次

| 元素 | 字号 | 权重 |
|---|---|---|
| KPI 数字 | 26~28px | 700 |
| 标题 h1 | 20~26px | 600+，可加字距 |
| 面板标题 h2 | 13~14px | 600 |
| 轴标签/图例 | 11~12px | 400，用次要文字色 |
| 脚注 | 12px | 次要文字色 |

### 统一的 tooltip / 图例格式

所有图共用 `baseOption()`（第 07 章的写法）：深色底、统一文字色、统一边框——细节统一了，大屏才有「专业感」。

## 5.4.5 动态标题与 updateOption

联动更新时顺手更新面板标题（如上 `sideTitle.textContent`），让用户明确知道「现在看的是什么范围」。ECharts 自身的 `title` 也可以用 setOption 增量更新：

```js
chart.setOption({ title: { text: " Fiction 趋势" } });   // 只更新 title
```

## 常见坑与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| KPI 行在窄屏挤成一条 | 固定 5 列 | media query 降 2 列 |
| 联动后旧数据残留 | 过滤分支漏了某系列 | 联动渲染统一走一个 render 函数 |
| connect 不生效 | 实例未 init 完或传入非数组 | 确认 init 顺序，传数组 |
| 大屏在小屏上文字溢出 | 只写了大屏字号 | 用 clamp()/media query 分级 |
| 图表互相错位 | gap 与 padding 重复计算 | 统一用 gap，面板内用小 padding |

## 动手练习

1. 给 lab 04 增加「重置联动」按钮：点击后侧图恢复全量趋势。
2. 把 KPI 行改为可配置数组驱动（已实现），再加一张「平均库存」卡片。
3. 用第 07 章真实数据替换 lab 04 的静态数据（对接 `/api/charts/all`）。

## 小结与自检清单

- [ ] 能画出三级版式线框图并说出 F 型动线的意义
- [ ] 会用命名 grid-area + media query 做响应式大屏
- [ ] 两种联动（connect / 事件过滤）都能写出来
- [ ] 能背出深色大屏的配色三层结构

## 延伸阅读

- [MDN: CSS Grid 布局](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_grid_layout)
- [ECharts: 事件与行为](https://echarts.apache.org/handbook/zh/concepts/event/)
