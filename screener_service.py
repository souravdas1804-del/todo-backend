import yfinance as yf
import pandas as pd
import numpy as np

# Universe of representative Nifty 50 tickers
NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS",
    "HINDUNILVR.NS", "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS"
]

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def run_screener():
    results = []
    
    # Download past 6 months to ensure sufficient data for 50-day SMA & RSI
    data = yf.download(
        tickers=NIFTY_SYMBOLS,
        period="6mo",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False
    )
    
    for symbol in NIFTY_SYMBOLS:
        try:
            df = data[symbol].dropna()
            if len(df) < 50:
                continue

            # Indicators
            df["SMA_20"] = df["Close"].rolling(window=20).mean()
            df["SMA_50"] = df["Close"].rolling(window=50).mean()
            df["RSI"] = calculate_rsi(df["Close"], period=14)

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            price = round(float(latest["Close"]), 2)
            prev_price = round(float(prev["Close"]), 2)
            change_pct = round(((price - prev_price) / prev_price) * 100, 2)
            rsi = round(float(latest["RSI"]), 2) if not np.isnan(latest["RSI"]) else None
            sma_20 = round(float(latest["SMA_20"]), 2)
            sma_50 = round(float(latest["SMA_50"]), 2)
            volume = int(latest["Volume"])

            # Signal categorization
            signal = "Neutral"
            if rsi and rsi < 35:
                signal = "Oversold"
            elif rsi and rsi > 70:
                signal = "Overbought"
            elif price > sma_20 and sma_20 > sma_50:
                signal = "Bullish Trend"
            elif price < sma_20 and sma_20 < sma_50:
                signal = "Bearish Trend"

            results.append({
                "ticker": symbol.replace(".NS", ""),
                "exchange": "NSE",
                "price": price,
                "change_pct": change_pct,
                "volume": volume,
                "rsi": rsi,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "signal": signal,
            })
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            continue

    return results