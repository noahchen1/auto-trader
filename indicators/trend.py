def calculate_trend_score(df):
    close = df["Close"]

    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]

    current = close.iloc[-1]

    score = 0

    if current > ma50:
        score += 1
    
    if ma50 > ma200:
        score += 1
    
    return score