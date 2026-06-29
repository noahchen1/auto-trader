from indicators.trend import calculate_trend_score
from indicators.volume import volume_score
from indicators.rsi import rsi_score
from indicators.momentum  import calculate_rsi
from indicators.breakout import breakout_score
from indicators.strength import relative_strength_score
from indicators.risk import drawdown_score, volatility_score

MAX_SCORE = 19


def score_stock(symbol, df, market_regime=None):

    trend = calculate_trend_score(df)
    volume = volume_score(df)
    breakout = breakout_score(df)
    rs = relative_strength_score(df)
    rsi = calculate_rsi(df)
    rsiScore = rsi_score(rsi)
    volatility = volatility_score(df)
    drawdown = drawdown_score(df)
    market = market_regime["score"] if market_regime else 0

    score = (
        trend
        + volume
        + breakout
        + rs
        + rsiScore
        + volatility
        + drawdown
        + market
    )

    return {
        "symbol": symbol,
        "score": score,
        "confidence": round(score / MAX_SCORE * 100),
        "trend": trend,
        "volume": volume,
        "breakout": breakout,
        "relative_strength": rs,
        "rsi": round(rsi, 2),
        "volatility": volatility,
        "drawdown": drawdown,
        "market": market,
        "market_regime": market_regime["regime"] if market_regime else "UNKNOWN",
        "price": float(df["Close"].iloc[-1])
    }
