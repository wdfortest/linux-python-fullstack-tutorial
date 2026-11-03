# 07.4 · ECharts 大屏实战（布局、图表、联动）

> 本章配套代码：`projects/book-insight/web/`（index.html / css/style.css / js/main.js）
> 访问方式：启动后端后打开 `http://127.0.0.1:8000/`
> 理论详解见 [05-echarts-visualization/](../05-echarts-visualization/01-ECharts快速上手.md)；本章讲这张大屏的完整实现思路。

## 学习目标

- 掌握 CSS Grid 数据大屏布局：KPI 行 + 图表网格 + 响应式降级
- 会用 fetch + async/await 对接后端 JSON 并做错误兜底
- 掌握本屏 6 张图表的 option 写法与深色主题要点
- 理解「一次聚合请求 + 前端分发」的数据加载模式

## 4.1 大屏长什么样

实测截图（1440×1100，真实数据渲染）：

- 顶栏：标题 + 数据说明 + 刷新按钮与更新时间
- KPI 行 5 张卡片：图书总数 1000 / 分类数 50 / 均价 £35.07 / 平均评分 2.92★ / 在售 1000
- 图表区：评分分布（蓝柱）、价格分布（紫柱）、分类书目 TOP10（蓝横条）、分类均价 TOP10（绿横条）、价格×评分散点（500 点）、在售状态环形图
- 底部：评分最高图书 TOP10 星级书单表

## 4.2 布局：CSS Grid 三级结构

```text
┌──────────────────────────────────────────────┐
│ topbar（标题 / 副标题 / 刷新）                  │
├──────┬──────┬──────┬──────┬──────┤
│ KPI  │ KPI  │ KPI  │ KPI  │ KPI  │   ← 5 列等宽
├──────┼──────┼──────┼──────┼──────┤
│rating│price │catego│catpri│      │   ← 4 列命名区域
│ +----+----+  ry   │ce    │      │
│scatter│scatter│ │      │avail │
├──────┴──────┴──────┴──────┴──────┤
│ toplist（跨满 4 列）                          │
└──────────────────────────────────────────────┘
```

实现（节选自 `css/style.css`）：

```css
.grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, 1fr);
  grid-template-areas:
    "rating  price    category catprice"
    "scatter scatter  category avail"
    "toplist toplist  toplist  toplist";
}
@media (max-width: 1100px) { /* 4 列 → 2 列 */ }
@media (max-width: 640px)  { /* → 单列，KPI 两列 */ }
```

每个面板用 `style="grid-area: rating"` 挂到命名区域；散点图特意占两列（500 点需要宽度）。**ECharts 容器必须有显式高度**（`.chart { height: 280px }`），否则白屏——最常见的入门坑。

## 4.3 数据加载：一个请求 + 统一兜底

```js
async function loadDashboard() {
  try {
    const resp = await fetch("/api/charts/all");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();
    renderKpis(data.summary);
    renderRatingDist(data.rating_distribution);
    renderPriceHist(data.price_histogram);
    renderCategoryTop(data.categories);
    renderCategoryPrice(data.categories);
    renderScatter(data.price_rating_scatter);
    renderAvailability(data.availability);
    renderTopTable(data.top_rated);
    document.getElementById("refresh-time").textContent = "更新于 " + new Date().toLocaleTimeString("zh-CN");
  } catch (err) {
    errBox.textContent = "数据加载失败：" + err.message + "。请确认已启动后端：uvicorn api.main:app --reload";
    errBox.style.display = "block";
  }
}
```

三个工程细节：

1. **同一份分类数据喂两张图**：`categories` 既画书目 TOP10 也画均价 TOP10，后端不用重复出接口
2. **失败要有出口**：catch 里直接告诉用户「怎么把后端跑起来」，而不是只报错
3. **同源请求**：前端由 FastAPI 托管，`fetch("/api/charts/all")` 不需要绝对地址，天然无 CORS 问题

CDN 兜底（index.html 内）：

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@6.1.0/dist/echarts.min.js"></script>
<script>
  if (typeof echarts === "undefined") {
    document.write('<script src="https://registry.npmmirror.com/echarts/6.1.0/files/dist/echarts.min.js"><\/script>');
  }
</script>
```

jsdelivr 不可达时自动切国内 npmmirror（CDN 对比见 [ECharts 快速上手](../05-echarts-visualization/01-ECharts快速上手.md)）。

## 4.4 图表实现要点（6 张）

所有图表共用深色基础配置：

```js
function baseOption() {
  return {
    backgroundColor: "transparent",
    textStyle: { color: "#e2e8f0" },
    tooltip: { backgroundColor: "#1e293b", borderColor: "#334155", textStyle: { color: "#e2e8f0" } },
  };
}
```

| 图表 | 类型 | 关键配置 | 效果要点 |
|---|---|---|---|
| 评分分布 | bar | `label:{show:true, position:"top"}` | 柱顶标数值，一眼读数 |
| 价格分布 | bar | `itemStyle:{borderRadius:[4,4,0,0]}` | 圆角柱身，轴标签 rotate 30° 防重叠 |
| 分类书目 TOP10 | bar（横向） | `grid:{left:110}` + `reverse()` 数据 | 长分类名放 Y 轴，从小到大画显排名 |
| 分类均价 | bar（横向） | label formatter `£{value}` | 数值带货币符号 |
| 价格×评分 | scatter | `symbolSize:9, opacity:0.55` | 半透明叠加看清密度；抽样 500 点控制体积 |
| 在售状态 | pie | `radius:["42%","66%"]` | 环形中心留白更现代；borderColor 与底色一致形成分割线 |

横向条形图「从小到大画」的小技巧：

```js
const top = data.slice(0, 10).reverse();   // 后端按数量降序给，反转后第一项画在最底
```

ECharts 的 Y 轴类目自下而上排列，想要「第一名在最上面」就得反转数据。

## 4.5 交互细节

- **统一 resize**：`window.addEventListener("resize", () => Object.values(charts).forEach(c => c.resize()))`——实例注册表 `charts{}` 让所有图跟随窗口
- **手动刷新**：刷新按钮直接再跑 `loadDashboard()`，并更新「更新于」时间戳
- **星级行内可视化**：TOP10 表格里用 `"★".repeat(n) + "☆".repeat(5-n)` 纯文本画星，不引额外组件

## 4.6 与后端的契约

大屏只依赖一个端点 `/api/charts/all`，其响应结构（`api/schemas.py` 的 `ChartsAll`）：

```json
{
  "summary": {"total_books": 1000, "avg_price": 35.07, "...": "..."},
  "rating_distribution": [{"rating": 1, "count": 226}],
  "price_histogram": [{"bucket": "0-10", "count": 33}],
  "categories": [{"category": "Default", "count": 152, "avg_price": 34.39}],
  "top_rated": [{"title": "Sapiens...", "price": 54.23, "rating": 5}],
  "price_rating_scatter": [{"price": 12.5, "rating": 3}],
  "availability": [{"name": "在售", "value": 1000}]
}
```

**契约先行**：前后端字段名、数值口径（谁负责四舍五入、抽样多少）在开发前约定好，是并行开发的底线（更多讨论见 [异步数据与API对接](../05-echarts-visualization/03-异步数据与API对接.md)）。

## 常见坑与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 图表区域空白 | 容器无高度 / CDN 没加载成功 | `.chart` 显式高度；CDN 兜底脚本 |
| 窗口缩放后图变形 | 缺 resize 监听 | 统一 resize（见 4.5） |
| 分类名被截断 | Y 轴留白不足 | `grid.left` 调大 |
| 散点全是同色圆点 | 未做视觉映射 | 需要时上 visualMap（见[常用图表章](../05-echarts-visualization/02-常用图表类型详解.md)） |
| 刷新后旧图残留 | 重复 init | 固定实例复用 setOption（本项目 makeChart 注册表做法） |

## 动手练习

1. 给散点图加 `visualMap`：按评分着色（绿→红），观察颜色是否让「无相关性」更直观。
2. 增加「库存分布」直方图（0-5/6-10/... 分箱），后端无需改动——数据已含 availability。
3. 让大屏每 60 秒自动刷新，且页面隐藏时暂停（提示：`document.visibilitychange`）。

## 小结与自检清单

- [ ] 能用 CSS Grid 独立搭出响应式大屏骨架
- [ ] 能写出 fetch + try/catch 的标准加载流程并说清兜底文案的价值
- [ ] 会画横向条形图并处理「排名方向」
- [ ] 知道为什么用单一聚合端点 + 同源托管

## 延伸阅读

- [ECharts 配置项手册](https://echarts.apache.org/handbook/zh/basics/download)
- [MDN: CSS Grid 布局](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_grid_layout)
