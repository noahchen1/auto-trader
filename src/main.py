import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime
import csv

START_BALANCE = 1000.0
symbol = "TSLA"

def fetch_market_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if not data.empty:
        latest_price = float(data['Close'].iloc[-1])
        return {"price": latest_price, "data": data}
    else:
        return {"price": 0.0, "data": pd.DataFrame()}

def calculate_indicators(data):
    close = data['Close']
    short_ma = close.rolling(window=20).mean().iloc[-1]
    long_ma = close.rolling(window=100).mean().iloc[-1]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_latest = rsi.iloc[-1]
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

def decide_trade(market, balance, price):
    data = market["data"]
    if data.empty:
        return "hold", 0
    indicators = calculate_indicators(data)
    print(f"Indicators: {indicators}")

    # Example: Stronger signals = larger quantity
    strength = 0
    if indicators["short_ma"] > indicators["long_ma"]:
        strength += 1
    if indicators["rsi"] < 50:
        strength += 1
    if indicators["macd"] > indicators["macd_signal"]:
        strength += 1

    if strength == 3:
        qty = int(balance // price)  # Go all-in
        return "buy", qty
    elif strength == 2:
        qty = int((balance // price) * 0.5)  # Half-in
        return "buy", qty
    elif strength == 1:
        qty = int((balance // price) * 0.25)  # Quarter-in
        return "buy", qty
    # Sell logic: if all sell signals are strong, sell all
    if (
        indicators["short_ma"] < indicators["long_ma"] and
        indicators["rsi"] > 60 and
        indicators["macd"] < indicators["macd_signal"]
    ):
        return "sell", "all"
    return "hold", 0

def plot_performance(times, balances):
    plt.figure(figsize=(10, 5))
    plt.plot(times, balances, marker='o')
    plt.title(f"{symbol} Portfolio Performance")
    plt.xlabel("Time")
    plt.ylabel("Portfolio Value ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("performance_chart.png")
    plt.show()

    with open("performance_history.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date"] + times)
        writer.writerow(["Portfolio"] + balances)

def run_simulation(symbol, start_balance):
    balance = start_balance
    shares = 0
    times = []
    balances = []
    print("Starting trading simulation...")
    last_action = None  # Track previous action to trigger only on signal change
    while True:
        now = datetime.now()
        # Only run during market hours (9:30am to 4:00pm US Eastern)
        if now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 16:
            print("Market closed. Simulation ended.")
            break
        market = fetch_market_data(symbol)
        price = market["price"]
        action, qty = decide_trade(market, balance, price)
        # Only trade if action changes (buy/sell), not hold
        if action != last_action and action == "buy" and qty > 0 and balance >= price * qty:
            shares += qty
            balance -= price * qty
            print(f"Bought {qty} shares at ${price:.2f}")
        elif action != last_action and action == "sell" and shares > 0:
            if qty == "all":
                qty = shares
            balance += price * qty
            shares -= qty
            print(f"Sold {qty} shares at ${price:.2f}")
        last_action = action  # Update last action
        # Portfolio value = cash + value of shares
        portfolio_value = balance + shares * price
        times.append(now.strftime("%H:%M"))
        balances.append(portfolio_value)
        print(f"{now.strftime('%H:%M')}: Price=${price:.2f}, Action={action}, Quantity={qty}, Shares={shares}, Balance=${balance:.2f}, Portfolio=${portfolio_value:.2f}")
        time.sleep(60)  # Wait for 1 minute

if __name__ == "__main__":
    run_simulation(symbol, START_BALANCE)