# Event-Driven Quantitative Strategy & Real-Time Backtesting Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Type](https://img.shields.io/badge/Architecture-Event--Driven-purple.svg)]()
[![Institutional](https://img.shields.io/badge/Metrics-Sharpe%20%7C%20Sortino%20%7C%20Calmar-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Unit%20Tests-100%25%20Passed-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

An institutional-grade, event-driven quantitative backtesting and execution engine designed in Python. Unlike vector-based backtesters that suffer from subtle look-ahead bias and unrealistic instant executions, this engine operates on a discrete event queue (`MarketEvent` ➔ `SignalEvent` ➔ `OrderEvent` ➔ `FillEvent`), realistically simulating bid-ask spreads, order slippage, variable brokerage commissions, and portfolio margin accounting.

---

## 🏛️ Event-Driven Architecture

```
                       STREAMING HISTORICAL OHLCV / L2 FEED
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │          MarketEvent          │
                       │   (Bar timestamp, O-H-L-C-V)  │
                       └───────────────┬───────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
     ┌─────────────────────────────┐       ┌─────────────────────────────┐
     │      Alpha Strategy         │       │     Portfolio Risk Engine   │
     │   (Bollinger / Dual EMA)    │       │   (Mark-to-Market Equity)   │
     └──────────────┬──────────────┘       └─────────────────────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │         SignalEvent         │
     │     (LONG, SHORT, EXIT)     │
     └──────────────┬──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │     Portfolio Sizing        │
     │ (Cash & Target Allocation)  │
     └──────────────┬──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │          OrderEvent         │
     │      (BUY/SELL Shares)      │
     └──────────────┬──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │  Simulated Execution Broker │
     │  (Slippage Bps + Commission)│
     └──────────────┬──────────────┘
                    │
                    ▼
     ┌─────────────────────────────┐
     │          FillEvent          │
     │  (Ledger & Cash Settlement) │
     └─────────────────────────────┘
```

---

## ⚡ Core Engine Features

1. **Zero Look-Ahead Bias:**
   - Market data is streamed sequentially bar-by-bar; strategies can only inspect historical bars up to the current bar's timestamp.
2. **Realistic Slippage & Execution Penalties:**
   - Execution fills simulate market impact and bid-ask crossing penalty (configurable basis points per trade).
3. **Institutional Commission Modeling:**
   - Interactive Brokers tiered structure ($0.005/share, with $1.00 minimum ticket fee).
4. **Complete Quantitative Analytics:**
   - **Sharpe Ratio** (annualized over risk-free benchmark $R_f = 4.0\%$).
   - **Sortino Ratio** (downside risk deviation penalization).
   - **Calmar Ratio** (CAGR to Maximum Peak-to-Trough Drawdown).
   - **Win Rate & Profit Factor** (gross profits vs gross losses).

---

## 📊 Benchmark Strategy Results

Benchmarked on daily SPY and AAPL historical bars:

| Strategy | Cumulative Return | Win Rate | Profit Factor | Max Drawdown | Sharpe Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bollinger Mean Reversion** | **+6.12%** | **87.50%** | **3.59** | **-4.32%** | **+0.074** |
| **Dual Momentum (EMA-10/25)** | **+0.00%** | **50.00%** | **1.00** | **-6.94%** | **-0.657** |

---

## 🚀 Quickstart

### 1. Run Strategy Backtests
```bash
# Run Bollinger Bands Mean Reversion Strategy
python main.py --strategy bollinger

# Run Dual EMA Trend Momentum Strategy
python main.py --strategy momentum
```

### 2. Run Test Suite
```bash
python -m unittest tests/test_engine.py
```

### 3. Open Interactive Dashboard
Open `web/index.html` in your web browser to explore interactive equity curves, drawdowns, and trade fill audit logs.

---

## 📁 Repository Directory Structure

```
├── analytics/
│   └── performance.py           # Sharpe, Sortino, Calmar, Max Drawdown
├── data/
│   ├── AAPL.csv                 # Daily historical OHLCV dataset
│   └── SPY.csv                  # S&P 500 ETF historical OHLCV dataset
├── engine/
│   ├── data_handler.py          # Sequential bar streaming
│   ├── events.py                # Discrete event definitions
│   ├── execution.py             # Broker slippage & commission simulation
│   └── portfolio.py             # Position ledger & order sizing
├── strategies/
│   ├── base_strategy.py         # Abstract Strategy base class
│   ├── mean_reversion.py        # Bollinger Bands mean reversion
│   └── momentum_trend.py        # Dual EMA trend crossover
├── tests/
│   └── test_engine.py           # Unit tests
├── web/
│   ├── equity_data.json         # Exported backtest trajectory
│   └── index.html               # Interactive visual analytics dashboard
├── main.py                      # Main backtest runner
└── README.md                    # Technical documentation
```

---

## 📜 License
MIT License. Created by [Prasun Nandi](https://github.com/Prasunnandi).
