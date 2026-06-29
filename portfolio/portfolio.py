class Portfolio:

    def __init__(self, starting_cash):

        self.cash = starting_cash
        self.positions = {}

    def rebalance(self, signals):
        for stock in signals:
            symbol = stock["symbol"]

            if stock["signal"] != "SELL" or symbol not in self.positions:
                continue

            position = self.positions.pop(symbol)
            self.cash += position["shares"] * stock["price"]

        buys = [
            s
            for s in signals
            if s["signal"] == "BUY"
            and s["symbol"] not in self.positions
        ]

        if not buys:
            print("\nNo new BUY signals passed the risk filters.")
            return

        allocation = self.cash / len(buys)

        for stock in buys:

            shares = allocation / stock["price"]

            self.positions[stock["symbol"]] = {
                "shares": shares,
                "price": stock["price"],
                "score": stock["score"]
            }

            self.cash -= shares * stock["price"]

    def print_summary(self):

        print("\nPortfolio\n")

        if not self.positions:
            print("No open positions.")

        for symbol, position in self.positions.items():

            print(
                f"{symbol:6}"
                f"{position['shares']:.2f} shares "
                f"@ ${position['price']:.2f}"
            )

        print(f"\nCash: ${self.cash:.2f}")
