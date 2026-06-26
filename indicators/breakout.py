def breakout_score(df):
    current = df["Close"].iloc[-1]

    high_52 = (
        df["Close"]
        .rolling(252)
        .max()
        .shift(1)
        .iloc[-1]
    )

    if current > high_52:
        return 2

    return 0