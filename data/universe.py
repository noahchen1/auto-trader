import requests
from bs4 import BeautifulSoup


SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
REQUEST_HEADERS = {
    "User-Agent": (
        "auto-trader/1.0 "
        "(https://github.com/local/auto-trader; educational backtesting tool)"
    )
}

DEFAULT_UNIVERSE = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "TSLA",
    "AVGO",
    "ORCL",
    "AMD",
    "CRM",
    "ADBE",
    "NFLX",
    "INTC",
    "CSCO",
    "QCOM",
    "TXN",
    "IBM",
    "NOW",
    "AMAT",
    "MU",
    "LRCX",
    "KLAC",
    "PANW",
    "CRWD",
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "C",
    "V",
    "MA",
    "AXP",
    "BLK",
    "SCHW",
    "UNH",
    "JNJ",
    "LLY",
    "MRK",
    "ABBV",
    "PFE",
    "TMO",
    "ABT",
    "DHR",
    "ISRG",
    "AMGN",
    "GILD",
    "COST",
    "WMT",
    "HD",
    "LOW",
    "TGT",
    "NKE",
    "MCD",
    "SBUX",
    "CMG",
    "KO",
    "PEP",
    "PG",
    "CL",
    "PM",
    "MO",
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "EOG",
    "LIN",
    "SHW",
    "APD",
    "CAT",
    "DE",
    "GE",
    "HON",
    "UNP",
    "UPS",
    "RTX",
    "LMT",
    "BA",
    "DIS",
    "CMCSA",
    "T",
    "VZ",
]


def normalize_symbol(symbol):
    return symbol.strip().upper().replace(".", "-")


def unique_symbols(symbols):
    seen = set()
    normalized = []

    for symbol in symbols:
        symbol = normalize_symbol(symbol)

        if not symbol or symbol in seen:
            continue

        seen.add(symbol)
        normalized.append(symbol)

    return normalized


def parse_symbols(value):
    if not value:
        return []

    return unique_symbols(value.split(","))


def load_symbols_file(path):
    symbols = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.split("#", 1)[0]
            symbols.extend(line.replace(",", " ").split())

    return unique_symbols(symbols)


def load_sp500_symbols():
    response = requests.get(SP500_URL, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})

    if table is None:
        raise RuntimeError("Could not find S&P 500 constituents table.")

    symbols = []

    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")

        if not cells:
            continue

        symbols.append(cells[0].get_text(strip=True))

    return unique_symbols(symbols)
