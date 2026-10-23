import pytest

from stock_analysis_agent.analysis.trend import _slope_pct, predict_trend


def make_bars(closes, volumes=None):
    volumes = volumes or [1000] * len(closes)
    return [
        {
            "date": f"2026-10-{9 + i:02d}",
            "open": close - 0.5,
            "close": close,
            "high": close + 1,
            "low": close - 1,
            "volume": volume,
            "change_pct": 1.0,
        }
        for i, (close, volume) in enumerate(zip(closes, volumes))
    ]


def test_slope_pct():
    assert _slope_pct([100, 101, 102]) == pytest.approx(1 / 101 * 100)
    assert _slope_pct([100.0]) == 0.0
    assert _slope_pct([102, 101, 100]) == pytest.approx(-1 / 101 * 100)


def test_predict_uptrend():
    closes = [100 + i for i in range(10)]
    volumes = [100 + 10 * i for i in range(10)]
    result = predict_trend(make_bars(closes, volumes))
    assert result["direction"] == "看涨"
    assert result["score"] >= 3
    assert result["confidence"] > 0
    assert result["reasons"]


def test_predict_downtrend():
    closes = [110 - i for i in range(10)]
    volumes = [190 - 10 * i for i in range(10)]
    result = predict_trend(make_bars(closes, volumes))
    assert result["direction"] == "看跌"
    assert result["score"] <= -3


def test_predict_flat():
    result = predict_trend(make_bars([100.0] * 10))
    assert result["direction"] == "震荡"
    assert result["score"] == 0
    assert result["confidence"] == 0
    assert result["reasons"] == []


def test_predict_insufficient_data():
    result = predict_trend(make_bars([100.0, 101.0]))
    assert result["direction"] == "数据不足"
    assert result["confidence"] == 0


def test_predict_empty():
    result = predict_trend([])
    assert result["direction"] == "数据不足"
