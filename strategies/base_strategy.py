from abc import ABC, abstractmethod
import queue
from engine.events import MarketEvent

class Strategy(ABC):
    """Abstract Base Class for quantitative trading strategies."""
    def __init__(self, events_queue: queue.Queue, data_handler):
        self.events = events_queue
        self.data_handler = data_handler

    @abstractmethod
    def calculate_signals(self, event: MarketEvent):
        """Calculates alpha signal based on latest bar and pushes SignalEvent to queue."""
        pass
