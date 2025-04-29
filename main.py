import os
import time
import json
import pytz
import logging
import requests
import pandas as pd
from datetime import datetime
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from pyotp import TOTP
from telegram import Bot

# Set up logging
logging.basicConfig(level=logging.INFO)
IST = pytz.timezone('Asia/Kolkata')

# Environment Variables
USER_ID = os.getenv("USER_ID")
API_SECRET = os.getenv("API_SECRET")
TOTP_SECRET = os.getenv("ALICE_TWO_FA")  # Ensure this matches your environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize Telegram Bot
tg = Bot(token=BOT_TOKEN)

def send_alert(msg):
    try:
        tg.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def login():
    try:
        otp = TOTP(TOTP_SECRET).now()
        session = AliceBlue.login_and_get_sessionID(
            username=USER_ID,
            password=API_SECRET,
            twoFA=otp,
            api_secret=API_SECRET,  # use the same as password for simplicity
            app_id="ALICEBLUE"
        )
        access_token = AliceBlue.get_access_token(session)
        alice = AliceBlue(username=USER_ID, session_id=access_token)
        logging.info("✅ Login successful")
        send_alert("✅ Nifty Options Bot Logged In")
        return alice
    except Exception as e:
        logging.error(f"Login failed: {e}")
        send_alert(f"❌ Login failed: {e}")
        return None


def fetch_close(alice, symbol, tf):
    try:
        df = alice.get_historical(
            instrument=alice.get_instrument_by_symbol('NSE', symbol),
            from_datetime=datetime.now(IST).replace(hour=9, minute=15),
            to_datetime=datetime.now(IST),
            interval=tf
        )
        return df['close']
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return pd.Series()

def trade_logic():
    now = datetime.now(IST)
    if not (now.hour >= 9 and now.minute >= 30 and now.hour <= 15):
        return

    try:
        symbol = 'NIFTY'
        timeframes = ['1Minute', '5Minute', '15Minute']
        all_up = True
        for tf in timeframes:
            series = fetch_close(alice, symbol, tf)
            if len(series) < 2 or series.iloc[-1] <= series.iloc[-2]:
                all_up = False
                break

        if all_up:
            # Check 1H open < close
            hour_df = fetch_close(alice, symbol, '1Hour')
            if hour_df.iloc[-1] <= hour_df.iloc[-2]:
                return
            send_alert("🚀 All TFs green. BUY SIGNAL!")
    except Exception as e:
        logging.error(f"Trade logic error: {e}")

def health_check():
    send_alert("✅ Bot is running fine @ " + str(datetime.now(IST).strftime('%H:%M:%S')))

def run_bot():
    global alice
    alice = login()
    if alice is None:
        return

    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(run_bot, 'cron', hour=9, minute=0)  # relogin at 9:00 AM
    scheduler.add_job(health_check, 'interval', minutes=60)
    scheduler.add_job(trade_logic, 'interval', minutes=1)
    scheduler.start()

    logging.info("🚀 Bot Started")
    send_alert("🚀 Nifty Options Bot Started on Render")

if __name__ == "__main__":
    run_bot()
