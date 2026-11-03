/* Book Insight 大屏逻辑：拉取 /api/charts/all -> KPI 卡片 + 6 张 ECharts 图表 */
"use strict";

const ACCENT = "#38bdf8";
const ACCENT2 = "#a78bfa";
const PALETTE = ["#38bdf8", "#a78bfa", "#fbbf24", "#fb7185", "#34d399", "#22d3ee", "#f472b6", "#a3e635"];

const charts = {}; // 图表实例注册表，便于统一 resize

/** 统一的 ECharts 基础配置（深色主题要素） */
function baseOption() {
  return {
    backgroundColor: "transparent",
    textStyle: { color: "#e2e8f0" },
    tooltip: { backgroundColor: "#1e293b", borderColor: "#334155", textStyle: { color: "#e2e8f0" } },
  };
}

function makeChart(id) {
  const el = document.getElementById(id);
  const instance = echarts.init(el);
  charts[id] = instance;
  return instance;
}

/* ---------- KPI 卡片 ---------- */
function renderKpis(summary) {
  const row = document.getElementById("kpi-row");
  const kpis = [
    { label: "图书总数", value: summary.total_books },
    { label: "分类数", value: summary.categories },
    { label: "平均价格", value: "£" + summary.avg_price },
    { label: "平均评分", value: summary.avg_rating + " ★" },
    { label: "在售 / 总库存件数", value: summary.in_stock + " / " + summary.avg_stock + "均" },
  ];
  row.innerHTML = kpis
    .map((k) => `<div class="kpi"><div class="num">${k.value}</div><div class="label">${k.label}</div></div>`)
    .join("");
}

/* ---------- 图表 ---------- */
function renderRatingDist(data) {
  makeChart("chart-rating").setOption({
    ...baseOption(),
    grid: { left: 40, right: 16, top: 20, bottom: 30 },
    xAxis: { type: "category", data: data.map((d) => d.rating + " 星"), axisLine: { lineStyle: { color: "#475569" } }, axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    series: [{ type: "bar", data: data.map((d) => d.count), itemStyle: { color: ACCENT, borderRadius: [4, 4, 0, 0] }, label: { show: true, position: "top", color: "#e2e8f0" } }],
  });
}

function renderPriceHist(data) {
  makeChart("chart-price").setOption({
    ...baseOption(),
    grid: { left: 40, right: 16, top: 20, bottom: 40 },
    xAxis: { type: "category", data: data.map((d) => d.bucket), axisLine: { lineStyle: { color: "#475569" } }, axisLabel: { color: "#94a3b8", rotate: 30 } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    series: [{ type: "bar", data: data.map((d) => d.count), itemStyle: { color: ACCENT2, borderRadius: [4, 4, 0, 0] } }],
  });
}

function renderCategoryTop(data) {
  const top = data.slice(0, 10).reverse(); // 横向条形图：从小到大画
  makeChart("chart-category").setOption({
    ...baseOption(),
    grid: { left: 110, right: 24, top: 10, bottom: 24 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "category", data: top.map((d) => d.category), axisLabel: { color: "#cbd5e1", fontSize: 11 } },
    series: [{ type: "bar", data: top.map((d) => d.count), itemStyle: { color: ACCENT }, label: { show: true, position: "right", color: "#e2e8f0" } }],
  });
}

function renderCategoryPrice(data) {
  const top = data.slice(0, 10);
  makeChart("chart-catprice").setOption({
    ...baseOption(),
    grid: { left: 110, right: 40, top: 10, bottom: 24 },
    xAxis: { type: "value", name: "均价 £", nameTextStyle: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "category", data: top.map((d) => d.category), axisLabel: { color: "#cbd5e1", fontSize: 11 } },
    series: [{
      type: "bar",
      data: top.map((d) => d.avg_price),
      itemStyle: { color: "#34d399" },
      label: { show: true, position: "right", color: "#e2e8f0", formatter: (p) => "£" + p.value },
    }],
  });
}

function renderScatter(points) {
  makeChart("chart-scatter").setOption({
    ...baseOption(),
    grid: { left: 44, right: 20, top: 20, bottom: 36 },
    xAxis: { type: "value", name: "价格 £", nameTextStyle: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", name: "评分", min: 1, max: 5, nameTextStyle: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#94a3b8" } },
    series: [{
      type: "scatter",
      data: points.map((p) => [p.price, p.rating]),
      symbolSize: 9,
      itemStyle: { opacity: 0.55, color: ACCENT },
    }],
  });
}

function renderAvailability(data) {
  makeChart("chart-avail").setOption({
    ...baseOption(),
    legend: { bottom: 0, textStyle: { color: "#94a3b8" } },
    series: [{
      type: "pie",
      radius: ["42%", "66%"],
      center: ["50%", "44%"],
      data: data,
      label: { color: "#cbd5e1", formatter: "{b}: {c}" },
      itemStyle: { borderColor: "#1e293b", borderWidth: 2 },
      color: ["#34d399", "#fb7185"],
    }],
  });
}

/* ---------- TOP10 表格 ---------- */
function renderTopTable(books) {
  const wrap = document.getElementById("top-table");
  const stars = (n) => "★".repeat(n || 0) + "☆".repeat(5 - (n || 0));
  wrap.innerHTML = `
    <table>
      <thead><tr><th>#</th><th>书名</th><th>分类</th><th>价格</th><th>评分</th></tr></thead>
      <tbody>
        ${books.map((b, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${b.title}</td>
            <td>${b.category || "-"}</td>
            <td>£${b.price}</td>
            <td class="stars">${stars(b.rating)}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;
}

/* ---------- 数据加载与错误处理 ---------- */
async function loadDashboard() {
  const errBox = document.getElementById("err-box");
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

    document.getElementById("refresh-time").textContent =
      "更新于 " + new Date().toLocaleTimeString("zh-CN");
  } catch (err) {
    errBox.textContent = "数据加载失败：" + err.message + "。请确认已启动后端：uvicorn api.main:app --reload";
    errBox.style.display = "block";
  }
}

window.addEventListener("resize", () => Object.values(charts).forEach((c) => c.resize()));
document.getElementById("refresh-btn").addEventListener("click", loadDashboard);
loadDashboard();
