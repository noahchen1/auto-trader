from datetime import datetime
from data.market_data import MarketDataService
from strategies.score_engine import score_stock

WATCHLIST = [
    "TSLA",
    "NVDA",
    "META",
    "AMZN",
    "MSFT",
    "AAPL",
    "GOOGL"
]

def process_symbol(symbol, market_service):
    """
    Process a single stock.
    """

    print(f"\nProcessing {symbol}")

    df = market_service.get_history(symbol)

    if df.empty:
        print(f"No data returned for {symbol}")
        return
    
    metrics = score_stock(df)

    print(metrics)

    # print(
    #     f"Score={metrics['score']} "
    #     f"RSI={metrics['rsi']:.2f}"
    # )

    # Future enhancements:
    #
    # repository.save_signal(...)
    #
    # if ai_result.confidence >= 80:
    #     execute_trade(...)
    

def run_simulation():
    start_time = datetime.now()

    print("=" * 50)
    print("TRADING BOT STARTED")
    print(start_time)
    print("=" * 50)

    market_service = MarketDataService()

    for symbol in WATCHLIST:
        try:
            process_symbol(
                symbol,
                market_service
            )
        except Exception as e:
            print(
                f"Failed processing {symbol}: {e}"
            )

    print("\nRun Complete")

if __name__ == "__main__":
    run_simulation()

