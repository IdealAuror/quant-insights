<p align="center">
  <h1 align="center">📐 quant-insights</h1>
  <p align="center">
    <em>以 A 股市场为视角，复现学术研究中的量化洞察</em>
  </p>
  <p align="center">
    <br>
    <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-blue" alt="License">
    <img src="https://img.shields.io/badge/studies-1-brightgreen" alt="Studies">
    <img src="https://img.shields.io/badge/data-baostock-orange" alt="Data">
  </p>
</p>

---

量化研究案例合集。每项研究以已发表论文为基础，用 A 股数据进行复现与验证，检验原始结论在中国市场的适用性。

每项研究自成一体：回测脚本、分析图表、可视化 HTML 报告。

## 研究列表

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

## 环境配置

```bash
pip install baostock pandas numpy matplotlib scipy pyarrow
```

每个文件夹内的 `report.html` 可直接用浏览器打开查看完整可视化报告。

## 目录结构

```
quant-insights/
├── README.md                      ← English version
├── .github/
│   └── README.zh-CN.md            ← 中文版（GitHub 自动切换）
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

---

<p align="center">
  <sub>基于 <a href="LICENSE">CC BY-NC 4.0</a> 许可——自由分享，禁止商用。</sub>
</p>
