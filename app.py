import argparse
import random
from pathlib import Path

import pandas as pd

from backtest.simulator import BacktestSimulator
from data.market_data import MarketDataService
from data.universe import (
    DEFAULT_UNIVERSE,
    load_sp500_symbols,
    load_symbols_file,
    parse_symbols,
)
from strategies.score_engine import score_stock
from portfolio.portfolio import Portfolio
from portfolio.simulation import load_simulated_portfolio, portfolio_symbols
from strategies.signal_engine import generate_signals
from indicators.market import market_regime_score


def run_simulation(symbols, near_close=False, near_close_interval="1m"):
    market = MarketDataService()
    benchmark, benchmark_timestamp = get_signal_history(
        market,
        "SPY",
        near_close,
        near_close_interval,
    )
    market_regime = market_regime_score(benchmark)

    portfolio = Portfolio(
        starting_cash=100000
    )

    results = []
    near_close_timestamps = []

    for symbol in symbols:

        df, timestamp = get_signal_history(
            market,
            symbol,
            near_close,
            near_close_interval,
        )

        if df.empty:
            continue

        if timestamp is not None:
            near_close_timestamps.append(timestamp)

        metrics = score_stock(symbol, df, market_regime)

        results.append(metrics)

    signals = generate_signals(results)

    print_signal_data_source(
        near_close,
        near_close_interval,
        [benchmark_timestamp, *near_close_timestamps],
    )

    portfolio.rebalance(signals)

    portfolio.print_summary()


DEFAULT_LOOKBACK_DAYS = 253
DEFAULT_TRADES_CSV = "transactions.csv"
DEFAULT_STOP_LOSS_PCT = 0.05
DEFAULT_TRAILING_STOP_PCT = 0.15
DEFAULT_ITERATIVE_RESULTS_CSV = "iterative_backtests.csv"


def get_signal_history(market, symbol, near_close, near_close_interval):
    if near_close:
        return market.get_history_with_near_close(
            symbol,
            intraday_interval=near_close_interval,
        )

    return market.get_history(symbol), None


def print_signal_data_source(near_close, near_close_interval, timestamps):
    if not near_close:
        print("\nSignal data: daily close history")
        return

    timestamps = [timestamp for timestamp in timestamps if timestamp is not None]

    if not timestamps:
        print("\nSignal data: near-close requested, but no intraday bars were merged.")
        return

    latest_timestamp = max(timestamps)
    print(
        "\nSignal data: "
        f"near-close {near_close_interval} intraday bars through {latest_timestamp}"
    )


def run_backtest(
    symbols,
    buy_check_days=5,
    sell_check_days=1,
    trades_limit=None,
    start_date=None,
    end_date=None,
    trades_csv=None,
    stop_loss_pct=DEFAULT_STOP_LOSS_PCT,
    trailing_stop_pct=DEFAULT_TRAILING_STOP_PCT,
    portfolio_json=None,
):
    simulated_portfolio = load_simulated_portfolio(portfolio_json)
    symbols = include_portfolio_symbols(symbols, simulated_portfolio)
    market = MarketDataService()
    history = {}
    download_start = calculate_download_start(start_date, DEFAULT_LOOKBACK_DAYS)
    download_end = calculate_download_end(end_date)

    for symbol in symbols:
        df = market.get_history(symbol, start=download_start, end=download_end)

        if not df.empty:
            history[symbol] = df

    benchmark = market.get_history("SPY", start=download_start, end=download_end)

    simulator = BacktestSimulator(
        price_history=history,
        benchmark_history=benchmark,
        starting_cash=portfolio_starting_cash(simulated_portfolio, 100000),
        lookback_days=DEFAULT_LOOKBACK_DAYS,
        buy_check_days=buy_check_days,
        sell_check_days=sell_check_days,
        start_date=start_date,
        end_date=end_date,
        stop_loss_pct=stop_loss_pct,
        trailing_stop_pct=trailing_stop_pct,
        initial_cash=portfolio_cash(simulated_portfolio),
        initial_positions=portfolio_positions(simulated_portfolio),
    )
    result = simulator.run()

    print("\nBacktest\n")
    print(f"Starting cash: ${result['starting_cash']:.2f}")
    print(f"Ending value:  ${result['ending_value']:.2f}")
    print(f"Total return:  {result['total_return']:.2%}")
    print(f"Start date:    {start_date or 'Downloaded history start'}")
    print(f"End date:      {end_date or 'Downloaded history end'}")
    print(f"Buy checks:    Every {buy_check_days} trading day(s)")
    print(f"Sell checks:   Every {sell_check_days} trading day(s)")
    print("Execution:     Next trading day open")
    print(f"Hard stop:     {stop_loss_pct:.2%}")
    print(f"Trailing stop: {trailing_stop_pct:.2%}")
    print(f"Portfolio:     {portfolio_label(simulated_portfolio)}")
    print(f"Trades:        {len(result['trades'])}")
    print_transaction_history(result["trades"], trades_limit)

    if trades_csv:
        csv_path = export_transaction_history(result["trades"], trades_csv)
        print(f"\nTransaction CSV written to {csv_path}")


def run_iterative_backtests(
    symbols,
    iterations=25,
    min_period_days=60,
    max_period_days=252,
    buy_check_days=5,
    sell_check_days=1,
    start_date=None,
    end_date=None,
    results_csv=DEFAULT_ITERATIVE_RESULTS_CSV,
    seed=None,
    stop_loss_pct=DEFAULT_STOP_LOSS_PCT,
    trailing_stop_pct=DEFAULT_TRAILING_STOP_PCT,
    portfolio_json=None,
):
    simulated_portfolio = load_simulated_portfolio(portfolio_json)
    symbols = include_portfolio_symbols(symbols, simulated_portfolio)
    market = MarketDataService()
    history = {}
    download_start = calculate_download_start(start_date, DEFAULT_LOOKBACK_DAYS)
    download_end = calculate_download_end(end_date)

    for symbol in symbols:
        df = market.get_history(symbol, start=download_start, end=download_end)

        if not df.empty:
            history[symbol] = df

    benchmark = market.get_history("SPY", start=download_start, end=download_end)
    periods = random_backtest_periods(
        benchmark.index.sort_values(),
        iterations,
        min_period_days,
        max_period_days,
        DEFAULT_LOOKBACK_DAYS,
        seed,
        start_date,
        end_date,
    )

    results = []

    for index, period in enumerate(periods, start=1):
        simulator = BacktestSimulator(
            price_history=history,
            benchmark_history=benchmark,
            starting_cash=portfolio_starting_cash(simulated_portfolio, 100000),
            lookback_days=DEFAULT_LOOKBACK_DAYS,
            buy_check_days=buy_check_days,
            sell_check_days=sell_check_days,
            start_date=period["start_date"],
            end_date=period["end_date"],
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct,
            initial_cash=portfolio_cash(simulated_portfolio),
            initial_positions=portfolio_positions(simulated_portfolio),
        )
        result = simulator.run()
        results.append(
            {
                "iteration": index,
                "start_date": period["start_date"],
                "end_date": period["end_date"],
                "trading_days": period["trading_days"],
                "starting_value": result["starting_cash"],
                "ending_value": result["ending_value"],
                "total_return": result["total_return"],
                "trades": len(result["trades"]),
            }
        )

    print_iterative_summary(results, simulated_portfolio)

    if results_csv:
        csv_path = export_iterative_results(results, results_csv)
        print(f"\nIterative results CSV written to {csv_path}")


def include_portfolio_symbols(symbols, simulated_portfolio):
    portfolio_symbols_list = portfolio_symbols(simulated_portfolio)

    if not portfolio_symbols_list:
        return symbols

    return list(dict.fromkeys([*symbols, *portfolio_symbols_list]))


def portfolio_starting_cash(simulated_portfolio, default):
    if not simulated_portfolio:
        return default

    return simulated_portfolio["cash"]


def portfolio_cash(simulated_portfolio):
    if not simulated_portfolio:
        return None

    return simulated_portfolio["cash"]


def portfolio_positions(simulated_portfolio):
    if not simulated_portfolio:
        return None

    return simulated_portfolio["positions"]


def portfolio_label(simulated_portfolio):
    if not simulated_portfolio:
        return "default cash account"

    return str(simulated_portfolio["source"])


def random_backtest_periods(
    dates,
    iterations,
    min_period_days,
    max_period_days,
    lookback_days,
    seed,
    start_date=None,
    end_date=None,
):
    if min_period_days > max_period_days:
        raise SystemExit("--period-min-days must be less than or equal to --period-max-days")

    if start_date:
        dates = dates[dates >= pd.Timestamp(start_date)]

    if end_date:
        dates = dates[dates <= pd.Timestamp(end_date)]

    if len(dates) < lookback_days + min_period_days:
        raise SystemExit("Not enough downloaded history for the requested random periods.")

    rng = random.Random(seed)
    periods = []
    first_start_index = lookback_days
    last_start_index = len(dates) - min_period_days

    for _ in range(iterations):
        start_index = rng.randint(first_start_index, last_start_index)
        longest_period = min(max_period_days, len(dates) - start_index)
        trading_days = rng.randint(min_period_days, longest_period)
        end_index = start_index + trading_days - 1
        periods.append(
            {
                "start_date": dates[start_index].strftime("%Y-%m-%d"),
                "end_date": dates[end_index].strftime("%Y-%m-%d"),
                "trading_days": trading_days,
            }
        )

    return periods


def print_iterative_summary(results, simulated_portfolio):
    print("\nIterative Backtests\n")
    print(f"Runs:          {len(results)}")
    print(f"Portfolio:     {portfolio_label(simulated_portfolio)}")

    if not results:
        print("No iterative backtests were generated.")
        return

    returns = pd.Series([result["total_return"] for result in results])
    trades = pd.Series([result["trades"] for result in results])

    print(f"Average return:{returns.mean():11.2%}")
    print(f"Median return: {returns.median():11.2%}")
    print(f"Best return:   {returns.max():11.2%}")
    print(f"Worst return:  {returns.min():11.2%}")
    print(f"Win rate:      {(returns > 0).mean():11.2%}")
    print(f"Avg trades:    {trades.mean():11.1f}")
    print("\nRuns\n")

    header = (
        f"{'#':>3} "
        f"{'Start':10} "
        f"{'End':10} "
        f"{'Days':>5} "
        f"{'Start Value':>14} "
        f"{'End Value':>14} "
        f"{'Return':>9} "
        f"{'Trades':>6}"
    )
    print(header)
    print("-" * len(header))

    for result in results:
        print(
            f"{result['iteration']:3} "
            f"{result['start_date']:10} "
            f"{result['end_date']:10} "
            f"{result['trading_days']:5} "
            f"${result['starting_value']:13,.2f} "
            f"${result['ending_value']:13,.2f} "
            f"{result['total_return']:9.2%} "
            f"{result['trades']:6}"
        )


def export_iterative_results(results, path):
    columns = [
        "iteration",
        "start_date",
        "end_date",
        "trading_days",
        "starting_value",
        "ending_value",
        "total_return",
        "trades",
    ]
    csv_path = Path(path)

    if csv_path.parent != Path("."):
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(results, columns=columns).to_csv(csv_path, index=False)
    return csv_path


def format_trade_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    return str(value)


def format_optional_money(value):
    if value is None:
        return "-"

    return f"${value:,.2f}"


def format_optional_pct(value):
    if value is None:
        return "-"

    return f"{value:.2%}"


def print_transaction_history(trades, limit=None):
    print("\nTransaction History\n")

    if not trades:
        print("No transactions were generated by this backtest.")
        return

    visible_trades = trades if limit is None else trades[:limit]
    header = (
        f"{'Signal':10} "
        f"{'Date':10} "
        f"{'Side':4} "
        f"{'Symbol':6} "
        f"{'Shares':>10} "
        f"{'Price':>11} "
        f"{'Value':>13} "
        f"{'Rating':>7} "
        f"{'Reason':14} "
        f"{'P/L':>12} "
        f"{'P/L %':>8} "
        f"{'Days':>6}"
    )
    print(header)
    print("-" * len(header))

    for trade in visible_trades:
        holding_days = trade["holding_days"]
        holding_days = "-" if holding_days is None else str(holding_days)

        print(
            f"{format_trade_date(trade.get('signal_date', '-')):10} "
            f"{format_trade_date(trade['date']):10} "
            f"{trade['side']:4} "
            f"{trade['symbol']:6} "
            f"{trade['shares']:10.2f} "
            f"${trade['price']:10.2f} "
            f"${trade['value']:12,.2f} "
            f"{trade['rating']:7.2f} "
            f"{trade.get('reason', '-'):14} "
            f"{format_optional_money(trade['pnl']):>12} "
            f"{format_optional_pct(trade['pnl_pct']):>8} "
            f"{holding_days:>6}"
        )

    if limit is not None and len(trades) > limit:
        remaining = len(trades) - limit
        print(f"\n... {remaining} more transaction(s) not shown.")


def export_transaction_history(trades, path):
    columns = [
        "signal_date",
        "date",
        "side",
        "symbol",
        "shares",
        "price",
        "value",
        "rating",
        "reason",
        "entry_date",
        "entry_price",
        "cost_basis",
        "pnl",
        "pnl_pct",
        "holding_days",
    ]
    rows = []

    for trade in trades:
        row = {}

        for column in columns:
            row[column] = trade.get(column)

        row["date"] = format_trade_date(row["date"])

        if row["entry_date"] is not None:
            row["entry_date"] = format_trade_date(row["entry_date"])

        if row["signal_date"] is not None:
            row["signal_date"] = format_trade_date(row["signal_date"])

        rows.append(row)

    csv_path = Path(path)

    if csv_path.parent != Path("."):
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(rows, columns=columns).to_csv(csv_path, index=False)
    return csv_path


def resolve_symbols(args):
    if args.symbols:
        symbols = parse_symbols(args.symbols)
    elif args.symbols_file:
        symbols = load_symbols_file(args.symbols_file)
    elif args.universe == "sp500":
        try:
            symbols = load_sp500_symbols()
        except Exception as error:
            print(f"Could not load S&P 500 universe: {error}")
            print("Falling back to built-in default universe.")
            symbols = DEFAULT_UNIVERSE
    else:
        symbols = DEFAULT_UNIVERSE

    if args.limit:
        symbols = symbols[:args.limit]

    return symbols


def positive_int(value):
    parsed = int(value)

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")

    return parsed


def pct_float(value):
    parsed = float(value)

    if parsed < 0 or parsed >= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")

    return parsed


def valid_date(value):
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from error


def calculate_download_start(start_date, lookback_days):
    if not start_date:
        return None

    warmup_days = lookback_days * 2
    return (pd.Timestamp(start_date) - pd.Timedelta(days=warmup_days)).strftime(
        "%Y-%m-%d"  
    )


def calculate_download_end(end_date):
    if not end_date:
        return None

    return (pd.Timestamp(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def validate_date_range(start_date, end_date):
    if start_date and end_date and pd.Timestamp(end_date) < pd.Timestamp(start_date):
        raise SystemExit("--end-date must be on or after --start-date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run a historical rolling-window backtest instead of today's signals.",
    )
    parser.add_argument(
        "--iterative-backtest",
        action="store_true",
        help="Run repeated backtests over random historical periods.",
    )
    parser.add_argument(
        "--near-close",
        action="store_true",
        help="For today's signal scan, merge today's intraday bars into the daily candle.",
    )
    parser.add_argument(
        "--near-close-interval",
        choices=["1m", "2m", "5m", "15m", "30m", "60m"],
        default="1m",
        help="Intraday interval to use with --near-close.",
    )
    parser.add_argument(
        "--symbols",
        help="Comma-separated symbols to scan instead of the default universe.",
    )
    parser.add_argument(
        "--symbols-file",
        help="Path to a symbol file. Supports comma, space, or newline-separated symbols.",
    )
    parser.add_argument(
        "--universe",
        choices=["default", "sp500"],
        default="sp500",
        help="Stock universe to scan when --symbols or --symbols-file is not provided.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Only use the first N symbols from the selected universe.",
    )
    parser.add_argument(
        "--trades-limit",
        type=int,
        help="Only print the first N transactions from a backtest.",
    )
    parser.add_argument(
        "--trades-csv",
        default=DEFAULT_TRADES_CSV,
        help="Write the full backtest transaction history to this CSV path.",
    )
    parser.add_argument(
        "--results-csv",
        default=DEFAULT_ITERATIVE_RESULTS_CSV,
        help="Write iterative backtest results to this CSV path.",
    )
    parser.add_argument(
        "--no-results-csv",
        action="store_true",
        help="Do not write an iterative backtest results CSV.",
    )
    parser.add_argument(
        "--no-trades-csv",
        action="store_true",
        help="Do not write a backtest transaction CSV.",
    )
    parser.add_argument(
        "--buy-check-days",
        type=positive_int,
        default=5,
        help="How often the backtest checks for new buys, in trading days.",
    )
    parser.add_argument(
        "--sell-check-days",
        type=positive_int,
        default=1,
        help="How often the backtest checks existing positions for sells, in trading days.",
    )
    parser.add_argument(
        "--stop-loss-pct",
        type=pct_float,
        default=DEFAULT_STOP_LOSS_PCT,
        help="Hard stop loss from entry price, as a decimal. Use 0 to disable.",
    )
    parser.add_argument(
        "--trailing-stop-pct",
        type=pct_float,
        default=DEFAULT_TRAILING_STOP_PCT,
        help="Trailing stop from highest close since entry, as a decimal. Use 0 to disable.",
    )
    parser.add_argument(
        "--portfolio-json",
        help="Path to a simulated portfolio JSON file for backtests.",
    )
    parser.add_argument(
        "--iterations",
        type=positive_int,
        default=25,
        help="How many random-period backtests to run with --iterative-backtest.",
    )
    parser.add_argument(
        "--period-min-days",
        type=positive_int,
        default=60,
        help="Minimum random backtest period length in trading days.",
    )
    parser.add_argument(
        "--period-max-days",
        type=positive_int,
        default=252,
        help="Maximum random backtest period length in trading days.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        help="Seed for repeatable random-period backtests.",
    )
    parser.add_argument(
        "--start-date",
        type=valid_date,
        help="Backtest start date, formatted YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end-date",
        type=valid_date,
        help="Backtest end date, formatted YYYY-MM-DD.",
    )
    args = parser.parse_args()
    validate_date_range(args.start_date, args.end_date)

    if args.near_close and (args.backtest or args.iterative_backtest):
        raise SystemExit("--near-close is only supported for today's signal scan.")

    symbols = resolve_symbols(args)

    print(f"Scanning {len(symbols)} symbols.")

    if args.iterative_backtest:
        run_iterative_backtests(
            symbols,
            iterations=args.iterations,
            min_period_days=args.period_min_days,
            max_period_days=args.period_max_days,
            buy_check_days=args.buy_check_days,
            sell_check_days=args.sell_check_days,
            start_date=args.start_date,
            end_date=args.end_date,
            results_csv=None if args.no_results_csv else args.results_csv,
            seed=args.random_seed,
            stop_loss_pct=args.stop_loss_pct,
            trailing_stop_pct=args.trailing_stop_pct,
            portfolio_json=args.portfolio_json,
        )
    elif args.backtest:
        run_backtest(
            symbols,
            buy_check_days=args.buy_check_days,
            sell_check_days=args.sell_check_days,
            trades_limit=args.trades_limit,
            start_date=args.start_date,
            end_date=args.end_date,
            trades_csv=None if args.no_trades_csv else args.trades_csv,
            stop_loss_pct=args.stop_loss_pct,
            trailing_stop_pct=args.trailing_stop_pct,
            portfolio_json=args.portfolio_json,
        )
    else:
        run_simulation(
            symbols,
            near_close=args.near_close,
            near_close_interval=args.near_close_interval,
        )
