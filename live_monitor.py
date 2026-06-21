import yfinance as yf
import time
from datetime import datetime
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ticker = "TNA"
interval = "1h"
check_every_minutes = 8
log_file = "tna_monitor.log"

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} [{level}] - {message}"
    print(full_message, flush=True)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def send_telegram_message(message, retries=3):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("Telegram credentials missing.", "ERROR")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                log_message(f"Telegram send failed (attempt {attempt+1}): {response.text}", "WARNING")
        except Exception as e:
            log_message(f"Telegram exception (attempt {attempt+1}): {e}", "WARNING")
        time.sleep(2)
    
    log_message("Failed to send Telegram message after retries.", "ERROR")
    return False

print("Starting TNA monitor (Improved v2)...\n", flush=True)
log_message("Monitor started")

# Startup message
send_telegram_message("✅ <b>TNA Monitor Active</b>\nDynamic EMA50 alerts + improved resilience enabled.")

while True:
    try:
        df = yf.download(tickers=ticker, period="60d", interval=interval, progress=False)
        
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        log_message(f"Close: ${close_price:.2f} | EMA50: ${ema50:.2f} | EMA20: ${ema20:.2f} | AO: {ao:.2f}")
        
        # Dynamic Alert
        if close_price > ema50:
            alert_msg = (
                f"🚨 <b>ALERT - Price Above EMA50</b>\n\n"
                f"<b>Time:</b> {datetime.now().strftime('%H:%M')}\n"
                f"<b>Price:</b> ${close_price:.2f}\n"
                f"<b>EMA50:</b> ${ema50:.2f}\n"
                f"<b>AO:</b> {ao:.2f}\n\n"
                f"Consider reviewing entry conditions."
            )
            log_message(alert_msg, "ALERT")
            send_telegram_message(alert_msg)
        
        time.sleep(check_every_minutes * 60)
        
    except Exception as e:
        log_message(f"Main loop error: {e}", "ERROR")
        time.sleep(60)
