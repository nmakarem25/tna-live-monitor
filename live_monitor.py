import yfinance as yf
import time
from datetime import datetime
import os
import json
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ticker = "TNA"
interval = "1h"
check_every_minutes = 8
log_file = "tna_monitor.log"
position_file = "position.json"

trading_paused = False
last_alerted_candle = None
last_update_id = 0   # For Telegram command polling

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} [{level}] - {message}"
    print(full_message, flush=True)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def load_position():
    if os.path.exists(position_file):
        with open(position_file, "r") as f:
            return json.load(f)
    return {"shares": 0, "average_entry": 0.0}

def save_position(position):
    with open(position_file, "w") as f:
        json.dump(position, f, indent=2)

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

def check_telegram_commands():
    global last_update_id, trading_paused
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"
    try:
        response = requests.get(url, timeout=10).json()
        if response.get("ok"):
            for update in response.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "").strip().lower()
                
                if text == "/pause":
                    trading_paused = True
                    send_telegram_message("⏸️ <b>Trading PAUSED</b>\nNo new buys will be considered.")
                    log_message("Trading paused via Telegram command.", "WARNING")
                
                elif text == "/resume":
                    trading_paused = False
                    send_telegram_message("▶️ <b>Trading RESUMED</b>")
                    log_message("Trading resumed via Telegram command.")
    except Exception as e:
        log_message(f"Telegram command check error: {e}", "WARNING")

print("Starting TNA monitor (Full Version with Pause/Resume + Position Tracking)...\n", flush=True)
log_message("Monitor started")

position = load_position()
send_telegram_message("✅ <b>TNA Monitor Active</b>\nPosition tracking + Pause/Resume commands enabled.")

while True:
    check_telegram_commands()   # Check for /pause and /resume
    
    if trading_paused:
        log_message("Trading is PAUSED. Skipping monitoring cycle.", "WARNING")
        time.sleep(check_every_minutes * 60)
        continue
    
    try:
        df = yf.download(tickers=ticker, period="90d", interval=interval, progress=False)
        
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
