import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy import stats
import warnings, os

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

START_DATE, END_DATE, MAX_STOCKS = "2016-01-01", "2025-12-31", 100
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

STOCK_POOL = [
    "600519","601318","600036","600276","601166","600030","600900","601398","600028","600887",
    "601888","600309","601012","600690","600050","601668","600585","600000","601288","600104",
    "600016","601601","601328","600019","601225","600809","601857","600048","600196","601688",
    "600346","601138","600837","601211","600741","601628","600606","601390","600176","601669",
    "600460","600703","601111","600436","601877","600132","601919","600406","601899","600918",
    "601816","600183","601186","600547","601088","600570","600332","601006","600298","601336",
    "600795","600029","601985","600031","601021","600660","601800","600009","601865","600111",
    "601766","600383","601236","600271","601009","600938","601838","600600","601633","600893",
    "601155","600845","601989","600760","603259","603288","603501","603799","603986","603160",
    "603993","603369","603899","603486","603613","603658","603260","603882","603127","603605",
    "000858","000333","002714","000568","000651","000002","000001","000725","002415","000661",
    "000063","002304","000876","002027","000338","002352","000538","002142","000166","002049",
    "000100","000776","002050","002230","000895","000049","000423","002241","000703","002001",
    "002032","000983","002007","000977","000625","002594","002475","000708","002120","000839",
    "002081","000768","002008","000400","002558","000069","000961","002372","002601","000656",
    "002311","002129","000887","002271","002791","000963","000157","000627","002410","000596",
    "002736","002385","000786","002607","002202","002340","002179","000408","002065","002157",
    "300750","300059","300760","300124","300274","300122","300015","300033","300142","300014",
    "300529","300408","300347","300413","300136","300308","300316","300628","300207","300498",
    "300253","300123","300433","300003","300257","300285","300146","300394","300357","300244",
    "300037","300115","300363","300457","300390","300595","300773","300395","300726","300699",
    "300682","300392","300502","300083","300566","300326","300212","300399","300271","300487",
]

def to_bs_code(c): return f"sh.{c}" if c.startswith("6") else f"sz.{c}"

def fetch_all():
    lg = bs.login()
    d = {}
    for c in STOCK_POOL[:MAX_STOCKS]:
        f = os.path.join(CACHE_DIR, f"{c}.parquet")
        if os.path.exists(f):
            df = pd.read_parquet(f)
        else:
            rs = bs.query_history_k_data_plus(to_bs_code(c), "date,close,volume",
                start_date=START_DATE, end_date=END_DATE, frequency="d", adjustflag="2")
            rows = []
            while rs.error_code == "0" and rs.next(): rows.append(rs.get_row_data())
            if not rows: continue
            df = pd.DataFrame(rows, columns=["date","close","volume"])
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df = df.dropna(subset=["close"]).query("close > 0").sort_values("date").reset_index(drop=True)
            df.to_parquet(f)
        if len(df) > 252: d[c] = df
    bs.logout()
    return d

def build_records(all_data):
    cd = {c: df.set_index("date")["close"].rename(c) for c, df in all_data.items()}
    cdf = pd.DataFrame(cd).sort_index()
    mom = (1 + cdf.pct_change(252)) / (1 + cdf.pct_change(21)) - 1
    mi = mom.resample("ME").last().dropna(how="all").index
    dec = {}
    for dt in mi:
        m = mom.loc[:dt].iloc[-1].dropna()
        if len(m) < 20: continue
        dec[dt] = np.ceil(m.rank(pct=True) * 10).clip(1, 10).astype(int)
    dec_df = pd.DataFrame(dec).T
    dates = pd.DatetimeIndex(sorted(set().union(*[set(d["date"]) for d in all_data.values()])))
    dm = {}
    for me in sorted(dec_df.index):
        for i, d in enumerate(dates[dates < me].sort_values(ascending=False)[:20]): dm[d] = -(i+1)
        for i, d in enumerate(dates[dates > me].sort_values()[:15]): dm[d] = i+1
    dr = {c: df.set_index("date")["close"].pct_change().rename(c) for c, df in all_data.items()}
    ret_df = pd.DataFrame(dr).sort_index()
    recs = []
    for date, rd in dm.items():
        if date not in ret_df.index: continue
        vm = dec_df.index[dec_df.index <= date]
        if len(vm) == 0: continue
        dm_row = dec_df.loc[vm[-1]]
        for code in ret_df.columns:
            if code not in dm_row.index: continue
            r = ret_df.loc[date, code]
            dv = dm_row[code]
            if pd.notna(r) and pd.notna(dv):
                recs.append({"date": date, "rel_day": rd, "decile": int(dv), "return": r})
    return pd.DataFrame(recs)

def main():
    print("loading...")
    data = fetch_all()
    rdf = build_records(data)

    # Full window T-6 to T+5
    full = rdf[rdf["rel_day"].between(-6, 5)]
    other = rdf[~rdf["rel_day"].between(-9, 5)]
    base_lo = other[other["decile"] == 1]["return"]
    base_hi = other[other["decile"] == 10]["return"]
    base_wml = other.groupby("date").apply(lambda g: g[g["decile"]==10]["return"].mean() - g[g["decile"]==1]["return"].mean())

    print("\n" + "="*75)
    print("  FULL CYCLE: T-6 to T+5  (12 trading days)")
    print("="*75)
    print(f"  {'Day':>5}  {'Loser':>10}  {'Winner':>10}  {'WML':>10}  {'L_t':>7}  {'L_p':>8}  {'W_t':>7}  {'W_p':>8}  Sig")
    print("-"*75)

    stats_list = []
    for d in range(-6, 6):
        sub = full[full["rel_day"] == d]
        if len(sub) == 0:
            continue
        lo = sub[sub["decile"] == 1]["return"]
        hi = sub[sub["decile"] == 10]["return"]
        wml_day = sub.groupby("date").apply(lambda g: g[g["decile"]==10]["return"].mean() - g[g["decile"]==1]["return"].mean())
        t_lo, p_lo = stats.ttest_ind(lo, base_lo)
        t_hi, p_hi = stats.ttest_ind(hi, base_hi)
        sig_lo = "***" if p_lo < 0.001 else "** " if p_lo < 0.01 else "*  " if p_lo < 0.05 else "   "
        sig_hi = "***" if p_hi < 0.001 else "** " if p_hi < 0.01 else "*  " if p_hi < 0.05 else "   "
        label = f"T{'+' if d > 0 else ''}{d}"
        stats_list.append({"d": d, "label": label, "lo": lo.mean()*1e4, "hi": hi.mean()*1e4,
                           "wml": wml_day.mean()*1e4, "t_lo": t_lo, "p_lo": p_lo,
                           "t_hi": t_hi, "p_hi": p_hi, "sig_lo": sig_lo, "sig_hi": sig_hi})
        print(f"  {label:>5}  {lo.mean()*1e4:>+9.2f}  {hi.mean()*1e4:>+9.2f}  {wml_day.mean()*1e4:>+9.2f}  "
              f"{t_lo:>+6.2f}  {p_lo:>7.4f}  {t_hi:>+6.2f}  {p_hi:>7.4f}  {sig_lo}{sig_hi}")

    print("-"*75)
    print(f"  base  {base_lo.mean()*1e4:>+9.2f}  {base_hi.mean()*1e4:>+9.2f}  {base_wml.mean()*1e4:>+9.2f}")

    # ========== Plot ==========
    fig, axes = plt.subplots(3, 1, figsize=(16, 16), sharex=True)
    labels = [s["label"] for s in stats_list]
    x = np.arange(len(labels))

    # Colors: PreTOM zone (red bg), TOM zone (green bg)
    zone_colors = []
    for s in stats_list:
        if s["d"] <= -4:
            zone_colors.append("#fde8e8")  # light red
        elif s["d"] >= 1:
            zone_colors.append("#e8fde8")  # light green
        else:
            zone_colors.append("#f5f5f5")  # neutral

    # --- Panel 1: Loser ---
    ax = axes[0]
    for i, s in enumerate(stats_list):
        ax.bar(i, s["lo"], color="#c0392b" if s["lo"] < 0 else "#27ae60",
               alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(i, s["lo"] + (2 if s["lo"] >= 0 else -4),
                f"{s['lo']:.1f}", ha="center", va="bottom" if s["lo"] >= 0 else "top",
                fontsize=10, fontweight="bold")
    ax.axhline(base_lo.mean()*1e4, color="gray", ls="--", alpha=0.7, lw=1.2,
               label=f"baseline={base_lo.mean()*1e4:.1f}bps")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(5.5, color="k", lw=1.5, ls=":", alpha=0.5)  # month boundary
    ax.set_ylabel("bps", fontsize=12)
    ax.set_title("Loser (D1) Daily Return: T-6 to T+5", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.text(2, ax.get_ylim()[1]*0.9, "PreTOM SELL", fontsize=11, color="#c0392b",
            ha="center", fontweight="bold", alpha=0.7)
    ax.text(9, ax.get_ylim()[1]*0.9, "TOM REBOUND", fontsize=11, color="#27ae60",
            ha="center", fontweight="bold", alpha=0.7)

    # --- Panel 2: Winner ---
    ax = axes[1]
    for i, s in enumerate(stats_list):
        ax.bar(i, s["hi"], color="#2980b9" if s["hi"] > 0 else "#e67e22",
               alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(i, s["hi"] + (2 if s["hi"] >= 0 else -4),
                f"{s['hi']:.1f}", ha="center", va="bottom" if s["hi"] >= 0 else "top",
                fontsize=10, fontweight="bold")
    ax.axhline(base_hi.mean()*1e4, color="gray", ls="--", alpha=0.7, lw=1.2,
               label=f"baseline={base_hi.mean()*1e4:.1f}bps")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(5.5, color="k", lw=1.5, ls=":", alpha=0.5)
    ax.set_ylabel("bps", fontsize=12)
    ax.set_title("Winner (D10) Daily Return: T-6 to T+5", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)

    # --- Panel 3: WML ---
    ax = axes[2]
    for i, s in enumerate(stats_list):
        ax.bar(i, s["wml"], color="#8e44ad" if s["wml"] > 0 else "#e67e22",
               alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(i, s["wml"] + (2 if s["wml"] >= 0 else -4),
                f"{s['wml']:.1f}", ha="center", va="bottom" if s["wml"] >= 0 else "top",
                fontsize=10, fontweight="bold")
    ax.axhline(base_wml.mean()*1e4, color="gray", ls="--", alpha=0.7, lw=1.2,
               label=f"baseline={base_wml.mean()*1e4:.1f}bps")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(5.5, color="k", lw=1.5, ls=":", alpha=0.5)
    ax.set_ylabel("bps", fontsize=12)
    ax.set_title("WML (Winner - Loser) Daily: T-6 to T+5", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)

    # X axis
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, fontweight="bold")

    # Add zone shading
    for a in axes:
        for i in range(len(stats_list)):
            if stats_list[i]["d"] <= -4:
                a.axvspan(i-0.5, i+0.5, alpha=0.08, color="red", zorder=0)
            elif stats_list[i]["d"] >= 1:
                a.axvspan(i-0.5, i+0.5, alpha=0.08, color="green", zorder=0)

    # Add month boundary annotation
    for a in axes:
        a.annotate("", xy=(5.5, a.get_ylim()[0]), xytext=(5.5, a.get_ylim()[1]),
                   arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))

    fig.text(0.5, 0.01, "Month End |", ha="center", fontsize=12, fontweight="bold")

    plt.tight_layout(rect=[0, 0.02, 1, 1])
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full_cycle.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out}")

if __name__ == "__main__":
    main()
