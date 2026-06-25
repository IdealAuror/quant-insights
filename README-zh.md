<p align="center">
  <h1 align="center">📐 quant-insights</h1>
  <p align="center">
    <em>在A股市场复现学术研究成果</em>
  </p>
</p>

<p align="center">[English](./README.md) | [中文](./README-zh.md)</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-blue" alt="License">
  <img src="https://img.shields.io/badge/研究-4-brightgreen" alt="Studies">
  <img src="https://img.shields.io/badge/数据-baostock-orange" alt="Data">
</p>

---

精选量化研究案例集。每项研究在A股市场数据上复现一篇已发表论文，提炼原始发现并检验其在中国股票市场是否成立。

每项研究均为自包含：回测脚本、分析图表、中英文报告。

## 研究目录

<table>
<tr>
<td width="420">

#### 01 — [月内动量周期](01-intramonth-momentum/)

**论文：** Nathan, Suominen & Tasa (2026) — *The Intramonth Momentum Cycle* (SSRN)

**核心发现：** A股动量因子 70% 的收益集中在每月月末的 6 个交易日。

</td>
<td>

| 指标 | PreTOM | 其余交易日 | t |
|--------|:------:|:----------:|:-:|
| 输家 (D1) | **−9.9 bps** | +6.1 | **−4.2** |
| 赢家 (D10) | +11.1 | +10.0 | 0.2 |
| 多空 (10-1) | **+20.9 bps** | +3.9 | **2.0** |

</td>
</tr>
</table>

<details>
<summary><strong>核心要点</strong></summary>

- 效应**完全由输家驱动**——赢家在所有窗口表现一致
- 抛售压力呈**脉冲式**：集中在 T−6 和 T−5 两天，与美股的渐进式不同
- 仅 T−6 一天，输家下跌 **−45 bps**（t = −6.2，p < 0.0001）
- T+1 出现全市场反弹（输家 +47 bps，赢家 +56 bps）——beta 事件，非输家专属修复
- 根源：机构月末现金约束迫使基金经理清仓最可弃置的持仓

</details>

<table>
<tr>
<td width="420">

#### 02 — [四大支柱ETF轮动](02-four-pillar-etf-rotation/)

**类型：** 原创策略设计（非论文复现）

**核心发现：** 利用短期与长期偏离度捕捉均值回归的四资产ETF轮动策略，横跨A股、美股、黄金、债券。

</td>
<td>

| 指标 | 策略 | 基准（沪深300） |
|--------|:-----:|:-----------------:|
| 总收益 | **+92.7%** | ~+30% |
| 最大回撤 | **−8.2%** | ~−25% |
| 夏普比率 | **0.85** | — |
| Beta | **0.25** | 1.0 |

</td>
</tr>
</table>

<details>
<summary><strong>核心要点</strong></summary>

- 四只低相关ETF：红利低波(512890)、纳指100(513100)、黄金(518880)、10年国债(511260)
- 核心逻辑：超配偏离度为负的资产（短期跑输长期均值），低配偏离度为正的资产
- 5组参数压力测试——收益锁定在 87%–93% 区间，最大回撤从未突破 −10%
- 数学证明基准权重参数对最终配置无影响（只要无资产触碰15%下限）
- 弱点：持续单向趋势中跑输（如2023年AI驱动的纳指暴涨）

</details>

<table>
<tr>
<td width="420">

#### 03 — [红利ETF RSI双仓策略](03-dividend-etf-rsi-dual/)

**来源：** [IT阿伟量化投资博客](http://www.itawp.com/621.html)

**核心发现：** 针对红利ETF（510880）的单资产择时策略，年线偏离度定仓位，RSI捕捉短期波段。

</td>
<td>

| 指标 | 策略 | 基准（沪深300） |
|--------|:-----:|:-----------------:|
| 年化（含分红再投） | **5%–9%** | ~3% |
| 最大回撤 | **≤11%** | ~-25% |
| Beta | **0.22** | 1.0 |
| 任意时点买入胜率 | **100%** | — |

</td>
</tr>
</table>

<details>
<summary><strong>核心要点</strong></summary>

- 双仓结构：主仓（80%）用年线偏离度做价值择时；辅仓（20%）用RSI超卖信号做短线
- 分红再投至关重要——在价格回报之上额外贡献约 2%–3% 年化
- 5个不同时间窗口回测，任意时点买入均为正收益
- Beta 仅 0.22，与大盘几乎零相关——真正的绝对收益
- 弱点：疯牛初期踏空（如2019年）；交易频次低，需要耐心

</details>

<table>
<tr>
<td width="420">

#### 04 — [PE锚定双资产策略](04-pe-anchored-dual/)

**类型：** 原创策略设计（非论文复现）

**核心发现：** 以沪深300绝对PE为仓位中枢的双资产择时策略——低估满仓、高估轻仓——动量倾斜在红利ETF与创业板ETF之间分配资金。

</td>
<td>

| 指标 | 策略 | 基准（沪深300） |
|--------|:--------:|:-----------------:|
| 总收益 | **+150.6%** | +57.7% |
| 最大回撤 | **−26.2%** | ~−39% |
| Beta | **0.82** | 1.0 |
| Alpha | **+0.08** | — |

</td>
</tr>
</table>

<details>
<summary><strong>核心要点</strong></summary>

- 三层架构：PE估值中枢（沪深300 PE < 13 → 95%仓位；PE > 17 → 30%）→ 动量倾斜（强者获60%资金）→ 双池独立风控
- 不对称Alpha：2022年熊市仅跌 −8%（基准 −21%），2024年924行情 PE=12.8 触发满仓捕获 +25%
- 样本外验证：验证集（2022–2026）超额收益*高于*训练集（2019–2021）——无过拟合
- 收益归因：Beta贡献47%，Alpha（择时+网格+动量倾斜）贡献剩余103%
- 风险：−26% 最大回撤对保守型投资者偏高；若利率环境变化需重新校准PE阈值

</details>

## 快速开始

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

每个文件夹包含中英文 `*.html` 研究报告——在浏览器中打开即可阅读。

## 目录结构

```
quant-insights/
├── README.md                         ← 英文说明
├── README-zh.md                      ← 中文说明
├── LICENSE                           ← CC BY-NC 4.0（禁止商用）
│
├── 01-intramonth-momentum/           ← 因子研究（动量择时）
│   ├── momentum-cycle.html           ← 英文报告
│   ├── momentum-cycle.zh.html        ← 中文报告
│   ├── study.zh.md
│   ├── intramonth_momentum.py
│   ├── pretom_daily_v2.py
│   ├── posttom_daily.py
│   ├── tom_daily.py
│   ├── full_cycle.py
│   ├── cumulative_curve.py
│   └── *.png
│
├── 02-four-pillar-etf-rotation/      ← 策略设计（资产轮动）
│   ├── etf-rotation.html            ← 英文报告
│   ├── etf-rotation.zh.html         ← 中文报告
│   └── strategy.md
│
├── 03-dividend-etf-rsi-dual/         ← 策略设计（单资产择时）
│   ├── dividend-rsi.zh.html         ← 中文报告
│   └── study.zh.md
│
└── 04-pe-anchored-dual/              ← 策略设计（PE锚定双资产）
    ├── pe-anchored-dual.zh.html     ← 中文报告
    ├── study.zh.md
    └── pe_anchored_dual.py
```

---

<p align="center">
  <sub><a href="LICENSE">CC BY-NC 4.0</a> 许可协议——自由分享，禁止商用。</sub>
</p>
