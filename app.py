from datetime import datetime
from data.market_data import MarketDataService
from strategies.score_engine import score_stock
from portfolio.portfolio import Portfolio
from strategies.signal_engine import generate_signals
from indicators.market import market_regime_score

WATCHLIST = [
    "TSLA",
    "NVDA",
    "META",
    "AMZN",
    "MSFT",
    "AAPL",
    "GOOGL"
]


def run_simulation():
    market = MarketDataService()
    benchmark = market.get_history("SPY")
    market_regime = market_regime_score(benchmark)

    portfolio = Portfolio(
        starting_cash=100000
    )

    results = []

    for symbol in WATCHLIST:

        df = market.get_history(symbol)

        if df.empty:
            continue

        metrics = score_stock(symbol, df, market_regime)

        results.append(metrics)

    signals = generate_signals(results)

    portfolio.rebalance(signals)

    portfolio.print_summary()

if __name__ == "__main__":
    run_simulation()

