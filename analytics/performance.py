import math
from typing import List, Dict

class PerformanceAnalytics:
    """
    Computes institutional quantitative tear sheet metrics for backtest performance.
    """
    @staticmethod
    def calculate_tear_sheet(equity_curve: List[Dict], trade_history: List[Dict], initial_capital: float = 100_000.0, risk_free_rate: float = 0.04) -> Dict:
        if not equity_curve:
            return {}

        equities = [p["equity"] for p in equity_curve]
        final_equity = equities[-1]
        total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0

        # Daily period returns
        returns = []
        for i in range(1, len(equities)):
            r = (equities[i] - equities[i-1]) / equities[i-1]
            returns.append(r)

        n = len(returns)
        if n == 0:
            return {}

        avg_return = sum(returns) / n
        variance = sum((r - avg_return) ** 2 for r in returns) / n
        daily_vol = math.sqrt(variance) if variance > 0 else 1e-6
        annual_vol = daily_vol * math.sqrt(252)

        # Sharpe Ratio (annualized)
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
        excess_returns = [r - daily_rf for r in returns]
        avg_excess = sum(excess_returns) / n
        sharpe = (avg_excess / daily_vol) * math.sqrt(252) if daily_vol > 0 else 0.0

        # Downside Deviation for Sortino
        downside_returns = [r for r in excess_returns if r < 0]
        downside_var = sum(r ** 2 for r in downside_returns) / n if downside_returns else 1e-6
        downside_vol = math.sqrt(downside_var)
        sortino = (avg_excess / downside_vol) * math.sqrt(252) if downside_vol > 0 else 0.0

        # Maximum Drawdown calculation
        peak = equities[0]
        max_dd = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd

        max_drawdown_pct = max_dd * 100.0
        calmar = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0

        # Trade metrics
        sell_trades = [t for t in trade_history if t["action"] == "SELL"]
        winning_trades = [t for t in sell_trades if t["pnl"] > 0]
        losing_trades = [t for t in sell_trades if t["pnl"] < 0]

        total_trades = len(sell_trades)
        win_rate_pct = (len(winning_trades) / total_trades * 100.0) if total_trades > 0 else 0.0

        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        total_commissions = sum(t["commission"] for t in trade_history)

        return {
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annualized_volatility_pct": round(annual_vol * 100.0, 2),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "calmar_ratio": round(calmar, 3),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_pct": round(win_rate_pct, 2),
            "profit_factor": round(profit_factor, 2),
            "total_commissions": round(total_commissions, 2)
        }
