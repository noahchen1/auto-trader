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
        rebalance_days=20,
    ):
        self.price_history = price_history
        self.benchmark_history = benchmark_history
        self.starting_cash = starting_cash
        self.lookback_days = lookback_days
        self.rebalance_days = rebalance_days
        self.cash = starting_cash
        self.positions = {}
        self.trades = []
        self.equity_curve = []

    def run(self):
        dates = self._common_dates()

        for index, date in enumerate(dates):
            prices = self._prices_on(date)
            portfolio_value = self._portfolio_value(prices)

            self.equity_curve.append(
                {
                    "date": date,
                    "portfolio_value": portfolio_value,
                    "cash": self.cash,
                }
            )

            if index < self.lookback_days:
                continue

            if (index - self.lookback_days) % self.rebalance_days != 0:
                continue

            self._rebalance(date)

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

    def _rebalance(self, date):
        results = []
        benchmark_slice = self.benchmark_history.loc[:date].tail(self.lookback_days)
        market_regime = market_regime_score(benchmark_slice)

        for symbol, history in self.price_history.items():
            stock_slice = history.loc[:date].tail(self.lookback_days)

            if len(stock_slice) < self.lookback_days:
                continue

            results.append(score_stock(symbol, stock_slice, market_regime))

        signals = generate_signals(results, self.positions)

        self._process_sells(signals, date)
        self._process_buys(signals, date)

    def _process_sells(self, signals, date):
        for stock in signals:
            symbol = stock["symbol"]

            if stock["signal"] != "SELL" or symbol not in self.positions:
                continue

            position = self.positions.pop(symbol)
            value = position["shares"] * stock["price"]
            self.cash += value
            self.trades.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "side": "SELL",
                    "shares": position["shares"],
                    "price": stock["price"],
                    "value": value,
                    "score": stock["score"],
                }
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
                "score": stock["score"],
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
            if date not in history.index:
                continue

            prices[symbol] = float(history.loc[date, "Close"])

        return prices

    def _common_dates(self):
        if not self.price_history or self.benchmark_history.empty:
            return pd.DatetimeIndex([])

        indexes = [history.index for history in self.price_history.values()]
        indexes.append(self.benchmark_history.index)
        common = indexes[0]

        for index in indexes[1:]:
            common = common.intersection(index)

        return common.sort_values()
