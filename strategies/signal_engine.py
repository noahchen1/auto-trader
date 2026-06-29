MAX_POSITIONS = 5
MIN_BUY_RATING = 65
MAX_SELL_RATING = 45
MIN_MOMENTUM_FACTOR = 45
MIN_RISK_FACTOR = 35


def should_sell(stock, is_buy_candidate):
    return (
        not is_buy_candidate
        or stock["market_regime"] == "DEFENSIVE"
        or stock["rating"] <= MAX_SELL_RATING
        or stock["momentum_factor"] < MIN_MOMENTUM_FACTOR
        or stock["risk_factor"] < MIN_RISK_FACTOR
    )


def generate_signals(results, current_positions=None):
    current_positions = current_positions or {}

    ranked = sorted(
        results,
        key=lambda x: x["rating"],
        reverse=True
    )

    signals = []

    for i, stock in enumerate(ranked):
        stock = stock.copy()
        symbol = stock["symbol"]
        is_held = symbol in current_positions

        signal = "HOLD"
        is_buy_candidate = (
            i < MAX_POSITIONS
            and stock["rating"] >= MIN_BUY_RATING
            and stock["market_regime"] != "DEFENSIVE"
        )

        if is_buy_candidate and not is_held:
            signal = "BUY"

        if is_held and should_sell(stock, is_buy_candidate):
            signal = "SELL"

        stock["rank"] = i + 1
        stock["signal"] = signal

        signals.append(stock)

    return signals
