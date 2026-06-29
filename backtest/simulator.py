import pandas as pd

from indicators.market import market_regime_score
from strategies.score_engine import score_stock
from strategies.signal_engine import generate_signals


class BacktestSimulator:

    def __init__(
        self,
        price_history,
        benchmark_history,
        starting_cash=100000,
        lookback_days=253,
        buy_check_days=5,
        sell_check_days=1,
        rebalance_days=None,
        start_date=None,
        end_date=None,
        stop_loss_pct=0.08,
        trailing_stop_pct=0.12,
    ):
        self.price_history = price_history
        self.benchmark_history = benchmark_history
        self.starting_cash = starting_cash
        self.lookback_days = lookback_days
        self.buy_check_days = rebalance_days or buy_check_days
        self.sell_check_days = rebalance_days or sell_check_days
        self.start_date = pd.Timestamp(start_date) if start_date else None
        self.end_date = pd.Timestamp(end_date) if end_date else None
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.cash = starting_cash
        self.positions = {}
        self.trades = []
        self.equity_curve = []

    def run(self):
        dates = self._trading_dates()

        for index, date in enumerate(dates):
            if index < self.lookback_days:
                continue

            if not self._in_backtest_range(date):
                continue

            prices = self._prices_on(date)
            self._process_stop_losses(date, prices)
            portfolio_value = self._portfolio_value(prices)

            self.equity_curve.append(
                {
                    "date": date,
                    "portfolio_value": portfolio_value,
                    "cash": self.cash,
                }
            )

            sell_check = self._should_check(index, self.sell_check_days)
            buy_check = self._should_check(index, self.buy_check_days)

            if not sell_check and not buy_check:
                continue

            self._evaluate_signals(date, sell_check, buy_check)

        return self.summary()

    def summary(self):
        equity = pd.DataFrame(self.equity_curve)

        if equity.empty:
            return {
                "starting_cash": self.starting_cash,
                "ending_value": self.cash,
                "total_return": 0.0,
                "trades": self.trades,
                "equity_curve": equity,
            }

        final_date = equity["date"].iloc[-1]
        ending_value = self._portfolio_value(self._prices_on(final_date))

        return {
            "starting_cash": self.starting_cash,
            "ending_value": ending_value,
            "total_return": ending_value / self.starting_cash - 1,
            "trades": self.trades,
            "equity_curve": equity,
        }

    def _evaluate_signals(self, date, sell_check, buy_check):
        results = []
        benchmark_slice = self.benchmark_history.loc[:date].tail(self.lookback_days)
        market_regime = market_regime_score(benchmark_slice)

        for symbol, history in self.price_history.items():
            stock_slice = history.loc[:date].tail(self.lookback_days)

            if len(stock_slice) < self.lookback_days:
                continue

            if stock_slice.index[-1] != date:
                continue

            results.append(score_stock(symbol, stock_slice, market_regime))

        signals = generate_signals(results, self.positions)

        if sell_check:
            self._process_sells(signals, date)

        if buy_check:
            self._process_buys(signals, date)

    def _should_check(self, index, check_days):
        return (index - self.lookback_days) % check_days == 0

    def _process_sells(self, signals, date):
        for stock in signals:
            symbol = stock["symbol"]

            if stock["signal"] != "SELL" or symbol not in self.positions:
                continue

            self._sell_position(
                symbol=symbol,
                date=date,
                price=stock["price"],
                score=stock["score"],
                rating=stock["rating"],
                reason="SIGNAL",
            )

    def _process_buys(self, signals, date):
        buys = [
            stock
            for stock in signals
            if stock["signal"] == "BUY"
            and stock["symbol"] not in self.positions
        ]

        open_slots = max(0, 5 - len(self.positions))
        buys = buys[:open_slots]

        if not buys or self.cash <= 0:
            return

        allocation = self.cash / len(buys)

        for stock in buys:
            shares = allocation / stock["price"]
            value = shares * stock["price"]

            self.positions[stock["symbol"]] = {
                "shares": shares,
                "entry_price": stock["price"],
                "entry_date": date,
                "highest_price": stock["price"],
                "score": stock["score"],
                "rating": stock["rating"],
            }
            self.cash -= value
            self.trades.append(
                {
                    "date": date,
                    "symbol": stock["symbol"],
                    "side": "BUY",
                    "shares": shares,
                    "price": stock["price"],
                    "value": value,
                    "score": stock["score"],
                    "rating": stock["rating"],
                    "reason": "ENTRY",
                    "pnl": None,
                    "pnl_pct": None,
                    "holding_days": None,
                }
            )

    def _process_stop_losses(self, date, prices):
        for symbol, position in list(self.positions.items()):
            price = prices.get(symbol)

            if price is None:
                continue

            position["highest_price"] = max(position["highest_price"], price)
            hard_stop_price = position["entry_price"] * (1 - self.stop_loss_pct)
            trailing_stop_price = position["highest_price"] * (
                1 - self.trailing_stop_pct
            )

            if self.stop_loss_pct > 0 and price <= hard_stop_price:
                self._sell_position(
                    symbol=symbol,
                    date=date,
                    price=price,
                    score=position["score"],
                    rating=position["rating"],
                    reason="HARD_STOP",
                )
                continue

            if self.trailing_stop_pct > 0 and price <= trailing_stop_price:
                self._sell_position(
                    symbol=symbol,
                    date=date,
                    price=price,
                    score=position["score"],
                    rating=position["rating"],
                    reason="TRAILING_STOP",
                )

    def _sell_position(self, symbol, date, price, score, rating, reason):
        position = self.positions.pop(symbol)
        value = position["shares"] * price
        cost_basis = position["shares"] * position["entry_price"]
        pnl = value - cost_basis
        holding_days = (date - position["entry_date"]).days
        self.cash += value
        self.trades.append(
            {
                "date": date,
                "symbol": symbol,
                "side": "SELL",
                "shares": position["shares"],
                "price": price,
                "value": value,
                "score": score,
                "rating": rating,
                "reason": reason,
                "entry_date": position["entry_date"],
                "entry_price": position["entry_price"],
                "cost_basis": cost_basis,
                "pnl": pnl,
                "pnl_pct": pnl / cost_basis if cost_basis else 0,
                "holding_days": holding_days,
            }
        )

    def _portfolio_value(self, prices):
        value = self.cash

        for symbol, position in self.positions.items():
            price = prices.get(symbol)

            if price is None:
                continue

            value += position["shares"] * price

        return value

    def _prices_on(self, date):
        prices = {}

        for symbol, history in self.price_history.items():
            price = self._price_on_or_before(history, date)

            if price is None:
                continue

            prices[symbol] = price

        return prices

    def _trading_dates(self):
        if self.benchmark_history.empty:
            return pd.DatetimeIndex([])

        return self.benchmark_history.index.sort_values()

    def _price_on_or_before(self, history, date):
        history = history.loc[:date]

        if history.empty:
            return None

        return float(history["Close"].iloc[-1])

    def _in_backtest_range(self, date):
        if self.start_date is not None and date < self.start_date:
            return False

        if self.end_date is not None and date > self.end_date:
            return False

        return True
