from statistics import fmean


def _slope_pct(closes: list[float]) -> float:
    """最小二乘拟合的每日百分比斜率。"""
    n = len(closes)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = fmean(closes)
    denom = sum((x - mean_x) ** 2 for x in range(n))
    if denom == 0 or mean_y == 0:
        return 0.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in enumerate(closes)) / denom
    return slope / mean_y * 100


def _sma_signal(closes: list[float]) -> tuple[int, str]:
    sma5 = fmean(closes[-5:])
    sma10 = fmean(closes[-10:])
    diff = (sma5 / sma10 - 1) * 100
    if diff >= 1:
        return 2, f"5日均线明显高于10日均线（{diff:+.2f}%）"
    if diff > 0:
        return 1, f"5日均线略高于10日均线（{diff:+.2f}%）"
    if diff <= -1:
        return -2, f"5日均线明显低于10日均线（{diff:+.2f}%）"
    if diff < 0:
        return -1, f"5日均线略低于10日均线（{diff:+.2f}%）"
    return 0, "5日均线与10日均线持平"


def _momentum_signal(closes: list[float]) -> tuple[int, str]:
    if len(closes) < 6:
        return 0, ""
    chg = (closes[-1] / closes[-6] - 1) * 100
    if chg >= 4:
        return 2, f"近5日涨幅较大（{chg:+.2f}%）"
    if chg >= 1:
        return 1, f"近5日温和上涨（{chg:+.2f}%）"
    if chg > -1:
        return 0, f"近5日横盘（{chg:+.2f}%）"
    if chg > -4:
        return -1, f"近5日温和下跌（{chg:+.2f}%）"
    return -2, f"近5日跌幅较大（{chg:+.2f}%）"


def _slope_signal(closes: list[float]) -> tuple[int, str]:
    slope = _slope_pct(closes)
    if slope >= 0.5:
        return 2, f"收盘价线性趋势向上（日均 {slope:+.2f}%）"
    if slope >= 0.15:
        return 1, f"收盘价线性趋势偏向上（日均 {slope:+.2f}%）"
    if slope > -0.15:
        return 0, f"收盘价线性趋势走平（日均 {slope:+.2f}%）"
    if slope > -0.5:
        return -1, f"收盘价线性趋势偏向下（日均 {slope:+.2f}%）"
    return -2, f"收盘价线性趋势向下（日均 {slope:+.2f}%）"


def _up_ratio_signal(closes: list[float]) -> tuple[int, str]:
    diffs = [b - a for a, b in zip(closes, closes[1:])]
    if not diffs:
        return 0, ""
    up = sum(1 for d in diffs if d > 0)
    down = sum(1 for d in diffs if d < 0)
    if up == 0 and down == 0:
        return 0, "近期无涨跌变化"
    ratio = up / len(diffs)
    pct = ratio * 100
    if ratio >= 0.7:
        return 2, f"近10日中 {pct:.0f}% 的交易日上涨"
    if ratio >= 0.6:
        return 1, f"近10日上涨交易日偏多（{pct:.0f}%）"
    if ratio > 0.4:
        return 0, f"近10日涨跌互现（上涨 {pct:.0f}%）"
    if ratio > 0.3:
        return -1, f"近10日下跌交易日偏多（上涨仅 {pct:.0f}%）"
    return -2, f"近10日中仅 {pct:.0f}% 的交易日上涨"


def _volume_signal(bars: list[dict], closes: list[float]) -> tuple[int, str]:
    vols = [bar["volume"] for bar in bars]
    if len(vols) < 6:
        return 0, ""
    base = fmean(vols[:-3])
    if base <= 0:
        return 0, ""
    ratio = (fmean(vols[-3:]) / base - 1) * 100
    if closes[-1] == closes[-2]:
        return 0, "量价关系中性"
    if closes[-1] > closes[-2]:
        if ratio >= 20:
            return 2, f"放量上涨（近3日成交量比前期高 {ratio:.0f}%）"
        return 1, f"上涨但量能未明显放大（量比 {ratio:+.0f}%）"
    if ratio >= 20:
        return -2, f"放量下跌（近3日成交量比前期高 {ratio:.0f}%）"
    return -1, f"下跌且量能萎缩（量比 {ratio:+.0f}%）"


def predict_trend(bars: list[dict]) -> dict:
    """基于近 N 日行情的简单技术面打分模型，预测次日趋势。

    综合 5 个信号（均线、动量、趋势斜率、阳线占比、量价配合），
    每个信号 -2~+2 分：总分 >=3 看涨、<=-3 看跌、其余为震荡。
    """
    closes = [bar["close"] for bar in bars]
    if len(closes) < 5:
        return {
            "direction": "数据不足",
            "score": 0.0,
            "confidence": 0.0,
            "reasons": ["历史数据不足（少于 5 个交易日），无法预测"],
        }
    signals = [
        _sma_signal(closes),
        _momentum_signal(closes),
        _slope_signal(closes),
        _up_ratio_signal(closes),
        _volume_signal(bars, closes),
    ]
    score = sum(s for s, _ in signals)
    reasons = [reason for s, reason in signals if s != 0 and reason]
    if score >= 3:
        direction = "看涨"
    elif score <= -3:
        direction = "看跌"
    else:
        direction = "震荡"
    confidence = round(min(95.0, abs(score) * 10), 1)
    return {
        "direction": direction,
        "score": float(score),
        "confidence": confidence,
        "reasons": reasons,
    }
