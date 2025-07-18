def fetch_market_data(symbol):
    print(f"Fetch market data for {symbol}... (simulation)")
    return {"price": 100.0}

def decide_trade(data):
    print("Deciding trade based on data... (simulation)")

    if data["price"] < 105:
        return "buy"
    elif data["price"] > 110:
        return "sell"
    else:
        return "hold"
    
def execute_trade(action, symbol, qty):
    print(f"Executing {action} for {qty} shares of {symbol}... (simulation)")

def main():
    symbol = input("Enter stock symbol: ")
    qty = int(input("Enter quantity: "))
    data = fetch_market_data(symbol)
    action = decide_trade(data)

    if action in ["buy", "sell"]:
        execute_trade(action, symbol, qty)
    else:
        print("No trade executed (hold).")


if __name__ == "__main__":
    main()