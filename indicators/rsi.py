def rsi_score(rsi):
    if 50 <= rsi <= 75:
        return 2

    if 40 <= rsi < 50:
        return 1

    return 0