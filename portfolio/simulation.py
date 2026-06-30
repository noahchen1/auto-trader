import json
from pathlib import Path

import pandas as pd

from data.universe import normalize_symbol


def load_simulated_portfolio(path):
    if path is None:
        return None

    portfolio_path = Path(path)

    with portfolio_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    cash = float(data.get("cash", 0))
    positions = {}

    for item in data.get("positions", []):
        symbol = normalize_symbol(item["symbol"])
        shares = float(item["shares"])
        entry_price = item.get("entry_price", item.get("average_price"))

        if entry_price is None:
            raise ValueError(
                f"{portfolio_path} position {symbol} needs entry_price or average_price"
            )

        entry_date = item.get("entry_date")
        position = {
            "shares": shares,
            "entry_price": float(entry_price),
            "entry_date": pd.Timestamp(entry_date) if entry_date else None,
            "highest_price": float(item.get("highest_price", entry_price)),
            "score": float(item.get("score", 0)),
            "rating": float(item.get("rating", item.get("score", 0))),
        }
        positions[symbol] = position

    return {
        "cash": cash,
        "positions": positions,
        "source": portfolio_path,
    }


def portfolio_symbols(portfolio):
    if not portfolio:
        return []

    return list(portfolio["positions"].keys())
