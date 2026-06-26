class Portfolio:

    def __init__(self, starting_cash):

        self.cash = starting_cash
        self.positions = {}

    def rebalance(self, signals):

        buys = [
            s
            for s in signals
            if s["signal"] == "BUY"
        ]

        allocation = self.cash / len(buys)

        for stock in buys:

            shares = allocation / stock["price"]

            self.positions[stock["symbol"]] = {
                "shares": shares,
                "price": stock["price"],
                "score": stock["score"]
            }

    def print_summary(self):

        print("\nPortfolio\n")

        for symbol, position in self.positions.items():

            print(
                f"{symbol:6}"
                f"{position['shares']:.2f} shares "
                f"@ ${position['price']:.2f}"
            )