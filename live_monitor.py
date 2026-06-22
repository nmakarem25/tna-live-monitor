import yfinance as yf
import time
from datetime import datetime, time as dtime
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ticker = "TNA"
interval = "1h"
check_every_minutes = 8
log_file = "tna_monitor.log"

last_alerted_candle = None

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} [{level}] - {message}"
    print(full_message, flush=True)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("Telegram credentials missing.", "ERROR")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log_message(f"Telegram error: {e}", "ERROR")
        return False

def get_daily_summary():
    try:
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False)
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        above_ema50 = "Above" if close_price > ema50 else "Below"
        
        summary = (
            f"📊 <b>TNA Daily Summary</b>\n\n"
            f"<b>Time:</b> {datetime.now().strftime('%H:%M')}\n"
            f"<b>Close:</b> ${close_price:.2f}\n"
            f"<b>EMA50:</b> ${ema50:.2f} ({above_ema50})\n"
            f"<b>EMA20:</b> ${ema20:.2f}\n"
            f"<b>AO:</b> {ao:.2f}\n\n"
            f"Monitoring is active."
        )
        return summary
    except Exception as e:
        return f"Error generating daily summary: {e}"

print("Starting TNA monitor with Daily Summaries...\n", flush=True)
log_message("Monitor started")

send_telegram_message("✅ <b>TNA Monitor Active</b>\nDaily summaries at 3:55 PM & 7:55 PM ET enabled.")

while True:
    now = datetime.now()
    
    # Daily Summaries at 3:55 PM and 7:55 PM ET
    if now.hour == 15 and now.minute == 55:
        summary = get_daily_summary()
        send_telegram_message(summary)
        time.sleep(60)  # Prevent multiple sends in the same minute
    
    if now.hour == 19 and now.minute == 55:
        summary = get_daily_summary()
        send_telegram_message(summary)
        time.sleep(60)
    
    try:
        df = yf.download(tickers=ticker, period="60d", interval=interval, progress=False)
        close_price = float(df['Close'].values.flatten()[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().values.flatten()[-1])
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().values.flatten()[-1])
        ao = float((df['Close'].rolling(5).mean() - df['Close'].rolling(34).mean()).values.flatten()[-1])
        
        current_candle_time = df.index[-1]
        
        log_message(f"Close: ${close_price:.2f} | EMA50: ${ema50:.2f} | EMA20: ${ema20:.2f} | AO: {ao:.2f}")
        
        # One alert per 1H candle
        if close_price > ema50 and current_candle_time != last_alerted_candle:
            alert_msg = (
                f"🚨 <b>ALERT - Price Above EMA50</b>\n\n"
                f"<b>Time:</b> {current_candle_time.strftime('%H:%M')}\n"
                f"<b>Price:</b> ${close_price:.2f}\n"
                f"<b>EMA50:</b> ${ema50:.2f}\n"
                f"<b>AO:</b> {ao:.2f}"
            )
            log_message(alert_msg, "ALERT")
            send_telegram_message(alert_msg)
            last_alerted_candle = current_candle_time
        
        time.sleep(check_every_minutes * 60)
        
    except Exception as e:
        log_message(f"Main loop error: {e}", "ERROR")
        time.sleep(60)
