#!/usr/bin/env python3
"""
Real-Time Event-Driven Quantitative Backtesting Engine
Executes discrete event loop over streaming market data, portfolio risk sizing, and order fills.
"""

import queue
import argparse
import json
from engine.data_handler import HistoricCSVDataHandler
from engine.portfolio import Portfolio
from engine.execution import SimulatedExecutionHandler
from strategies.mean_reversion import BollingerMeanReversionStrategy
from strategies.momentum_trend import DualMomentumStrategy
from analytics.performance import PerformanceAnalytics

def run_backtest(strategy_name: str = "bollinger", initial_capital: float = 100_000.0):
    print("=" * 65)
    print("  QUANTITATIVE EVENT-DRIVEN STRATEGY BACKTESTING ENGINE")
    print(f"  Strategy: {strategy_name.upper()} | Initial Capital: ${initial_capital:,.2f}")
    print("=" * 65)

    events = queue.Queue()
    symbols = ["SPY", "AAPL"]
    data_handler = HistoricCSVDataHandler(events, "data", symbols)
    portfolio = Portfolio(events, data_handler, initial_capital=initial_capital, position_size_pct=0.40)
    execution_handler = SimulatedExecutionHandler(events, data_handler, slippage_bps=2.5, commission_per_share=0.005)

    if strategy_name.lower() == "bollinger":
        strategy = BollingerMeanReversionStrategy(events, data_handler, window=15, num_std=1.8)
    else:
        strategy = DualMomentumStrategy(events, data_handler, fast_period=10, slow_period=25)

    bar_count = 0
    while data_handler.continue_backtest:
        data_handler.update_bars()
        bar_count += 1

        while not events.empty():
            event = events.get()

            if event.__class__.__name__ == "MarketEvent":
                portfolio.update_market_equity(event)
                strategy.calculate_signals(event)

            elif event.__class__.__name__ == "SignalEvent":
                portfolio.handle_signal(event)

            elif event.__class__.__name__ == "OrderEvent":
                execution_handler.execute_order(event)

            elif event.__class__.__name__ == "FillEvent":
                portfolio.handle_fill(event)

    # Compute Tear Sheet Analytics
    metrics = PerformanceAnalytics.calculate_tear_sheet(
        portfolio.equity_curve,
        portfolio.trade_history,
        initial_capital=initial_capital
    )

    print("\n================ INSTITUTIONAL PERFORMANCE TEAR SHEET ================")
    print(f" Initial Portfolio Capital : ${metrics.get('initial_capital', 0):,.2f}")
    print(f" Final Portfolio Equity    : ${metrics.get('final_equity', 0):,.2f}")
    print(f" Total Cumulative Return   : {metrics.get('total_return_pct', 0):+.2f}%")
    print(f" Annualized Volatility     : {metrics.get('annualized_volatility_pct', 0):.2f}%")
    print(f" Sharpe Ratio (Rf = 4.0%)  : {metrics.get('sharpe_ratio', 0):.3f}")
    print(f" Sortino Ratio             : {metrics.get('sortino_ratio', 0):.3f}")
    print(f" Calmar Ratio              : {metrics.get('calmar_ratio', 0):.3f}")
    print(f" Max Drawdown (Peak-Trough): -{metrics.get('max_drawdown_pct', 0):.2f}%")
    print("----------------------------------------------------------------------")
    print(f" Total Trades Executed     : {metrics.get('total_trades', 0)}")
    print(f" Winning Trades / Losing   : {metrics.get('winning_trades', 0)} / {metrics.get('losing_trades', 0)}")
    print(f" Win Rate                  : {metrics.get('win_rate_pct', 0):.2f}%")
    print(f" Profit Factor             : {metrics.get('profit_factor', 0):.2f}")
    print(f" Brokerage Commissions     : ${metrics.get('total_commissions', 0):,.2f}")
    print("======================================================================\n")

    # Export latest equity curve for web visualization
    with open("web/equity_data.json", "w", encoding="utf-8") as f:
        json.dump({
            "metrics": metrics,
            "equity_curve": portfolio.equity_curve[-60:],
            "trades": portfolio.trade_history
        }, f, indent=2)

    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=["bollinger", "momentum"], default="bollinger")
    args = parser.parse_args()
    run_backtest(args.strategy)
