def sma(prices: list[float], window: int) -> float | None:
    """简单移动平均（SMA），数据不足时返回 None。"""
    if window <= 0 or len(prices) < window:
        return None
    return sum(prices[-window:]) / window
