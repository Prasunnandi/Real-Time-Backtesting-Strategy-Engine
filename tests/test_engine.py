import unittest
import queue
from engine.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from engine.portfolio import Portfolio
from engine.execution import SimulatedExecutionHandler
from analytics.performance import PerformanceAnalytics

class MockDataHandler:
    def __init__(self, current_bar):
        self.bar = current_bar

    def get_latest_bar(self, symbol):
        return self.bar

class TestBacktestingEngine(unittest.TestCase):
    def test_events_instantiation(self):
        m = MarketEvent("AAPL", "2023-01-03", 130.0, 132.0, 129.0, 131.0, 100000)
        self.assertEqual(m.symbol, "AAPL")
        self.assertEqual(m.close, 131.0)

    def test_portfolio_signal_to_order(self):
        events = queue.Queue()
        mock_bar = MarketEvent("SPY", "2023-01-03", 400.0, 405.0, 399.0, 400.0, 50000)
        mock_data = MockDataHandler(mock_bar)

        portfolio = Portfolio(events, mock_data, initial_capital=100_000.0, position_size_pct=0.20)
        sig = SignalEvent("SPY", "2023-01-03", "LONG", 1.0)
        portfolio.handle_signal(sig)

        self.assertFalse(events.empty())
        order = events.get()
        self.assertEqual(order.symbol, "SPY")
        self.assertEqual(order.direction, "BUY")
        self.assertEqual(order.quantity, 50)  # $20,000 / $400 = 50 shares

    def test_execution_slippage_and_fill(self):
        events = queue.Queue()
        mock_bar = MarketEvent("SPY", "2023-01-03", 400.0, 405.0, 399.0, 400.0, 50000)
        mock_data = MockDataHandler(mock_bar)

        exec_handler = SimulatedExecutionHandler(events, mock_data, slippage_bps=10.0, commission_per_share=0.01)
        order = OrderEvent("SPY", "MKT", 100, "BUY")
        exec_handler.execute_order(order)

        self.assertFalse(events.empty())
        fill = events.get()
        self.assertEqual(fill.symbol, "SPY")
        self.assertGreater(fill.fill_price, 400.0)  # Buy order incurs upward slippage
        self.assertEqual(fill.commission, 1.0)     # 100 * 0.01 = 1.00

    def test_tear_sheet_math(self):
        curve = [
            {"equity": 100000.0},
            {"equity": 102000.0},
            {"equity": 101000.0},
            {"equity": 105000.0}
        ]
        trades = [
            {"action": "SELL", "pnl": 2000.0, "commission": 2.0},
            {"action": "SELL", "pnl": -1000.0, "commission": 2.0},
            {"action": "SELL", "pnl": 4000.0, "commission": 2.0}
        ]
        metrics = PerformanceAnalytics.calculate_tear_sheet(curve, trades, initial_capital=100000.0)
        self.assertEqual(metrics["total_return_pct"], 5.0)
        self.assertEqual(metrics["total_trades"], 3)
        self.assertEqual(metrics["winning_trades"], 2)
        self.assertAlmostEqual(metrics["win_rate_pct"], 66.67, places=1)

if __name__ == "__main__":
    unittest.main()
