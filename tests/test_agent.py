import pytest

from stock_analysis_agent.agent import StockAnalysisAgent
from stock_analysis_agent.data.market import _secid, normalize_symbol


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
    "raw,expected",
    [
        ("600519", "600519"),
        ("sh600519", "600519"),
        ("600519.SH", "600519"),
        (" sz000001 ", "000001"),
        ("SZ300750", "300750"),
    ],
)
def test_normalize_symbol(raw, expected):
    assert normalize_symbol(raw) == expected


@pytest.mark.parametrize("bad", ["", "abc", "60051", "1234567"])
def test_normalize_symbol_invalid(bad):
    with pytest.raises(ValueError):
        normalize_symbol(bad)


@pytest.mark.parametrize(
    "code,expected",
    [
        ("600519", "1.600519"),
        ("688981", "1.688981"),
        ("000001", "0.000001"),
        ("300750", "0.300750"),
    ],
)
def test_secid(code, expected):
    assert _secid(code) == expected


def test_analyze_with_data(monkeypatch):
    monkeypatch.setattr(
        "stock_analysis_agent.agent.get_recent_daily",
        lambda symbol, days=10: ("贵州茅台", make_bars([10, 11, 12, 13, 14])),
    )
    result = StockAnalysisAgent().analyze("600519")
    assert result["symbol"] == "600519"
    assert result["name"] == "贵州茅台"
    assert result["latest_price"] == 14
    assert result["sma_5"] == pytest.approx(12.0)


def test_analyze_without_data(monkeypatch):
    monkeypatch.setattr(
        "stock_analysis_agent.agent.get_recent_daily",
        lambda symbol, days=10: ("", []),
    )
    result = StockAnalysisAgent().analyze("600519")
    assert result["name"] == ""
    assert result["latest_price"] is None
    assert result["sma_5"] is None


def test_recent_daily_returns_name_and_bars(monkeypatch):
    def fake(symbol, days=10):
        return ("贵州茅台", make_bars([1, 2]))

    monkeypatch.setattr("stock_analysis_agent.agent.get_recent_daily", fake)
    name, bars = StockAnalysisAgent().recent_daily("sh600519", days=10)
    assert name == "贵州茅台"
    assert len(bars) == 2
    assert bars[0]["close"] == 1
