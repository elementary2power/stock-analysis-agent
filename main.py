from stock_analysis_agent import __version__
from stock_analysis_agent.analysis.trend import predict_trend
from stock_analysis_agent.agent import StockAnalysisAgent
from stock_analysis_agent.data.market import normalize_symbol


def _display_width(text: str) -> int:
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def format_bars(symbol: str, name: str, bars: list[dict]) -> str:
    """将行情列表格式化为对齐的文本表格（兼容中文列宽）。"""
    title = f"{symbol} {name}".rstrip() + f" 最近 {len(bars)} 个交易日行情（前复权）"
    header = (
        _pad("日期", 13)
        + _pad("开盘", 11)
        + _pad("收盘", 11)
        + _pad("最高", 11)
        + _pad("最低", 11)
        + "涨跌幅"
    )
    lines = [title, header]
    for bar in bars:
        change = "—" if bar["change_pct"] is None else f"{bar['change_pct']:+.2f}%"
        lines.append(
            _pad(bar["date"], 13)
            + _pad(f"{bar['open']:.2f}", 11)
            + _pad(f"{bar['close']:.2f}", 11)
            + _pad(f"{bar['high']:.2f}", 11)
            + _pad(f"{bar['low']:.2f}", 11)
            + change
        )
    return "\n".join(lines)


def format_prediction(prediction: dict) -> str:
    """将次日趋势预测结果格式化为文本。"""
    lines = [
        "—— 明日趋势预测 ——",
        f"方向: {prediction['direction']}（综合得分 {prediction['score']:.0f}/10，置信度 {prediction['confidence']:.0f}%）",
    ]
    reasons = prediction["reasons"]
    lines.extend(f"  · {reason}" for reason in reasons)
    if not reasons:
        lines.append("  · 多空信号不明显")
    lines.append("注: 基于简单技术指标打分模型，仅供参考，不构成投资建议")
    return "\n".join(lines)


def main():
    print(f"stock-analysis-agent v{__version__}")
    symbol = input("请输入股票代码（如 600519，回车退出）: ").strip()
    if not symbol:
        return
    try:
        code = normalize_symbol(symbol)
    except ValueError as exc:
        print(f"输入错误: {exc}")
        return
    agent = StockAnalysisAgent()
    try:
        stock_name, bars = agent.recent_daily(code, days=10)
    except Exception as exc:
        print(f"获取行情失败: {exc}")
        return
    if not bars:
        print("未查询到行情数据，请确认股票代码是否正确")
        return
    print(format_bars(code, stock_name, bars))
    print(format_prediction(predict_trend(bars)))


if __name__ == "__main__":
    main()
