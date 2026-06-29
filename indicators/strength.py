def relative_strength_score(df):
    close = df["Close"]

    if len(close) < 126:
        return 0

    current = close.iloc[-1]

    score = 0

    ret_3m = current / close.iloc[-63] - 1
    ret_6m = current / close.iloc[-126] - 1

    if ret_3m > 0.10:
        score += 2

    if ret_6m > 0.20:
        score += 2

    return score
