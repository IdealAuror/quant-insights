# ============================================================
# 策略名称：价值成长双策略（绝对PE锚定版）
# 标的：红利ETF(510880) + 创业板ETF(159915) + 银华日利(511880)
# 核心：沪深300 PE<13满仓95%，PE>17轻仓30%，中间线性变化
# 无趋势过滤，无波动率因子，纯粹PE+动量+网格止盈
# 回测区间：2019-01-01 至 2026-06-11
# 回测结果：累计+150.62%（基准+57.73%）| 最大回撤-26.19% | Alpha+0.08
# ============================================================

from jqdata import *
import numpy as np
import pandas as pd


# ==================== 初始化 ====================

def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)

    g.val_etf = '510880.XSHG'    # 红利ETF（价值池）
    g.grow_etf = '159915.XSHE'   # 创业板ETF（成长池）
    g.safe_etf = '511880.XSHG'   # 银华日利（现金管理）

    # 价值策略参数
    g.v_buy = 0.08            # 允许价格高于年线8%以内买入
    g.v_sell = 0.18           # 第一档止盈：涨超18%
    g.v_sell_high = 0.30      # 第二档清仓：涨超30%
    g.v_sub_rsi_buy = 30      # RSI超卖买入阈值
    g.v_sub_rsi_sell = 70     # RSI超买卖出阈值
    g.v_peak_drop = 5         # RSI峰值回落止盈幅度（点）
    g.v_buy_cnt = 0           # 价值主仓买入计数
    g.v_sell_cnt = 0          # 价值主仓卖出计数
    g.v_last_buy = None       # 上次买入日期
    g.v_sub_on = False        # 辅仓持有标志
    g.v_peak_rsi = 0          # RSI峰值追踪
    g.v_buy_price = 0         # 最后一次买入价

    # 成长策略状态
    g.g_hold = False          # 成长持仓标志
    g.g_high_price = 0        # 持仓期间最高价（止损用）

    set_order_cost(OrderCost(close_tax=0, open_commission=0.0003,
                             close_commission=0.0003, min_commission=5), type='fund')
    run_daily(trade, time='14:50')


# ==================== 辅助函数 ====================

def rsi(close, n=14):
    """Wilder RSI(14) 计算"""
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - (100 / (1 + up / dn))


def get_pe(context):
    """获取沪深300当前PE_TTM绝对值"""
    try:
        q = query(valuation).filter(valuation.code == '000300.XSHG')
        df = get_fundamentals(q, date=context.current_dt, fields=['pe_ttm'])
        if df is None or len(df) == 0:
            return 13.0
        return df['pe_ttm'].iloc[0]
    except:
        return 13.0


# ==================== 主交易逻辑 ====================

def trade(context):
    tv = context.portfolio.total_value
    today = context.current_dt.date()

    pe = get_pe(context)

    # ---- 第一层：绝对PE仓位映射（锚定A股长期中枢） ----
    # PE=13 -> 95%, PE=15 -> 65%, PE=17 -> 30%
    if pe < 13:
        equity_ratio = 0.95
        min_hold_ratio = 0.40
        is_low = True
        is_high = False
    elif pe < 15:
        equity_ratio = 0.95 - (pe - 13) * 0.15
        min_hold_ratio = 0.40 - (pe - 13) * 0.10
        is_low = True
        is_high = False
    elif pe < 17:
        equity_ratio = 0.65 - (pe - 15) * 0.175
        min_hold_ratio = 0.20 - (pe - 15) * 0.05
        is_low = False
        is_high = True
    else:
        equity_ratio = 0.30
        min_hold_ratio = 0.10
        is_low = False
        is_high = True

    equity_ratio = max(0.30, min(0.95, equity_ratio))
    min_hold_ratio = max(0.10, min(0.40, min_hold_ratio))

    log.info('PE=%.1f | 总权益上限%.0f%% | 单池底仓%.0f%%',
             pe, equity_ratio * 100, min_hold_ratio * 100)

    # ---- 第二层：动量分配（仅决定买哪个，不决定总仓位） ----
    try:
        df_v_ret = attribute_history(g.val_etf, 20, '1d', ['close'], skip_paused=True)
        df_g_ret = attribute_history(g.grow_etf, 20, '1d', ['close'], skip_paused=True)
        if len(df_v_ret) >= 10 and len(df_g_ret) >= 10:
            val_ret = df_v_ret['close'].iloc[-1] / df_v_ret['close'].iloc[0] - 1
            grow_ret = df_g_ret['close'].iloc[-1] / df_g_ret['close'].iloc[0] - 1
            if grow_ret > val_ret:
                val_weight, grow_weight = 0.40, 0.60
            else:
                val_weight, grow_weight = 0.60, 0.40
        else:
            val_weight, grow_weight = 0.5, 0.5
    except:
        val_weight, grow_weight = 0.5, 0.5

    max_v_cash = tv * equity_ratio * val_weight
    max_g_cash = tv * equity_ratio * grow_weight
    v_min_hold = min(tv * min_hold_ratio, max_v_cash)
    g_min_hold = min(tv * min_hold_ratio, max_g_cash)

    # ---- 第三层A：价值池（红利ETF 510880）—— 网格定投 + RSI辅仓 ----
    df_v = attribute_history(g.val_etf, 280, '1d', ['close'], skip_paused=True)
    v_target_val = v_min_hold

    if df_v is not None and len(df_v) >= 250:
        c = df_v['close']
        price = c.iloc[-1]
        ma250 = c.rolling(250).mean().iloc[-1]
        ma20 = c.rolling(20).mean().iloc[-1]
        dev = price / ma250 - 1
        rsi14 = rsi(c, 14).iloc[-1]

        # 计算当前主仓比例
        main_pct = 0
        if g.v_buy_cnt > 0:
            main_pct = 0.25 * g.v_buy_cnt * 0.8
            for _ in range(g.v_sell_cnt):
                main_pct *= 0.7
            main_pct = max(main_pct, 0.08)

        # 买入：PE<15时日频，否则隔3天
        if is_low:   # PE < 15，低估区域加速建仓
            buy_interval = 1
            buy_threshold = g.v_buy  # 8%溢价以内
        else:        # PE >= 15，正常节奏
            buy_interval = 3
            buy_threshold = 0.03

        if dev < buy_threshold and g.v_buy_cnt < 4:
            if g.v_last_buy is None or (today - g.v_last_buy).days >= buy_interval:
                g.v_buy_cnt += 1
                g.v_last_buy = today
                g.v_buy_price = price
                main_pct = 0.25 * g.v_buy_cnt * 0.8
                log.info('价值买入 %d/4 | 偏离 %.2f%% (日频)' if is_low else '价值买入 %d/4 | 偏离 %.2f%%',
                         g.v_buy_cnt, dev * 100)

        # 卖出（高估区强制减仓，但不低于底仓）
        if is_high and main_pct > 0.08:  # PE >= 15 且偏高
            if dev > 0:
                v_target_val = v_min_hold
                log.info('高估风控：价值减至底仓%.0f%% | 偏离%.2f%%', min_hold_ratio * 100, dev * 100)
        elif dev > g.v_sell and main_pct > 0.08:
            if dev > g.v_sell_high:
                # 第二档：清仓至底仓
                v_target_val = v_min_hold
                log.info('价值清仓至底仓 | 偏离%.2f%%', dev * 100)
            elif g.v_sell_cnt < 3:
                # 第一档：卖30%仓位
                g.v_sell_cnt += 1
                main_pct = max(main_pct * 0.7, 0.08)
                log.info('价值卖出 %d/3 | 偏离 %.2f%%', g.v_sell_cnt, dev * 100)

        # 辅仓（RSI超卖买入）
        sub_pct = 0
        if not g.v_sub_on:
            if rsi14 < g.v_sub_rsi_buy and price < ma20:
                g.v_sub_on = True
                g.v_peak_rsi = rsi14
                sub_pct = 0.2
                log.info('价值辅仓买入 | RSI %.1f', rsi14)
        else:
            if rsi14 > g.v_peak_rsi:
                g.v_peak_rsi = rsi14
            if g.v_peak_rsi >= g.v_sub_rsi_sell and (g.v_peak_rsi - rsi14) >= g.v_peak_drop:
                g.v_sub_on = False
                log.info('价值辅仓止盈')
            elif rsi14 < 20:
                g.v_sub_on = False
                log.info('价值辅仓止损')
            else:
                sub_pct = 0.2

        grid_val = max_v_cash * (main_pct + sub_pct)
        v_target_val = max(v_min_hold, grid_val)
        v_target_val = min(v_target_val, max_v_cash)

    # ---- 第三层B：成长池（创业板ETF 159915）—— 趋势跟随 ----
    df_g = attribute_history(g.grow_etf, 280, '1d', ['close'], skip_paused=True)
    g_target_val = g_min_hold

    if df_g is not None and len(df_g) >= 250:
        cg = df_g['close']
        price_g = cg.iloc[-1]
        ma250_g = cg.rolling(250).mean().iloc[-1]
        vol_df = attribute_history(g.grow_etf, 20, '1d', ['volume'], skip_paused=True)
        vol_ma20 = vol_df['volume'].mean() if vol_df is not None else 1

        # 买入信号
        if is_low:
            # PE<15左侧买入：站上年线*0.95且缩量
            buy_sig = price_g > ma250_g * 0.95 and (vol_df is None or vol_df['volume'].iloc[-1] < vol_ma20 * 1.2)
        else:
            # PE>=15右侧买入：站上年线*1.02
            buy_sig = price_g > ma250_g * 1.02
        sell_sig = price_g < ma250_g * 0.92

        # 高估风控
        if is_high and g.g_hold:
            g_target_val = g_min_hold
            g.g_hold = False
            g.g_high_price = 0
            log.info('高估风控：成长清仓至底仓%.0f%%', min_hold_ratio * 100)
        elif not g.g_hold and buy_sig:
            # 买入
            g.g_hold = True
            g.g_high_price = price_g
            log.info('成长买入 | 价 %.3f (PE<15左侧)' if is_low else '成长买入 | 价 %.3f', price_g)
        elif g.g_hold:
            # 持仓中：追踪最高价 + 止损检查
            if price_g > g.g_high_price:
                g.g_high_price = price_g
            if (g.g_high_price - price_g) / g.g_high_price > 0.08 or sell_sig:
                g.g_hold = False
                g_target_val = g_min_hold
                g.g_high_price = 0
                log.info('成长止损/破位卖出 | 价 %.3f', price_g)

        if g.g_hold:
            g_target_val = max_g_cash
        else:
            g_target_val = g_min_hold
        g_target_val = min(g_target_val, max_g_cash)

    # ---- 总仓位硬约束 ----
    total_target = v_target_val + g_target_val
    max_equity = tv * equity_ratio
    if total_target > max_equity:
        scale = max_equity / total_target
        v_target_val *= scale
        g_target_val *= scale

    # ---- 执行 ----
    order_target_value(g.val_etf, v_target_val)
    order_target_value(g.grow_etf, g_target_val)
    order_target_value(g.safe_etf, tv - v_target_val - g_target_val)

    actual_equity = v_target_val + g_target_val
    log.info('执行 | 价值%.0f元(%.0f%%) 成长%.0f元(%.0f%%) 总仓%.0f%%',
             v_target_val, v_target_val / tv * 100,
             g_target_val, g_target_val / tv * 100,
             actual_equity / tv * 100)
