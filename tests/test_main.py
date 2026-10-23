from main import format_bars, format_prediction


def make_bar(**overrides):
    bar = {
        "date": "2026-10-23",
        "open": 10.0,
        "close": 10.5,
        "high": 11.0,
        "low": 9.5,
        "volume": 100,
        "change_pct": 1.23,
    }
    bar.update(overrides)
    return bar


def test_format_bars_contains_data():
    bars = [make_bar(), make_bar(date="2026-10-22", change_pct=-0.56)]
    text = format_bars("600519", "贵州茅台", bars)
    assert "600519 贵州茅台" in text
    assert "最近 2 个交易日" in text
    assert "2026-10-23" in text
    assert "2026-10-22" in text
    assert "+1.23%" in text
    assert "-0.56%" in text


def test_format_bars_handles_missing_change_pct():
    text = format_bars("600519", "贵州茅台", [make_bar(change_pct=None)])
    assert "—" in text


def test_format_prediction():
    prediction = {
        "direction": "看涨",
        "score": 6.0,
        "confidence": 60.0,
        "reasons": ["5日均线高于10日均线", "放量上涨"],
    }
    text = format_prediction(prediction)
    assert "看涨" in text
    assert "6/10" in text
    assert "60%" in text
    assert "5日均线高于10日均线" in text
    assert "不构成投资建议" in text


def test_format_prediction_no_reasons():
    prediction = {"direction": "震荡", "score": 0.0, "confidence": 0.0, "reasons": []}
    text = format_prediction(prediction)
    assert "震荡" in text
    assert "多空信号不明显" in text
