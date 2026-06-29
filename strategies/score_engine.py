from indicators.trend import calculate_trend_score
from indicators.volume import volume_score
from indicators.momentum  import calculate_rsi
from indicators.breakout import breakout_score
from indicators.strength import relative_strength_score
from indicators.risk import drawdown_score, volatility_score

FACTOR_WEIGHTS = {
    "momentum": 0.55,
    "risk": 0.25,
    "volume": 0.10,
    "timing": 0.10,
}


def normalize(value, maximum):
    if maximum == 0:
        return 0

    return min(value / maximum, 1) * 100


def calculate_momentum_factor(trend, breakout, relative_strength):
    return (
        normalize(trend, 5) * 0.40
        + normalize(relative_strength, 4) * 0.40
        + normalize(breakout, 2) * 0.20
    )


def calculate_risk_factor(volatility, drawdown):
    return (
        normalize(volatility, 2) * 0.50
        + normalize(drawdown, 2) * 0.50
    )


def calculate_timing_factor(rsi):
    if 45 <= rsi <= 85:
        return 100

    if 35 <= rsi < 45 or 85 < rsi <= 90:
        return 50

    return 0


def score_stock(symbol, df, market_regime=None):

    trend = calculate_trend_score(df)
    volume = volume_score(df)
    breakout = breakout_score(df)
    rs = relative_strength_score(df)
    rsi = calculate_rsi(df)
    volatility = volatility_score(df)
    drawdown = drawdown_score(df)

    momentum_factor = calculate_momentum_factor(trend, breakout, rs)
    risk_factor = calculate_risk_factor(volatility, drawdown)
    volume_factor = normalize(volume, 2)
    timing_factor = calculate_timing_factor(rsi)

    rating = (
        momentum_factor * FACTOR_WEIGHTS["momentum"]
        + risk_factor * FACTOR_WEIGHTS["risk"]
        + volume_factor * FACTOR_WEIGHTS["volume"]
        + timing_factor * FACTOR_WEIGHTS["timing"]
    )
    rating = round(rating, 2)

    return {
        "symbol": symbol,
        "score": rating,
        "rating": rating,
        "score_pct": rating,
        "momentum_factor": round(momentum_factor, 2),
        "risk_factor": round(risk_factor, 2),
        "volume_factor": round(volume_factor, 2),
        "timing_factor": round(timing_factor, 2),
        "trend": trend,
        "volume": volume,
        "breakout": breakout,
        "relative_strength": rs,
        "rsi": round(rsi, 2),
        "volatility": volatility,
        "drawdown": drawdown,
        "market": market_regime["score"] if market_regime else 0,
        "market_regime": market_regime["regime"] if market_regime else "UNKNOWN",
        "price": float(df["Close"].iloc[-1])
    }
