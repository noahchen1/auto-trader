import argparse

from backtest.simulator import BacktestSimulator
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


def run_backtest():
    market = MarketDataService()
    history = {}

    for symbol in WATCHLIST:
        df = market.get_history(symbol)

        if not df.empty:
            history[symbol] = df

    benchmark = market.get_history("SPY")

    simulator = BacktestSimulator(
        price_history=history,
        benchmark_history=benchmark,
        starting_cash=100000,
    )
    result = simulator.run()

    print("\nBacktest\n")
    print(f"Starting cash: ${result['starting_cash']:.2f}")
    print(f"Ending value:  ${result['ending_value']:.2f}")
    print(f"Total return:  {result['total_return']:.2%}")
    print(f"Trades:        {len(result['trades'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run a historical rolling-window backtest instead of today's signals.",
    )
    args = parser.parse_args()

    if args.backtest:
        run_backtest()
    else:
        run_simulation()

