<p align="center">
  <h1 align="center">📐 quant-insights</h1>
  <p align="center">
    <em>Replicating academic research through the lens of the A-share market</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-blue" alt="License">
    <img src="https://img.shields.io/badge/studies-2-brightgreen" alt="Studies">
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

#### 01 — [PreTOM Momentum Crush](01-pretom-momentum-crush/)

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

<table>
<tr>
<td width="420">

#### 02 — [Four-Pillar ETF Rotation](02-four-pillar-etf-rotation/)

**Type:** Original strategy design (non-paper)

**Headline:** A four-asset ETF rotation strategy using short-term vs long-term deviation to harvest mean-reversion across A-share, US equity, gold, and bonds.

</td>
<td>

| Metric | Value | Benchmark (HS300) |
|--------|:-----:|:-----------------:|
| Total Return | **+92.7%** | ~+30% |
| Max Drawdown | **−8.2%** | ~−25% |
| Sharpe Ratio | **0.85** | — |
| Beta | **0.25** | 1.0 |

</td>
</tr>
</table>

<details>
<summary><strong>Key takeaways</strong></summary>

- Four low-correlation ETFs: Dividend Low-Vol (512890), Nasdaq 100 (513100), Gold (518880), 10Y Bond (511260)
- Core logic: overweight assets with negative deviation (underperforming their long-term average), underweight those with positive deviation
- Stress-tested across 5 parameter sets — returns locked in 87%–93% range, max drawdown never exceeded −10%
- Base weight parameter is mathematically proven to have zero impact on final allocation (as long as no asset hits the 15% floor)
- Weakness: underperforms in sustained one-directional trends (e.g., 2023 AI-driven Nasdaq rally)

</details>

## Getting Started

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

Each folder contains `report.html` (English) and `report.zh.html` (Chinese) — open in your browser for the full visual report.

## Repository Layout

```
quant-insights/
├── README.md
├── LICENSE                        ← CC BY-NC 4.0 (non-commercial)
│
├── 01-pretom-momentum-crush/      ← factor study (momentum timing)
│   ├── report.html / report.zh.html
│   ├── intramonth_momentum.py
│   ├── pretom_daily_v2.py
│   ├── posttom_daily.py
│   ├── tom_daily.py
│   ├── full_cycle.py
│   ├── cumulative_curve.py
│   └── *.png
│
└── 02-four-pillar-etf-rotation/   ← strategy design (asset rotation)
    ├── report.html / report.zh.html
    └── strategy.md
```

---

<p align="center">
  <sub>Licensed under <a href="LICENSE">CC BY-NC 4.0</a> — share freely, no commercial use.</sub>
</p>
