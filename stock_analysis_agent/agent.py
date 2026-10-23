from stock_analysis_agent import config
from stock_analysis_agent.analysis.indicators import sma
from stock_analysis_agent.analysis.trend import predict_trend
from stock_analysis_agent.data.market import get_recent_daily, normalize_symbol


class StockAnalysisAgent:
    """股票分析智能体。"""

    def __init__(self, name: str = "stock-analysis-agent"):
        self.name = name
        self.data_source = config.DATA_SOURCE

    def recent_daily(self, symbol: str, days: int = 10) -> tuple[str, list[dict]]:
        """最近 N 个交易日的日线行情，返回 (股票名称, 行情列表)。"""
        return get_recent_daily(symbol, days=days)

    def predict_trend(self, symbol: str, days: int = 10) -> dict:
        """基于最近 N 个交易日的行情，预测次日趋势。"""
        _, bars = get_recent_daily(symbol, days=days)
        return predict_trend(bars)

    def analyze(self, symbol: str) -> dict:
        """对指定股票执行分析，返回分析结果。"""
        stock_name, bars = get_recent_daily(symbol)
        closes = [bar["close"] for bar in bars]
        return {
            "symbol": normalize_symbol(symbol),
            "name": stock_name,
            "data_source": self.data_source,
            "latest_price": closes[-1] if closes else None,
            "sma_5": sma(closes, 5),
        }
