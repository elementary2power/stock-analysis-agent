from main import format_bars


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
