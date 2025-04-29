import os
import time
import logging
import pyotp
import pandas as pd
from datetime import datetime
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
APP_ID = os.getenv("ALICE_APP_ID")
API_SECRET = os.getenv("ALICE_API_SECRET")
USER_ID = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
TWO_FA_SECRET = os.getenv("ALICE_TWO_FA")
REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

# Telegram settings (Optional)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Generate TOTP
def generate_totp(secret_key):
    totp = pyotp.TOTP(secret_key)
    return totp.now()

# Login to Alice Blue
session_id = None
def login():
    global session_id
    try:
        totp_code = generate_totp(TWO_FA_SECRET)
        logger.info(f"Generated OTP: {totp_code}")

        session = AliceBlue.login_and_get_sessionID(
            username=USER_ID,
            password=PASSWORD,
            twoFA=totp_code,
            app_id=APP_ID,
            api_secret=API_SECRET
        )
        session_id = session
        logger.info("✅ Successfully logged in to Alice Blue!")
        return AliceBlue(username=USER_ID, session_id=session, app_id=APP_ID)
    except Exception as e:
        logger.error(f"❌ Login Failed: {e}")
        return None

# Trading Logic (Dummy Placeholder)
def run_trading_logic():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[RUNNING] Trading logic at {now}")

# Health Check
def health_check():
    logger.info("✅ Bot is running fine (Health Check)")

# Main Function
def run_bot():
    alice = login()
    if alice is None:
        logger.error("Login failed. Bot Stopped.")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_trading_logic, 'interval', minutes=1)
    scheduler.add_job(health_check, 'interval', minutes=30)
    scheduler.start()

    logger.info("🚀 Bot Started")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("🛑 Bot stopped manually.")

if __name__ == "__main__":
    run_bot()
