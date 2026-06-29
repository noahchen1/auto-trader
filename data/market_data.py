import yfinance as yf
import pandas as pd

class MarketDataService:
    def get_history(self, symbol, period="2y", interval="1d", start=None, end=None):
        download_args = {
            "tickers": symbol,
            "interval": interval,
            "auto_adjust": True,
            "progress": False,
        }

        if start or end:
            download_args["start"] = start
            download_args["end"] = end
        else:
            download_args["period"] = period

        df = yf.download(**download_args)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    
    def get_price(self, symbol):
        data = yf.Ticker(symbol).history(period="1d")

        if data.empty:
            return None
        
        return float(data["Close"].iloc[-1])
