import yfinance as yf
import pandas as pd

class MarketDataService:
    def get_history(self, symbol):
        df = yf.download(
            symbol,
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    
    def get_price(self, symbol):
        data = yf.Ticker(symbol).history(preiod="1d")

        if data.empty:
            return None
        
        return float(data["Close"].iloc[-1])