import queue
from engine.events import OrderEvent, FillEvent

class SimulatedExecutionHandler:
    """
    Simulates order execution with realistic slippage (bps) and broker commissions.
    """
    def __init__(self, events_queue: queue.Queue, data_handler, slippage_bps: float = 2.0, commission_per_share: float = 0.005):
        self.events = events_queue
        self.data_handler = data_handler
        self.slippage_bps = slippage_bps
        self.commission_per_share = commission_per_share

    def execute_order(self, order: OrderEvent):
        latest_bar = self.data_handler.get_latest_bar(order.symbol)
        if not latest_bar:
            return

        base_price = latest_bar.close
        # Slippage penalty: buyers pay slightly more, sellers receive slightly less
        slip_pct = (self.slippage_bps / 10000.0)
        if order.direction == 'BUY':
            fill_price = base_price * (1.0 + slip_pct)
        else:
            fill_price = base_price * (1.0 - slip_pct)

        commission = max(1.0, order.quantity * self.commission_per_share)
        slippage_cost = abs(fill_price - base_price) * order.quantity

        fill = FillEvent(
            timestamp=latest_bar.timestamp,
            symbol=order.symbol,
            exchange="SIMULATED",
            quantity=order.quantity,
            direction=order.direction,
            fill_price=round(fill_price, 4),
            commission=round(commission, 2),
            slippage=round(slippage_cost, 2)
        )
        self.events.put(fill)
