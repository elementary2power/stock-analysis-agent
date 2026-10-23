import time

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
_EASTMONEY_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
_TENCENT_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"


def normalize_symbol(symbol: str) -> str:
    """将 sh600519 / 600519.SH 等常见格式统一为 6 位数字代码。"""
    digits = "".join(ch for ch in symbol if ch.isdigit())
    if len(digits) != 6:
        raise ValueError(f"无效的股票代码: {symbol!r}（示例: 600519）")
    return digits


def _secid(code: str) -> str:
    market = "1" if code.startswith(("6", "9")) else "0"
    return f"{market}.{code}"


def _tencent_code(code: str) -> str:
    prefix = "sh" if code.startswith(("6", "9", "5")) else "sz"
    return f"{prefix}{code}"


def _get_json(url: str, params: dict, retries: int) -> dict:
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=_HEADERS, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1)
    raise RuntimeError(f"请求行情接口失败: {url}") from last_error


def _parse_eastmoney(payload: dict) -> tuple[str, list[dict]]:
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


def _parse_tencent(payload: dict, code: str) -> tuple[str, list[dict]]:
    tc = _tencent_code(code)
    node = (payload.get("data") or {}).get(tc) or {}
    qt_row = (node.get("qt") or {}).get(tc) or []
    name = str(qt_row[1]) if len(qt_row) > 1 and qt_row[1] else ""
    bars = []
    for row in node.get("qfqday") or node.get("day") or []:
        if len(row) < 6:
            continue
        bars.append(
            {
                "date": row[0],
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": int(float(row[5])),
                "change_pct": None,
            }
        )
    for i in range(1, len(bars)):
        prev_close = bars[i - 1]["close"]
        if prev_close > 0:
            bars[i]["change_pct"] = (bars[i]["close"] / prev_close - 1) * 100
    return name, bars


def _fetch_tencent(code: str, days: int, retries: int) -> tuple[str, list[dict]]:
    params = {"param": f"{_tencent_code(code)},day,,,{days + 1},qfq"}
    return _parse_tencent(_get_json(_TENCENT_URL, params, retries), code)


def _fetch_eastmoney(code: str, days: int, retries: int) -> tuple[str, list[dict]]:
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
    return _parse_eastmoney(_get_json(_EASTMONEY_URL, params, retries))


def get_recent_daily(symbol: str, days: int = 10, retries: int = 2) -> tuple[str, list[dict]]:
    """获取 A 股最近 N 个交易日的日线行情（前复权，按日期升序）。

    腾讯为主数据源、东方财富为备用源，单源失败自动切换，各自内置重试。
    返回 (股票名称, 行情列表)；上市时间过短时最早一根 K 线的涨跌幅为 None。
    """
    code = normalize_symbol(symbol)
    fallback: tuple[str, list[dict]] | None = None
    last_error: Exception | None = None
    for fetch in (_fetch_tencent, _fetch_eastmoney):
        try:
            name, bars = fetch(code, days, retries)
        except Exception as exc:
            last_error = exc
            continue
        if bars:
            return name, bars[-days:]
        if fallback is None:
            fallback = (name, bars)
    if fallback is not None:
        return fallback
    raise RuntimeError(f"获取 {code} 行情失败，请稍后重试") from last_error
