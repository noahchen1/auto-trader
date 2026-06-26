MAX_POSITIONS = 5

def generate_signals(results):

    ranked = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

    signals = []

    for i, stock in enumerate(ranked):

        signal = "HOLD"

        if i < MAX_POSITIONS:
            signal = "BUY"

        stock["rank"] = i + 1
        stock["signal"] = signal

        signals.append(stock)

    return signals