def volume_score(df):
    current = df["Volume"].iloc[-1]

    average = df["Volume"].rolling(20).mean().iloc[-1]

    if current > average * 2:
        return 2

    if current > average * 1.5:
        return 1

    return 0