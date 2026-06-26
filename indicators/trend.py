def calculate_trend_score(df):
    close = df["Close"]
    current = close.iloc[-1]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]

    score = 0
    
    if current > ma20:
        score += 1

    if current > ma50:
        score += 1

    if current > ma200:
        score += 1

    if ma20 > ma50:
        score += 1

    if ma50 > ma200:
        score += 1

    return score