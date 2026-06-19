import yfinance as yf
import time
from datetime import datetime
import os
import requests

# Environment Variables (from Render)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ticker = "TNA"
interval = "1h"
check_every_minutes = 8
alert_level = 70.05
log_file = "tna_monitor.log"

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} - {message}"
    print(full_message, flush=True)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("Telegram credentials not found in environment variables.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log_message(f"Failed to send Telegram message: {e}")

print("Starting TNA monitor with Telegram notifications...\n", flush=True)
log_message("Monitor started")

while True:
    try:
        df = yf.download(tickers=ticker, period="30d", interval=interval, progress=False)
        
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        message = f"Close: ${close_price:.2f} | EMA50: ${ema50:.2f} | EMA20: ${ema20:.2f} | AO: {ao:.2f}"
        log_message(message)
        
        # Send alert via Telegram
        if close_price > alert_level:
            alert_msg = f"🚨 <b>ALERT</b>\nPrice: ${close_price:.2f} is above ${alert_level}\nEMA50: ${ema50:.2f} | AO: {ao:.2f}"
            log_message(alert_msg)
            send_telegram_message(alert_msg)
        
        time.sleep(check_every_minutes * 60)
        
    except Exception as e:
        log_message(f"Error: {e}")
        time.sleep(60)
