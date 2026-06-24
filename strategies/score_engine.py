from indicators.trend import calculate_trend_score
from indicators.volume import volume_score
from indicators.momentum import calculate_rsi

def score_stock(df):
    score = 0

    trend = calculate_trend_score(df)

    score += trend

    volume = volume_score(df)

    score += volume

    rsi = calculate_rsi(df)

    if 40 <= rsi <= 65:
        score += 2

    return {
        "score": score,
        "rsi": rsi
    }

