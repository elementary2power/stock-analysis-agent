import time

import requests

_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def normalize_symbol(symbol: str) -> str:
    """将 sh600519 / 600519.SH 等常见格式统一为 6 位数字代码。"""
    digits = "".join(ch for ch in symbol if ch.isdigit())
    if len(digits) != 6:
        raise ValueError(f"无效的股票代码: {symbol!r}（示例: 600519）")
    return digits


def _secid(code: str) -> str:
    market = "1" if code.startswith(("6", "9")) else "0"
    return f"{market}.{code}"


def get_recent_daily(symbol: str, days: int = 10, retries: int = 3) -> tuple[str, list[dict]]:
    """获取 A 股最近 N 个交易日的日线行情（前复权，按日期升序）。

    直连东方财富公开行情接口，返回 (股票名称, 行情列表)。
    该接口会拒绝无浏览器 UA 的请求且偶发断连，故携带 UA 并内置重试。
    """
    code = normalize_symbol(symbol)
    params = {
        "secid": _secid(code),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "end": "20500101",
        "lmt": str(days),
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
    }
    last_error = None
    payload = None
    for attempt in range(retries):
        try:
            resp = requests.get(_KLINE_URL, params=params, headers=_HEADERS, timeout=10)
            resp.raise_for_status()
            payload = resp.json()
            break
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1 + attempt)
    if payload is None:
        raise RuntimeError(f"获取 {code} 行情失败，请稍后重试") from last_error
    data = payload.get("data") or {}
    bars = []
    for line in data.get("klines") or []:
        parts = line.split(",")
        if len(parts) < 10:
            continue
        bars.append(
            {
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": int(float(parts[5])),
                "change_pct": float(parts[8]),
            }
        )
    return data.get("name") or "", bars
