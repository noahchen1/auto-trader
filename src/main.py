import requests
import yfinance as yf
import pandas as pd

def fetch_market_data(symbol):
    print(f"Fetch market data for {symbol}... (simulation)")
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="5d", interval="1m")
    print(data)
    if not data.empty:
        latest_price = int(data['Close'].iloc[-1])
        print(f"Fetched market data for {symbol}: ${latest_price}")
        return {"price": latest_price, "data": data}
    else:
        print("No data found.")
        return {"price": 0.0, "data": pd.DataFrame()}

def calculate_indicators(data):
    close = data['Close']
    # Moving Averages
    short_ma = close.rolling(window=20).mean().iloc[-1]
    long_ma = close.rolling(window=100).mean().iloc[-1]
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_latest = rsi.iloc[-1]
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_latest = macd.iloc[-1]
    signal_latest = signal.iloc[-1]
    return {
        "short_ma": short_ma,
        "long_ma": long_ma,
        "rsi": rsi_latest,
        "macd": macd_latest,
        "macd_signal": signal_latest
    }

def decide_trade(market):
    print("Deciding trade based on data... (sophisticated strategy)")
    data = market["data"]
    if data.empty:
        print("No data for decision.")
        return "hold"
    indicators = calculate_indicators(data)
    print(f"Indicators: {indicators}")

    # Example strategy:
    # Buy if short MA > long MA, RSI < 70, MACD > Signal
    # Sell if short MA < long MA, RSI > 30, MACD < Signal
    if (
        indicators["short_ma"] > indicators["long_ma"] and
        indicators["rsi"] < 70 and
        indicators["macd"] > indicators["macd_signal"]
    ):
        return "buy"
    elif (
        indicators["short_ma"] < indicators["long_ma"] and
        indicators["rsi"] > 30 and
        indicators["macd"] < indicators["macd_signal"]
    ):
        return "sell"
    else:
        return "hold"

def execute_trade(action, symbol, qty):
    print(f"Executing {action} for {qty} shares of {symbol}... (simulation)")

def main():
    symbol = input("Enter stock symbol: ")
    qty = int(input("Enter quantity: "))
    market = fetch_market_data(symbol)
    action = decide_trade(market)
    if action in ["buy", "sell"]:
        execute_trade(action, symbol, qty)
    else:
        print("No trade executed (hold).")
    print(f"Latest price: ${market['price']}, Action: {action}")

if __name__ == "__main__":
    main()