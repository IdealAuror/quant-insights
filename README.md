<p align="center">
  <h1 align="center">📐 quant-insights</h1>
  <p align="center">
    <em>Replicating academic research through the lens of the A-share market</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-blue" alt="License">
    <img src="https://img.shields.io/badge/studies-1-brightgreen" alt="Studies">
    <img src="https://img.shields.io/badge/data-baostock-orange" alt="Data">
  </p>
</p>

---

<details open>
<summary><h2>🇺🇸 English</h2></summary>

A curated collection of quantitative research case studies. Each study replicates a published paper against A-share market data, distilling the original findings and testing whether they hold in China's equity market.

Every study is self-contained: backtest scripts, analysis charts, and a visual HTML report.

### Studies

<table>
<tr>
<td width="420">

#### 01 — [Intramonth Momentum Cycle](01-intramonth-momentum/)

**Paper:** Nathan, Suominen & Tasa (2026) — *The Intramonth Momentum Cycle* (SSRN)

**Headline:** 70% of A-share momentum profits are earned in just 6 trading days before month-end.

</td>
<td>

| Metric | PreTOM | Other Days | t |
|--------|:------:|:----------:|:-:|
| Loser (D1) | **−9.9 bps** | +6.1 | **−4.2** |
| Winner (D10) | +11.1 | +10.0 | 0.2 |
| Long-Short | **+20.9 bps** | +3.9 | **2.0** |

</td>
</tr>
</table>

<details>
<summary><strong>Key takeaways</strong></summary>

- The effect is **entirely loser-driven** — winners behave identically across all windows
- Selling pressure is **pulse-shaped**: concentrated on T−6 and T−5, unlike the gradual build-up seen in the US
- On T−6 alone, losers drop **−45 bps** (t = −6.2, p < 0.0001)
- T+1 sees a broad market rebound (+47 bps losers, +56 bps winners) — a beta event, not a loser-specific reversal
- Root cause: institutional month-end cash constraints force managers to liquidate their most dispensable holdings

</details>

### Getting Started

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

Each folder contains a `report.html` — open it in your browser for the full visual report.

### Repository Layout

```
quant-insights/
├── README.md
├── .github/README.zh-CN.md        ← 中文版
├── LICENSE                        ← CC BY-NC 4.0 (non-commercial)
│
└── 01-intramonth-momentum/
    ├── report.html                ← visual report (open in browser)
    ├── intramonth_momentum.py     ← main backtest engine
    ├── pretom_daily_v2.py         ← PreTOM daily decomposition
    ├── posttom_daily.py           ← PostTOM daily decomposition
    ├── tom_daily.py               ← turn-of-month daily view
    ├── full_cycle.py              ← T−6 → T+5 overview chart
    ├── cumulative_curve.py        ← cumulative return curves
    └── *.png                      ← rendered charts
```

</details>

<details>
<summary><h2>🇨🇳 中文</h2></summary>

量化研究案例合集。每项研究以已发表论文为基础，用 A 股数据进行复现与验证，检验原始结论在中国市场的适用性。

每项研究自成一体：回测脚本、分析图表、可视化 HTML 报告。

### 研究列表

<table>
<tr>
<td width="420">

#### 01 — [月内动量周期](01-intramonth-momentum/)

**论文：** Nathan, Suominen & Tasa (2026) — *The Intramonth Momentum Cycle* (SSRN)

**核心发现：** A 股动量收益 70% 集中在月末倒数第 5-6 个交易日。

</td>
<td>

| 指标 | PreTOM | 其余交易日 | t |
|------|:------:|:---------:|:-:|
| 输家 (D1) | **−9.9 bps** | +6.1 | **−4.2** |
| 赢家 (D10) | +11.1 | +10.0 | 0.2 |
| 多空 (10−1) | **+20.9 bps** | +3.9 | **2.0** |

</td>
</tr>
</table>

<details>
<summary><strong>详细结论</strong></summary>

- 效应**完全由输家驱动**——赢家在各窗口无显著差异
- 抛售呈**脉冲式**：集中在 T−6 和 T−5 两天，不同于美股的渐进式分布
- T−6 输家单日跌幅 **−45 bps**（t = −6.2, p < 0.0001）
- T+1 全市场反弹（输家 +47bps，赢家 +56bps）——市场级别 beta 效应，非输家专属
- 根本原因：机构月末现金约束迫使基金经理抛售最可弃置的持仓

</details>

### 环境配置

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

每个文件夹内的 `report.html` 可直接用浏览器打开查看完整可视化报告。

### 目录结构

```
quant-insights/
├── README.md
├── .github/README.zh-CN.md        ← 中文版
├── LICENSE                        ← CC BY-NC 4.0（禁止商用）
│
└── 01-intramonth-momentum/
    ├── report.html                ← 可视化报告（浏览器打开）
    ├── intramonth_momentum.py     ← 主回测引擎
    ├── pretom_daily_v2.py         ← PreTOM 逐日拆解
    ├── posttom_daily.py           ← PostTOM 逐日拆解
    ├── tom_daily.py               ← 月末月初逐日分析
    ├── full_cycle.py              ← T−6 → T+5 全景图
    ├── cumulative_curve.py        ← 累积收益曲线
    └── *.png                      ← 渲染图表
```

</details>

---

<p align="center">
  <sub>Licensed under <a href="LICENSE">CC BY-NC 4.0</a> — share freely, no commercial use.</sub>
</p>
