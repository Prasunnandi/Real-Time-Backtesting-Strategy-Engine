import collections
import math
import queue
from strategies.base_strategy import Strategy
from engine.events import MarketEvent, SignalEvent

class BollingerMeanReversionStrategy(Strategy):
    """
    Mean-Reversion Quantitative Alpha Strategy using Bollinger Bands.
    Enters LONG when price dips > 2 standard deviations below SMA-20.
    Exits when price reverts back to the rolling mean.
    """
    def __init__(self, events_queue: queue.Queue, data_handler, window: int = 20, num_std: float = 2.0):
        super().__init__(events_queue, data_handler)
        self.window = window
        self.num_std = num_std
        self.price_history = collections.defaultdict(lambda: collections.deque(maxlen=window))
        self.in_position = collections.defaultdict(bool)

    def calculate_signals(self, event: MarketEvent):
        prices = self.price_history[event.symbol]
        prices.append(event.close)

        if len(prices) < self.window:
            return

        sma = sum(prices) / self.window
        variance = sum((p - sma) ** 2 for p in prices) / self.window
        std = math.sqrt(variance) if variance > 0 else 1e-6

        lower_band = sma - (self.num_std * std)
        upper_band = sma + (self.num_std * std)
        z_score = (event.close - sma) / std

        # Long Entry on oversold extreme
        if not self.in_position[event.symbol] and event.close <= lower_band:
            signal = SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type='LONG',
                strength=min(1.5, max(0.8, abs(z_score) / 2.0)),
                strategy_id="BOLLINGER_REVERSION"
            )
            self.events.put(signal)
            self.in_position[event.symbol] = True

        # Exit on mean reversion crossing above SMA
        elif self.in_position[event.symbol] and event.close >= sma:
            signal = SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type='EXIT',
                strength=1.0,
                strategy_id="BOLLINGER_REVERSION"
            )
            self.events.put(signal)
            self.in_position[event.symbol] = False
