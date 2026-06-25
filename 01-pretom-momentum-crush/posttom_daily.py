"""
PostTOM窗口逐日分析：赢家(T-3到T+3每天)的收益变化
"""
import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy import stats
import warnings
import os

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

START_DATE = "2016-01-01"
END_DATE = "2025-12-31"
MAX_STOCKS = 100
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

STOCK_POOL = [
    "600519", "601318", "600036", "600276", "601166", "600030", "600900",
    "601398", "600028", "600887", "601888", "600309", "601012", "600690",
    "600050", "601668", "600585", "600000", "601288", "600104", "600016",
    "601601", "601328", "600019", "601225", "600809", "601857", "600048",
    "600196", "601688", "600346", "601138", "600837", "601211", "600741",
    "601628", "600606", "601390", "600176", "601669", "600460", "600703",
    "601111", "600436", "601877", "600132", "601919", "600406", "601899",
    "600918", "601816", "600183", "601186", "600547", "601088", "600570",
    "600332", "601006", "600298", "601336", "600795", "600029", "601985",
    "600031", "601021", "600660", "601800", "600009", "601865", "600111",
    "601766", "600383", "601236", "600271", "601009", "600938", "601838",
    "600600", "601633", "600893", "601155", "600845", "601989", "600760",
    "603259", "603288", "603501", "603799", "603986", "603160", "603993",
    "603369", "603899", "603486", "603613", "603658", "603260", "603882",
    "603127", "603605", "603233", "603816", "603195", "603185",
    "000858", "000333", "002714", "000568", "000651", "000002", "000001",
    "000725", "002415", "000661", "000063", "002304", "000876", "002027",
    "000338", "002352", "000538", "002142", "000166", "002049", "000100",
    "000776", "002050", "002230", "000895", "000049", "000423", "002241",
    "000703", "002001", "002032", "000983", "002007", "000977", "000625",
    "002594", "002475", "000708", "002120", "000839", "002081", "000768",
    "002008", "000400", "002558", "000069", "000961", "002372", "002601",
    "000656", "002311", "002129", "000887", "002271", "002791", "000963",
    "000157", "000627", "002410", "000596", "002736", "002385", "000786",
    "002607", "002202", "002340", "002179", "000408", "002065", "002157",
    "300750", "300059", "300760", "300124", "300274", "300122", "300015",
    "300033", "300142", "300014", "300529", "300408", "300347", "300413",
    "300136", "300308", "300316", "300628", "300207", "300498", "300253",
    "300123", "300433", "300003", "300257", "300285", "300146", "300394",
    "300357", "300244", "300037", "300115", "300363", "300457", "300390",
    "300595", "300773", "300395", "300726", "300699", "300682", "300392",
    "300502", "300083", "300566", "300326", "300212", "300399", "300271",
    "300487", "300353", "300339", "300300", "300440", "300474", "300476",
    "300099", "300573", "300202", "300251", "300340", "300190", "300547",
]


def to_bs_code(code):
    return f"sh.{code}" if code.startswith("6") else f"sz.{code}"


def fetch_all_data():
    lg = bs.login()
    all_data = {}
    for i, code in enumerate(STOCK_POOL[:MAX_STOCKS]):
        cache_file = os.path.join(CACHE_DIR, f"{code}.parquet")
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
        else:
            rs = bs.query_history_k_data_plus(to_bs_code(code), "date,close,volume",
                start_date=START_DATE, end_date=END_DATE, frequency="d", adjustflag="2")
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            if not rows:
                continue
            df = pd.DataFrame(rows, columns=["date", "close", "volume"])
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df = df.dropna(subset=["close"])
            df = df[df["close"] > 0].sort_values("date").reset_index(drop=True)
            df.to_parquet(cache_file)
        if len(df) > 252:
            all_data[code] = df
    bs.logout()
    return all_data


def build_records(all_data):
    close_dict = {code: df.set_index("date")["close"].rename(code) for code, df in all_data.items()}
    close_df = pd.DataFrame(close_dict).sort_index()
    ret_12m = close_df.pct_change(252)
    ret_1m = close_df.pct_change(21)
    momentum = (1 + ret_12m) / (1 + ret_1m) - 1

    monthly_idx = momentum.resample("ME").last().dropna(how="all").index
    deciles = {}
    for date in monthly_idx:
        mom = momentum.loc[:date].iloc[-1].dropna()
        if len(mom) < 20:
            continue
        ranks = mom.rank(pct=True)
        decile = np.ceil(ranks * 10).clip(1, 10).astype(int)
        deciles[date] = decile
    deciles_df = pd.DataFrame(deciles).T

    dates = pd.DatetimeIndex(sorted(set().union(*[set(d["date"]) for d in all_data.values()])))
    all_day_map = {}
    for me in sorted(deciles_df.index):
        pre_days = dates[dates < me].sort_values(ascending=False)
        post_days = dates[dates > me].sort_values()
        for i, d in enumerate(pre_days[:15]):
            all_day_map[d] = -(i + 1)
        for i, d in enumerate(post_days[:10]):
            all_day_map[d] = i + 1

    daily_returns = {code: df.set_index("date")["close"].pct_change().rename(code) for code, df in all_data.items()}
    ret_df = pd.DataFrame(daily_returns).sort_index()

    records = []
    for date, rel_day in all_day_map.items():
        if date not in ret_df.index:
            continue
        valid_months = deciles_df.index[deciles_df.index <= date]
        if len(valid_months) == 0:
            continue
        month = valid_months[-1]
        decile_map = deciles_df.loc[month]
        for code in ret_df.columns:
            if code not in decile_map.index:
                continue
            r = ret_df.loc[date, code]
            d = decile_map[code]
            if pd.notna(r) and pd.notna(d):
                records.append({"date": date, "rel_day": rel_day, "decile": int(d), "return": r})

    return pd.DataFrame(records)


def main():
    print("加载数据...")
    all_data = fetch_all_data()
    records_df = build_records(all_data)

    # ========== PostTOM逐日: T-3到T+3 ==========
    posttom = records_df[records_df["rel_day"].between(-3, 3)]
    baseline = records_df[~records_df["rel_day"].between(-9, 3)]

    print("\n" + "=" * 60)
    print("PostTOM窗口 [T-3 ~ T+3] 逐日收益")
    print("=" * 60)

    daily_stats = []
    for d in range(-3, 4):
        sub = posttom[posttom["rel_day"] == d]
        lo = sub[sub["decile"] == 1]["return"]
        hi = sub[sub["decile"] == 10]["return"]
        wml = hi.mean() - lo.mean()
        daily_stats.append({
            "rel_day": d,
            "label": f"T{'+' if d > 0 else ''}{d}",
            "loser_mean": lo.mean() * 10000,
            "winner_mean": hi.mean() * 10000,
            "wml": wml * 10000,
            "n": len(sub),
        })
        print(f"  T{'+' if d > 0 else ''}{d:2d}: 输家={lo.mean()*10000:+7.2f}bps  "
              f"赢家={hi.mean()*10000:+7.2f}bps  WML={wml*10000:+7.2f}bps  (n={len(sub)})")

    # 赢家逐日 vs 基线
    base_hi = baseline[baseline["decile"] == 10]["return"]
    base_lo = baseline[baseline["decile"] == 1]["return"]
    print(f"\n基线(其余日): 赢家={base_hi.mean()*10000:.2f}bps, 输家={base_lo.mean()*10000:.2f}bps")

    print("\n赢家逐日 vs 基线 t检验:")
    for st in daily_stats:
        sub_hi = posttom[(posttom["rel_day"] == st["rel_day"]) & (posttom["decile"] == 10)]["return"]
        t, p = stats.ttest_ind(sub_hi, base_hi)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"  {st['label']}: t={t:+.2f}, p={p:.4f} {sig}")

    print("\n输家逐日 vs 基线 t检验:")
    for st in daily_stats:
        sub_lo = posttom[(posttom["rel_day"] == st["rel_day"]) & (posttom["decile"] == 1)]["return"]
        t, p = stats.ttest_ind(sub_lo, base_lo)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"  {st['label']}: t={t:+.2f}, p={p:.4f} {sig}")

    # 绘图
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    labels = [s["label"] for s in daily_stats]

    # 图1: 赢家逐日
    ax = axes[0]
    hi_vals = [s["winner_mean"] for s in daily_stats]
    colors = ["#2980b9" if v > base_hi.mean()*10000 else "#95a5a6" for v in hi_vals]
    bars = ax.bar(labels, hi_vals, color=colors, alpha=0.85, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, hi_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.axhline(base_hi.mean()*10000, color="gray", linestyle="--", alpha=0.6,
               label=f"其余日均值={base_hi.mean()*10000:.1f}bps")
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("赢家(D10) PostTOM逐日收益\n月初是否涨得更猛?")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(fontsize=9)

    # 图2: 输家逐日
    ax = axes[1]
    lo_vals = [s["loser_mean"] for s in daily_stats]
    colors2 = ["#c0392b" if v < base_lo.mean()*10000 else "#27ae60" for v in lo_vals]
    bars2 = ax.bar(labels, lo_vals, color=colors2, alpha=0.85, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars2, lo_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val:.1f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=10, fontweight="bold")
    ax.axhline(base_lo.mean()*10000, color="gray", linestyle="--", alpha=0.6,
               label=f"其余日均值={base_lo.mean()*10000:.1f}bps")
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("输家(D1) PostTOM逐日收益\n是否在此窗口反弹?")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(fontsize=9)

    # 图3: WML逐日
    ax = axes[2]
    wml_vals = [s["wml"] for s in daily_stats]
    colors3 = ["#8e44ad" if v > 0 else "#e67e22" for v in wml_vals]
    bars3 = ax.bar(labels, wml_vals, color=colors3, alpha=0.85, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars3, wml_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val:.1f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=10, fontweight="bold")
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("WML(赢家-输家) PostTOM逐日")
    ax.axhline(0, color="black", linewidth=0.8)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posttom_daily.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n图表已保存: {out}")

    # 趋势检验
    print("\n===== 趋势检验 =====")
    slope_hi, _, r_hi, p_hi, _ = stats.linregress(range(len(hi_vals)), hi_vals)
    print(f"赢家逐日趋势: 斜率={slope_hi:.2f}bps/天, R2={r_hi**2:.3f}, p={p_hi:.4f}")

    slope_lo, _, r_lo, p_lo, _ = stats.linregress(range(len(lo_vals)), lo_vals)
    print(f"输家逐日趋势: 斜率={slope_lo:.2f}bps/天, R2={r_lo**2:.3f}, p={p_lo:.4f}")

    slope_wml, _, r_wml, p_wml, _ = stats.linregress(range(len(wml_vals)), wml_vals)
    print(f"WML逐日趋势:  斜率={slope_wml:.2f}bps/天, R2={r_wml**2:.3f}, p={p_wml:.4f}")


if __name__ == "__main__":
    main()
