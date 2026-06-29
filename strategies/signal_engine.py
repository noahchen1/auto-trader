MAX_POSITIONS = 5
MIN_BUY_SCORE = 11
MIN_BUY_CONFIDENCE = 58

def generate_signals(results):

    ranked = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

    signals = []

    for i, stock in enumerate(ranked):

        signal = "HOLD"

        if (
            i < MAX_POSITIONS
            and stock["score"] >= MIN_BUY_SCORE
            and stock["confidence"] >= MIN_BUY_CONFIDENCE
            and stock["market_regime"] != "DEFENSIVE"
        ):
            signal = "BUY"

        stock["rank"] = i + 1
        stock["signal"] = signal

        signals.append(stock)

    return signals
