def volatility_score(df):
    close = df["Close"]

    if len(close) < 21:
        return 0

    annualized_volatility = close.pct_change().tail(20).std() * (252 ** 0.5)

    if annualized_volatility < 0.25:
        return 2

    if annualized_volatility < 0.45:
        return 1

    return 0


def drawdown_score(df):
    close = df["Close"]

    if len(close) < 63:
        return 0

    rolling_high = close.tail(63).max()
    drawdown = close.iloc[-1] / rolling_high - 1

    if drawdown > -0.08:
        return 2

    if drawdown > -0.15:
        return 1

    return 0
