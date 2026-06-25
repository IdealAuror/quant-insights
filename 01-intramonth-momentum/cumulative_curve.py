import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
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

    full = rdf[rdf["rel_day"].between(-6, 5)]

    # mean daily return per decile per relative day
    daily_mean = full.groupby(["rel_day", "decile"])["return"].mean().unstack()

    days = list(range(-6, 6))
    labels = [f"T{'+' if d > 0 else ''}{d}" for d in days]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # ---- Top row: cumulative return by decile ----
    for col_idx, (deciles_to_plot, title_text) in enumerate([
        ([1, 2, 3], "输家组 (D1-D3)"),
        ([8, 9, 10], "赢家组 (D8-D10)"),
    ]):
        ax = axes[0][col_idx]
        colors = ["#c0392b", "#e74c3c", "#f1948a"] if col_idx == 0 else ["#85c1e9", "#3498db", "#2471a3"]
        for i, dec in enumerate(deciles_to_plot):
            if dec not in daily_mean.columns:
                continue
            cum = daily_mean[dec].reindex(days).fillna(0).cumsum() * 10000
            ax.plot(range(len(days)), cum.values, marker="o", color=colors[i],
                    lw=2.5, markersize=7, label=f"D{dec}", zorder=3)
            # annotate start and end
            ax.annotate(f"{cum.values[0]:+.0f}", (0, cum.values[0]),
                        textcoords="offset points", xytext=(-10, 10), fontsize=9, color=colors[i])
            ax.annotate(f"{cum.values[-1]:+.0f}", (len(days)-1, cum.values[-1]),
                        textcoords="offset points", xytext=(8, 5), fontsize=9, fontweight="bold", color=colors[i])

        ax.axvline(6, color="k", lw=1.2, ls=":", alpha=0.4)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(labels, fontsize=10)
        ax.set_ylabel("Cumulative Return (bps)", fontsize=11)
        ax.set_title(title_text, fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        # shade zones
        for i in range(len(days)):
            if days[i] <= -4:
                ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="red", zorder=0)
            elif days[i] >= 1:
                ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="green", zorder=0)

    # ---- Bottom left: D1 vs D10 cumulative ----
    ax = axes[1][0]
    for dec, color, label in [(1, "#c0392b", "Loser D1"), (10, "#2471a3", "Winner D10")]:
        cum = daily_mean[dec].reindex(days).fillna(0).cumsum() * 10000
        ax.plot(range(len(days)), cum.values, marker="o", color=color,
                lw=3, markersize=8, label=label, zorder=3)
        ax.annotate(f"{cum.values[-1]:+.0f}", (len(days)-1, cum.values[-1]),
                    textcoords="offset points", xytext=(8, 5), fontsize=11, fontweight="bold", color=color)
    ax.fill_between(range(len(days)),
                    daily_mean[1].reindex(days).fillna(0).cumsum().values * 10000,
                    daily_mean[10].reindex(days).fillna(0).cumsum().values * 10000,
                    alpha=0.15, color="#8e44ad", zorder=0)
    ax.axvline(6, color="k", lw=1.2, ls=":", alpha=0.4)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Cumulative Return (bps)", fontsize=11)
    ax.set_title("Loser D1 vs Winner D10", fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    for i in range(len(days)):
        if days[i] <= -4:
            ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="red", zorder=0)
        elif days[i] >= 1:
            ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="green", zorder=0)

    # ---- Bottom right: WML cumulative ----
    ax = axes[1][1]
    wml_daily = daily_mean[10] - daily_mean[1]
    wml_cum = wml_daily.reindex(days).fillna(0).cumsum() * 10000
    colors_wml = ["#8e44ad" if v >= 0 else "#e67e22" for v in wml_daily.reindex(days).fillna(0).values]
    ax.plot(range(len(days)), wml_cum.values, marker="o", color="#8e44ad",
            lw=3, markersize=8, label="WML (D10-D1)", zorder=3)
    ax.fill_between(range(len(days)), 0, wml_cum.values,
                    where=wml_cum.values >= 0, alpha=0.2, color="#8e44ad", zorder=0)
    ax.fill_between(range(len(days)), 0, wml_cum.values,
                    where=wml_cum.values < 0, alpha=0.2, color="#e67e22", zorder=0)
    ax.axvline(6, color="k", lw=1.2, ls=":", alpha=0.4)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Cumulative Return (bps)", fontsize=11)
    ax.set_title("WML Cumulative: T-6 to T+5", fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    for i in range(len(days)):
        if days[i] <= -4:
            ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="red", zorder=0)
        elif days[i] >= 1:
            ax.axvspan(i-0.5, i+0.5, alpha=0.06, color="green", zorder=0)
    # annotate
    ax.annotate(f"Peak: +{wml_cum.values[:7].max():.0f}", xy=(np.argmax(wml_cum.values[:7]), wml_cum.values[:7].max()),
                xytext=(-40, 20), textcoords="offset points", fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#8e44ad"))

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cumulative_curve.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out}")

if __name__ == "__main__":
    main()
