import yfinance as yf
import time
from datetime import datetime

ticker = "TNA"
interval = "1h"
check_every_minutes = 5

print(f"Starting upgraded live monitor for {ticker}...\n")

while True:
    try:
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False)
        
        # Most stable extraction method right now
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker} Update:")
        print(f"  Close: ${close_price:.2f} | EMA50: ${ema50:.2f} | EMA20: ${ema20:.2f} | AO: {ao:.2f}")
        
        if close_price > 70.05:
            print("  >>> ALERT: Price above $70.05 (EMA50 level) <<<")
        
        print("-" * 55)
        time.sleep(check_every_minutes * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)