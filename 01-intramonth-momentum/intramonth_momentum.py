"""
A股月内动量周期回测
论文: The Intramonth Momentum Cycle (Nathan, Suominen, Tasa, 2026)
验证: PreTOM窗口 (月末倒数第4-9个交易日) 是否贡献了动量因子的大部分收益
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

# ==================== 配置 ====================
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


def to_bs_code(code: str) -> str:
    return f"sh.{code}" if code.startswith("6") else f"sz.{code}"


def fetch_all_data() -> dict:
    """用baostock批量获取后复权日线数据"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    lg = bs.login()
    print(f"baostock登录: {lg.error_msg}")

    all_data = {}
    codes = STOCK_POOL[:MAX_STOCKS]

    for i, code in enumerate(codes):
        cache_file = os.path.join(CACHE_DIR, f"{code}.parquet")

        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
        else:
            rs = bs.query_history_k_data_plus(
                to_bs_code(code), "date,close,volume",
                start_date=START_DATE, end_date=END_DATE,
                frequency="d", adjustflag="2"
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            if not rows:
                continue
            df = pd.DataFrame(rows, columns=["date", "close", "volume"])
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
            df = df.dropna(subset=["close"])
            df = df[df["close"] > 0].sort_values("date").reset_index(drop=True)
            df.to_parquet(cache_file)

        if len(df) > 252:
            all_data[code] = df

        if (i + 1) % 50 == 0:
            print(f"  进度 {i+1}/{len(codes)}，成功 {len(all_data)}")

    bs.logout()
    print(f"最终有效股票: {len(all_data)}")
    return all_data


def calc_momentum(all_data: dict) -> pd.DataFrame:
    close_dict = {code: df.set_index("date")["close"].rename(code) for code, df in all_data.items()}
    close_df = pd.DataFrame(close_dict).sort_index()
    ret_12m = close_df.pct_change(252)
    ret_1m = close_df.pct_change(21)
    return (1 + ret_12m) / (1 + ret_1m) - 1


def get_monthly_deciles(momentum: pd.DataFrame) -> pd.DataFrame:
    monthly_idx = momentum.resample("ME").last().dropna(how="all").index
    deciles = {}
    for date in monthly_idx:
        mom = momentum.loc[:date].iloc[-1].dropna()
        if len(mom) < 20:
            continue
        ranks = mom.rank(pct=True)
        decile = np.ceil(ranks * 10).clip(1, 10).astype(int)
        deciles[date] = decile
    return pd.DataFrame(deciles).T


def assign_month_day(dates: pd.DatetimeIndex, month_ends: list) -> dict:
    all_day_map = {}
    for me in month_ends:
        pre_days = dates[dates < me].sort_values(ascending=False)
        post_days = dates[dates > me].sort_values()
        for i, d in enumerate(pre_days[:15]):
            all_day_map[d] = -(i + 1)
        for i, d in enumerate(post_days[:10]):
            all_day_map[d] = i + 1
    return all_day_map


def calc_returns_by_rel_day(all_data: dict, deciles_df: pd.DataFrame, day_map: dict) -> pd.DataFrame:
    daily_returns = {code: df.set_index("date")["close"].pct_change().rename(code) for code, df in all_data.items()}
    ret_df = pd.DataFrame(daily_returns).sort_index()

    records = []
    for date, rel_day in day_map.items():
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


def analyze_pretom(records_df: pd.DataFrame) -> dict:
    pretom = records_df[records_df["rel_day"].between(-9, -4)]
    other = records_df[~records_df["rel_day"].between(-9, -4)]
    post = records_df[records_df["rel_day"].between(-3, 3)]
    return {
        "pretom": pretom.groupby("decile")["return"].mean() * 10000,
        "other": other.groupby("decile")["return"].mean() * 10000,
        "post": post.groupby("decile")["return"].mean() * 10000,
    }


def statistical_tests(records_df: pd.DataFrame):
    pretom = records_df[records_df["rel_day"].between(-9, -4)]
    other = records_df[~records_df["rel_day"].between(-9, -4)]

    print("\n===== 统计检验 =====")

    lo_p = pretom[pretom["decile"] == 1]["return"]
    lo_o = other[other["decile"] == 1]["return"]
    t1, p1 = stats.ttest_ind(lo_p, lo_o)
    print(f"输家(D1): PreTOM={lo_p.mean()*10000:.2f}bps, 其余日={lo_o.mean()*10000:.2f}bps, t={t1:.2f}, p={p1:.4f}")

    hi_p = pretom[pretom["decile"] == 10]["return"]
    hi_o = other[other["decile"] == 10]["return"]
    t2, p2 = stats.ttest_ind(hi_p, hi_o)
    print(f"赢家(D10): PreTOM={hi_p.mean()*10000:.2f}bps, 其余日={hi_o.mean()*10000:.2f}bps, t={t2:.2f}, p={p2:.4f}")

    pd_ = pretom.groupby(["date", "decile"])["return"].mean().unstack()
    od_ = other.groupby(["date", "decile"])["return"].mean().unstack()
    if 1 in pd_.columns and 10 in pd_.columns and 1 in od_.columns and 10 in od_.columns:
        wml_p = pd_[10] - pd_[1]
        wml_o = od_[10] - od_[1]
        t3, p3 = stats.ttest_ind(wml_p.dropna(), wml_o.dropna())
        print(f"WML(10-1): PreTOM={wml_p.mean()*10000:.2f}bps, 其余日={wml_o.mean()*10000:.2f}bps, t={t3:.2f}, p={p3:.4f}")

    total_wml = records_df.groupby("date").apply(
        lambda g: g[g["decile"] == 10]["return"].mean() - g[g["decile"] == 1]["return"].mean()
    )
    pretom_dates = records_df[records_df["rel_day"].between(-9, -4)]["date"].unique()
    pretom_wml = total_wml[total_wml.index.isin(pretom_dates)]
    ratio = pretom_wml.sum() / total_wml.sum() if total_wml.sum() != 0 else 0
    print(f"\nPreTOM窗口贡献了动量多空收益的 {ratio*100:.1f}%")


def plot_results(records_df: pd.DataFrame, analysis: dict):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 图1: WML按月内日分布
    ax = axes[0, 0]
    rel_days = sorted([d for d in records_df["rel_day"].unique() if -12 <= d <= 6])
    wml_by_day = []
    for d in rel_days:
        sub = records_df[records_df["rel_day"] == d]
        lo = sub[sub["decile"] == 1]["return"].mean()
        hi = sub[sub["decile"] == 10]["return"].mean()
        wml_by_day.append((hi - lo) * 10000)

    colors = ["#e74c3c" if -9 <= d <= -4 else "#3498db" for d in rel_days]
    ax.bar(range(len(rel_days)), wml_by_day, color=colors, alpha=0.8, edgecolor="white")
    ax.set_xticks(range(len(rel_days)))
    ax.set_xticklabels([f"T{'+' if d > 0 else ''}{d}" for d in rel_days], rotation=45)
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("动量多空组合(WML) 按月内相对交易日\n红色=PreTOM窗口 [T-9, T-4]")
    ax.axhline(0, color="black", linewidth=0.5)

    # 图2: PreTOM各分位
    ax = axes[0, 1]
    pretom = analysis["pretom"]
    deciles = sorted(pretom.index)
    colors2 = plt.cm.RdYlGn(np.linspace(0, 1, len(deciles)))
    ax.bar(deciles, [pretom.get(d, 0) for d in deciles], color=colors2, edgecolor="white")
    ax.set_xlabel("动量分位 (1=输家, 10=赢家)")
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("PreTOM窗口 [T-9, T-4] 各分位日均收益")
    ax.axhline(0, color="black", linewidth=0.5)

    # 图3: 三窗口对比
    ax = axes[1, 0]
    other = analysis["other"]
    post = analysis["post"]
    x = np.arange(len(deciles))
    w = 0.25
    ax.bar(x - w, [pretom.get(d, 0) for d in deciles], w, label="PreTOM [T-9, T-4]", color="#e74c3c", alpha=0.8)
    ax.bar(x, [other.get(d, 0) for d in deciles], w, label="其余交易日", color="#3498db", alpha=0.8)
    ax.bar(x + w, [post.get(d, 0) for d in deciles], w, label="Post [T-3, T+3]", color="#2ecc71", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(deciles)
    ax.set_xlabel("动量分位")
    ax.set_ylabel("日均收益 (bps)")
    ax.set_title("各窗口下的分位收益对比")
    ax.legend()
    ax.axhline(0, color="black", linewidth=0.5)

    # 图4: 累计净值
    ax = axes[1, 1]
    rs = records_df.sort_values("date")
    for decile, label in [(1, "输家(D1)"), (10, "赢家(D10)")]:
        sp = rs[(rs["decile"] == decile) & rs["rel_day"].between(-9, -4)]
        so = rs[(rs["decile"] == decile) & ~rs["rel_day"].between(-9, -4)]
        if len(sp) > 0:
            ax.plot(range(len(sp)), (1 + sp["return"]).cumprod().values, label=f"{label} PreTOM")
        if len(so) > 0:
            ax.plot(range(len(so)), (1 + so["return"]).cumprod().values, label=f"{label} 其余日", alpha=0.5)
    ax.set_xlabel("交易日序号")
    ax.set_ylabel("累计净值")
    ax.set_title("输家/赢家 在PreTOM vs 其余交易日的累计收益")
    ax.legend(fontsize=8)
    ax.axhline(1, color="black", linewidth=0.5)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intramonth_result.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"图表已保存: {out}")


def main():
    print("=" * 60)
    print("A股月内动量周期回测")
    print(f"回测区间: {START_DATE} ~ {END_DATE}")
    print(f"股票池: {min(len(STOCK_POOL), MAX_STOCKS)} 只")
    print("=" * 60)

    print("\n[1/5] 获取股票数据...")
    all_data = fetch_all_data()

    print("\n[2/5] 计算动量信号...")
    momentum = calc_momentum(all_data)

    print("\n[3/5] 每月末动量十分位分组...")
    deciles_df = get_monthly_deciles(momentum)
    print(f"共 {len(deciles_df)} 个月的分组数据")

    print("\n[4/5] 计算月内相对交易日收益...")
    dates = pd.DatetimeIndex(sorted(set().union(*[set(d["date"]) for d in all_data.values()])))
    month_ends = sorted(deciles_df.index)
    day_map = assign_month_day(dates, month_ends)
    records_df = calc_returns_by_rel_day(all_data, deciles_df, day_map)
    print(f"共 {len(records_df)} 条观测")

    print("\n[5/5] 分析结果...")
    analysis = analyze_pretom(records_df)

    print("\n===== PreTOM [T-9, T-4] 各分位日均收益 (bps) =====")
    for d in sorted(analysis["pretom"].index):
        print(f"  D{d:2d}: {analysis['pretom'][d]:+.2f}")

    print("\n===== 其余交易日各分位日均收益 (bps) =====")
    for d in sorted(analysis["other"].index):
        print(f"  D{d:2d}: {analysis['other'][d]:+.2f}")

    statistical_tests(records_df)
    plot_results(records_df, analysis)
    return records_df, analysis


if __name__ == "__main__":
    records_df, analysis = main()
