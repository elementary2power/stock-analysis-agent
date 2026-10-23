# stock-analysis-agent

股票分析智能体。

## 项目结构

```
stock-analysis-agent/
├── main.py                     # 程序入口
├── requirements.txt            # 运行依赖
├── requirements-dev.txt        # 开发依赖（含测试）
├── stock_analysis_agent/       # 源码包
│   ├── agent.py                # Agent 核心逻辑
│   ├── config.py               # 配置（从环境变量读取）
│   ├── data/                   # 行情数据获取
│   └── analysis/               # 指标与分析
└── tests/                      # 单元测试
```

## 功能

- 输入 A 股代码，展示最近 10 个交易日行情（前复权，数据源：东方财富公开行情接口）
- 支持的代码格式：`600519` / `sh600519` / `600519.SH` 等

## 快速开始

```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python main.py
```

## 运行测试

```powershell
.venv\Scripts\python -m pytest
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `STOCK_DATA_SOURCE` | 数据源名称，默认 `eastmoney` |
| `STOCK_API_KEY` | 数据源 API Key（接入真实数据源时使用） |
