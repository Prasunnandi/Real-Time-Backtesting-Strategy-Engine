import collections
import queue
from strategies.base_strategy import Strategy
from engine.events import MarketEvent, SignalEvent

class DualMomentumStrategy(Strategy):
    """
    Momentum Trend-Following Strategy using Fast & Slow Exponential Moving Averages (EMA).
    Enters LONG when Fast EMA crosses above Slow EMA.
    Exits when Fast EMA crosses below Slow EMA.
    """
    def __init__(self, events_queue: queue.Queue, data_handler, fast_period: int = 12, slow_period: int = 26):
        super().__init__(events_queue, data_handler)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.fast_alpha = 2.0 / (fast_period + 1)
        self.slow_alpha = 2.0 / (slow_period + 1)

        self.fast_ema = {}
        self.slow_ema = {}
        self.in_position = collections.defaultdict(bool)

    def calculate_signals(self, event: MarketEvent):
        symbol = event.symbol
        close = event.close

        if symbol not in self.fast_ema:
            self.fast_ema[symbol] = close
            self.slow_ema[symbol] = close
            return

        prev_fast = self.fast_ema[symbol]
        prev_slow = self.slow_ema[symbol]

        # Update EMAs
        self.fast_ema[symbol] = (close * self.fast_alpha) + (prev_fast * (1.0 - self.fast_alpha))
        self.slow_ema[symbol] = (close * self.slow_alpha) + (prev_slow * (1.0 - self.slow_alpha))

        # Golden Cross: Fast EMA crosses above Slow EMA
        if not self.in_position[symbol] and prev_fast <= prev_slow and self.fast_ema[symbol] > self.slow_ema[symbol]:
            signal = SignalEvent(
                symbol=symbol,
                timestamp=event.timestamp,
                signal_type='LONG',
                strength=1.0,
                strategy_id="DUAL_MOMENTUM"
            )
            self.events.put(signal)
            self.in_position[symbol] = True

        # Death Cross: Fast EMA crosses below Slow EMA
        elif self.in_position[symbol] and prev_fast >= prev_slow and self.fast_ema[symbol] < self.slow_ema[symbol]:
            signal = SignalEvent(
                symbol=symbol,
                timestamp=event.timestamp,
                signal_type='EXIT',
                strength=1.0,
                strategy_id="DUAL_MOMENTUM"
            )
            self.events.put(signal)
            self.in_position[symbol] = False
