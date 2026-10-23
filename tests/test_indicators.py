import pytest

from stock_analysis_agent.analysis.indicators import sma


def test_sma_basic():
    assert sma([1, 2, 3, 4, 5], 3) == pytest.approx(4.0)


def test_sma_single_window():
    assert sma([2.5], 1) == pytest.approx(2.5)


def test_sma_not_enough_data():
    assert sma([1, 2], 3) is None


def test_sma_invalid_window():
    assert sma([1, 2, 3], 0) is None
