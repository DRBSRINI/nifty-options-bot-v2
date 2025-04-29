# main.py

import os
import time
import pytz
import json
import pyotp
import logging
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from alice_blue import AliceBlue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
APP_ID = os.getenv("ALICE_APP_ID")
API_SECRET = os.getenv("ALICE_API_SECRET")
USER_ID = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_SECRET = os.getenv("ALICE_TWO_FA")
REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

def generate_otp():
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.now()

def login():
    logger.info(f"DEBUG: Logging in with user_id={USER_ID}, app_id={APP_ID}")
    try:
        otp = generate_otp()
        logger.info(f"DEBUG: Generated OTP = {otp}")
        session = AliceBlue.login_and_get_sessionID(
            username=USER_ID,
            password=PASSWORD,
            twoFA=otp,
            app_id=APP_ID,
            api_secret=API_SECRET
        )
        logger.info("✅ Login successful.")
        return AliceBlue(username=USER_ID, session_id=session)
    except Exception as e:
        logger.error("❌ Login Failed: " + str(e))
        return None

def run_trading_logic():
    logger.info("⚙️ Running trading logic...")
    try:
        # Sample check
        now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S")
        logger.info(f"✅ Trading bot active at {now}")
    except Exception as e:
        logger.error(f"⚠️ Trading logic error: {e}")

def health_check():
    logger.info("🧠 Bot heartbeat... all systems nominal.")

def run_bot():
    alice = login()
    if alice is None:
        logger.error("🛑 Bot Stopped: Login failed.")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_trading_logic, 'interval', minutes=1, id='run_trading_logic')
    scheduler.add_job(health_check, 'interval', minutes=30, id='health_check')
    scheduler.start()
    logger.info("🤖 Bot Started 🚀")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Bot Stopped manually.")

if __name__ == "__main__":
    run_bot()
