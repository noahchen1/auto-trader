def market_regime_score(df):
    close = df["Close"]

    if len(close) < 200:
        return {
            "score": 0,
            "regime": "UNKNOWN",
            "market_trend": 0.0,
            "market_drawdown": 0.0,
        }

    current = close.iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    high_252 = close.rolling(252, min_periods=200).max().iloc[-1]
    drawdown = current / high_252 - 1

    score = 0

    if current > ma200:
        score += 2

    if ma50 > ma200:
        score += 1

    if drawdown > -0.08:
        score += 1

    if score >= 3:
        regime = "BULL"
    elif score == 2:
        regime = "NEUTRAL"
    else:
        regime = "DEFENSIVE"

    return {
        "score": score,
        "regime": regime,
        "market_trend": round(current / ma200 - 1, 4),
        "market_drawdown": round(drawdown, 4),
    }
