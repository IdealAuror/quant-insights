<p align="center">
  <h1 align="center">📐 quant-insights</h1>
  <p align="center">
    <em>Replicating academic research through the lens of the A-share market</em>
  </p>
  <p align="center">
    <a href="README.zh-CN.md">🇨🇳 中文</a>
    <br>
    <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-blue" alt="License">
    <img src="https://img.shields.io/badge/studies-1-brightgreen" alt="Studies">
    <img src="https://img.shields.io/badge/data-baostock-orange" alt="Data">
  </p>
</p>

---

A curated collection of quantitative research case studies. Each study replicates a published paper against A-share market data, distilling the original findings and testing whether they hold in China's equity market.

Every study is self-contained: backtest scripts, analysis charts, and a visual HTML report.

## Studies

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

## Getting Started

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

Each folder contains a `report.html` — open it in your browser for the full visual report.

## Repository Layout

```
quant-insights/
├── README.md
├── README.zh-CN.md                ← 中文版
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

---

<p align="center">
  <sub>Licensed under <a href="LICENSE">CC BY-NC 4.0</a> — share freely, no commercial use.</sub>
</p>
