import yfinance as yf
import time
from datetime import datetime

ticker = "TNA"
interval = "1h"
check_every_minutes = 8
alert_level = 70.05
log_file = "tna_monitor.log"

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} - {message}"
    print(full_message, flush=True)          # Added flush=True
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

print("Starting TNA monitor with flush=True...\n", flush=True)
log_message("Monitor started")

while True:
    try:
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False)
        
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        message = f"Close: ${close_price:.2f} | EMA50: ${ema50:.2f} | EMA20: ${ema20:.2f} | AO: {ao:.2f}"
        log_message(message)
        
        if close_price > alert_level:
            alert_msg = f">>> ALERT: Price ${close_price:.2f} is above ${alert_level} (EMA50 level)"
            log_message(alert_msg)
        
        time.sleep(check_every_minutes * 60)
        
    except Exception as e:
        log_message(f"Error: {e}")
        time.sleep(60)
