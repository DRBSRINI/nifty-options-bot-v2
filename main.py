import os
import time
import pytz
import json
import logging
import datetime as dt
import pandas as pd
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from pyotp import TOTP

# ========== Logging Setup ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ENV Variables ==========
USERNAME = os.getenv("ALICE_USERNAME")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")
API_SECRET = os.getenv("ALICE_API_SECRET")
APP_ID = os.getenv("ALICE_APP_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== Timezone ==========
IST = pytz.timezone("Asia/Kolkata")

# ========== Telegram ==========
def send_telegram_message(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

# ========== Login ==========
def login():
    totp = TOTP(TOTP_SECRET).now()
    logger.info("Starting Alice Blue TOTP Login...")
    logger.info(f"Generated TOTP: {totp}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=USERNAME,
        password=PASSWORD,
        twoFA=totp,
        api_secret=API_SECRET,
        app_id=APP_ID
    )
    print("✅ Login successful!")
    return AliceBlue(session_id=session_id, username=USERNAME)
    
# ========= STRATEGY EXECUTION ========== #
trade_count_ce = 0
trade_count_pe = 0

def run_bot():
    global trade_count_ce, trade_count_pe

    now = datetime.datetime.now(IST).time()
    if now < ENTRY_START or now > ENTRY_END:
        return

    # Example check: simulate 15m/5m/1m momentum (to be implemented)
    if trade_count_ce < MAX_TRADES_PER_DAY:
        logger.info("🔔 Entry CE condition met (mock)")
        send_alert("🔔 [MOCK] BUY NIFTY ATM CE (1 lot)")
        trade_count_ce += 1

    if trade_count_pe < MAX_TRADES_PER_DAY:
        logger.info("🔔 Entry PE condition met (mock)")
        send_alert("🔔 [MOCK] BUY NIFTY ATM PE (1 lot)")
        trade_count_pe += 1

# ========== Main Bot Logic ==========
def run_bot():
    try:
        alice = login()
        send_telegram_message("✅ Bot Logged In Successfully!")
        # Additional trading logic can be inserted here
    except Exception as e:
        logger.error(f"Login failed: {e}")
        send_telegram_message(f"❌ Login failed: {e}")

# ========== Health Check ==========
def health_check():
    logger.info("✅ Health Check Passed - Bot is running")
    send_telegram_message("✅ Health Check: Bot is running")

# ========== Scheduler Setup ==========
scheduler = BackgroundScheduler()
scheduler.add_job(run_bot, 'cron', day_of_week='mon-fri', hour=9, minute=15, timezone=IST)
scheduler.add_job(health_check, 'interval', minutes=60, timezone=IST)
scheduler.start()

logger.info("🚀 Bot Started")
send_telegram_message("🚀 Nifty Options Bot Started on Render")

# Keep alive
while True:
    time.sleep(60)
