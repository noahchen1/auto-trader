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

    def get_history_with_near_close(
        self,
        symbol,
        period="2y",
        intraday_period="1d",
        intraday_interval="1m",
    ):
        daily = self.get_history(symbol, period=period, interval="1d")
        intraday = self.get_history(
            symbol,
            period=intraday_period,
            interval=intraday_interval,
        )

        if daily.empty or intraday.empty:
            return daily, None

        intraday = intraday.dropna(subset=["Close"])

        if intraday.empty:
            return daily, None

        session_date = intraday.index[-1].date()
        session_rows = intraday[
            pd.Series(intraday.index.date, index=intraday.index) == session_date
        ]

        if session_rows.empty:
            return daily, None

        partial_day = self._build_partial_daily_row(session_rows)
        session_timestamp = session_rows.index[-1]
        daily = daily[daily.index.date < session_date]
        daily.loc[pd.Timestamp(session_date), partial_day.index] = partial_day
        daily = daily.sort_index()

        return daily, session_timestamp
    
    def get_price(self, symbol):
        data = yf.Ticker(symbol).history(period="1d")

        if data.empty:
            return None
        
        return float(data["Close"].iloc[-1])

    def _build_partial_daily_row(self, intraday):
        values = {
            "Open": float(intraday["Open"].iloc[0]),
            "High": float(intraday["High"].max()),
            "Low": float(intraday["Low"].min()),
            "Close": float(intraday["Close"].iloc[-1]),
        }

        if "Volume" in intraday.columns:
            values["Volume"] = float(intraday["Volume"].sum())

        return pd.Series(values)
