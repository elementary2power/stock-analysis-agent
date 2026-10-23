import pytest

from stock_analysis_agent.data import market
from stock_analysis_agent.data.market import (
    _parse_eastmoney,
    _parse_tencent,
    _tencent_code,
    get_recent_daily,
)

TENCENT_PAYLOAD = {
    "code": 0,
    "data": {
        "sh600519": {
            "qfqday": [
                ["2026-10-21", "1331.88", "1309.69", "1331.98", "1302.36", "33514.00"],
                ["2026-10-22", "1303.21", "1318.49", "1322.00", "1296.00", "42491.00"],
                ["2026-10-23", "1311.84", "1336.66", "1343.88", "1310.00", "48555.00"],
            ],
            "qt": {"sh600519": ["51", "贵州茅台", "600519", "1336.66"]},
        }
    },
}

EASTMONEY_PAYLOAD = {
    "rc": 0,
    "data": {
        "name": "贵州茅台",
        "klines": [
            "2026-10-22,1303.21,1318.49,1322.00,1296.00,42491,557621700.00,1.99,0.67,8.80,0.34",
            "2026-10-23,1311.84,1336.66,1343.88,1310.00,48555,646260500.00,2.57,1.38,18.17,0.39",
        ],
    },
}


def make_bars(closes):
    return [
        {
            "date": f"2026-10-{9 + i:02d}",
            "open": close - 0.5,
            "close": close,
            "high": close + 1,
            "low": close - 1,
            "volume": 1000,
            "change_pct": 1.0,
        }
        for i, close in enumerate(closes)
    ]


@pytest.mark.parametrize(
    "code,expected",
    [
        ("600519", "sh600519"),
        ("688981", "sh688981"),
        ("000001", "sz000001"),
        ("300750", "sz300750"),
    ],
)
def test_tencent_code(code, expected):
    assert _tencent_code(code) == expected


def test_parse_tencent():
    name, bars = _parse_tencent(TENCENT_PAYLOAD, "600519")
    assert name == "贵州茅台"
    assert len(bars) == 3
    assert bars[0]["date"] == "2026-10-21"
    assert bars[0]["close"] == pytest.approx(1309.69)
    assert bars[0]["volume"] == 33514
    assert bars[0]["change_pct"] is None
    assert bars[1]["change_pct"] == pytest.approx((1318.49 / 1309.69 - 1) * 100)
    assert bars[2]["change_pct"] == pytest.approx((1336.66 / 1318.49 - 1) * 100)


def test_parse_eastmoney():
    name, bars = _parse_eastmoney(EASTMONEY_PAYLOAD)
    assert name == "贵州茅台"
    assert len(bars) == 2
    assert bars[1]["date"] == "2026-10-23"
    assert bars[1]["close"] == pytest.approx(1336.66)
    assert bars[1]["change_pct"] == pytest.approx(1.38)


def test_get_recent_daily_uses_primary(monkeypatch):
    em_called = []
    monkeypatch.setattr(market, "_fetch_tencent", lambda c, d, r: ("贵州茅台", make_bars([1, 2, 3])))
    monkeypatch.setattr(
        market,
        "_fetch_eastmoney",
        lambda c, d, r: em_called.append(1) or ("备用源", make_bars([9])),
    )
    name, bars = market.get_recent_daily("600519", days=2)
    assert name == "贵州茅台"
    assert [bar["close"] for bar in bars] == [2, 3]
    assert em_called == []


def test_get_recent_daily_falls_back(monkeypatch):
    def broken(code, days, retries):
        raise RuntimeError("boom")

    monkeypatch.setattr(market, "_fetch_tencent", broken)
    monkeypatch.setattr(market, "_fetch_eastmoney", lambda c, d, r: ("贵州茅台", make_bars([1, 2])))
    name, bars = market.get_recent_daily("600519", days=10)
    assert name == "贵州茅台"
    assert len(bars) == 2


def test_get_recent_daily_all_failed(monkeypatch):
    def broken(code, days, retries):
        raise RuntimeError("boom")

    monkeypatch.setattr(market, "_fetch_tencent", broken)
    monkeypatch.setattr(market, "_fetch_eastmoney", broken)
    with pytest.raises(RuntimeError):
        market.get_recent_daily("600519")


def test_get_recent_daily_invalid_code():
    with pytest.raises(ValueError):
        get_recent_daily("abc")
