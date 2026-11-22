import csv
import queue
from typing import Dict, List, Optional
from engine.events import MarketEvent

class HistoricCSVDataHandler:
    """
    Streams historical bar data from CSV files bar-by-bar to eliminate look-ahead bias.
    """
    def __init__(self, events_queue: queue.Queue, csv_dir: str, symbol_list: List[str]):
        self.events = events_queue
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.symbol_data: Dict[str, List[MarketEvent]] = {}
        self.symbol_idx: Dict[str, int] = {}
        self.latest_bar: Dict[str, Optional[MarketEvent]] = {s: None for s in symbol_list}
        self.continue_backtest = True
        self._load_csv_data()

    def _load_csv_data(self):
        for symbol in self.symbol_list:
            filepath = f"{self.csv_dir}/{symbol}.csv"
            events = []
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    events.append(MarketEvent(
                        symbol=symbol,
                        timestamp=row["timestamp"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"])
                    ))
            self.symbol_data[symbol] = events
            self.symbol_idx[symbol] = 0

    def get_latest_bar(self, symbol: str) -> Optional[MarketEvent]:
        return self.latest_bar.get(symbol)

    def update_bars(self):
        """Pushes the next bar for each symbol into the event queue."""
        has_more = False
        for symbol in self.symbol_list:
            idx = self.symbol_idx[symbol]
            if idx < len(self.symbol_data[symbol]):
                bar = self.symbol_data[symbol][idx]
                self.latest_bar[symbol] = bar
                self.symbol_idx[symbol] += 1
                self.events.put(bar)
                has_more = True
        
        if not has_more:
            self.continue_backtest = False
