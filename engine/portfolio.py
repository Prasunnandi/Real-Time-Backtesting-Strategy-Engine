import queue
from typing import Dict, List
from engine.events import SignalEvent, OrderEvent, FillEvent, MarketEvent

class Portfolio:
    """
    Manages positions, cash balance, margin, and order sizing.
    Tracks mark-to-market equity curve without look-ahead bias.
    """
    def __init__(self, events_queue: queue.Queue, data_handler, initial_capital: float = 100_000.0, position_size_pct: float = 0.20):
        self.events = events_queue
        self.data_handler = data_handler
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.position_size_pct = position_size_pct

        self.current_positions: Dict[str, int] = {}
        self.cost_basis: Dict[str, float] = {}
        self.realized_pnl = 0.0
        self.total_commission_paid = 0.0
        self.total_slippage_paid = 0.0

        # Equity curve timeline: [{"timestamp": t, "equity": eq, "cash": c, "drawdown": dd}]
        self.equity_curve: List[Dict] = []
        self.peak_equity = initial_capital
        self.trade_history: List[Dict] = []

    def update_market_equity(self, market_event: MarketEvent):
        """Calculates total portfolio mark-to-market value based on closing prices."""
        market_val = 0.0
        for symbol, qty in self.current_positions.items():
            bar = self.data_handler.get_latest_bar(symbol)
            if bar:
                market_val += qty * bar.close

        total_equity = self.current_cash + market_val
        self.peak_equity = max(self.peak_equity, total_equity)
        drawdown_pct = (self.peak_equity - total_equity) / self.peak_equity if self.peak_equity > 0 else 0.0

        self.equity_curve.append({
            "timestamp": market_event.timestamp,
            "equity": round(total_equity, 2),
            "cash": round(self.current_cash, 2),
            "holdings_val": round(market_val, 2),
            "drawdown_pct": round(drawdown_pct * 100.0, 3)
        })

    def handle_signal(self, signal: SignalEvent):
        """Converts Alpha signals into risk-sized Order events."""
        latest_bar = self.data_handler.get_latest_bar(signal.symbol)
        if not latest_bar:
            return

        current_qty = self.current_positions.get(signal.symbol, 0)
        price = latest_bar.close

        if signal.signal_type == 'LONG' and current_qty == 0:
            # Sizing: allocate target percentage of portfolio equity
            target_alloc = (self.current_cash * self.position_size_pct) * signal.strength
            target_shares = int(target_alloc / price)
            if target_shares > 0 and (target_shares * price) <= self.current_cash:
                order = OrderEvent(
                    symbol=signal.symbol,
                    order_type='MKT',
                    quantity=target_shares,
                    direction='BUY'
                )
                self.events.put(order)

        elif signal.signal_type == 'EXIT' and current_qty > 0:
            order = OrderEvent(
                symbol=signal.symbol,
                order_type='MKT',
                quantity=current_qty,
                direction='SELL'
            )
            self.events.put(order)

    def handle_fill(self, fill: FillEvent):
        """Updates internal ledger and cash upon trade execution fill."""
        current_qty = self.current_positions.get(fill.symbol, 0)
        self.total_commission_paid += fill.commission
        self.total_slippage_paid += fill.slippage

        if fill.direction == 'BUY':
            cost = (fill.quantity * fill.fill_price) + fill.commission
            self.current_cash -= cost
            self.current_positions[fill.symbol] = current_qty + fill.quantity
            self.cost_basis[fill.symbol] = fill.fill_price

            self.trade_history.append({
                "timestamp": fill.timestamp,
                "symbol": fill.symbol,
                "action": "BUY",
                "shares": fill.quantity,
                "price": fill.fill_price,
                "commission": fill.commission,
                "pnl": 0.0
            })

        elif fill.direction == 'SELL':
            proceeds = (fill.quantity * fill.fill_price) - fill.commission
            self.current_cash += proceeds
            avg_entry = self.cost_basis.get(fill.symbol, fill.fill_price)
            trade_pnl = (fill.fill_price - avg_entry) * fill.quantity - fill.commission
            self.realized_pnl += trade_pnl

            self.current_positions[fill.symbol] = current_qty - fill.quantity
            if self.current_positions[fill.symbol] == 0:
                del self.cost_basis[fill.symbol]

            self.trade_history.append({
                "timestamp": fill.timestamp,
                "symbol": fill.symbol,
                "action": "SELL",
                "shares": fill.quantity,
                "price": fill.fill_price,
                "commission": fill.commission,
                "pnl": round(trade_pnl, 2)
            })
