# main.py

import os
import json
import time
import logging
import pyotp
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ENV Variables
USER_ID = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
APP_ID = os.getenv("ALICE_APP_ID")
API_SECRET = os.getenv("ALICE_API_SECRET")
TOTP_SECRET = os.getenv("ALICE_TWO_FA")

def generate_totp():
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.now()

def alice_login():
    logger.info("🔐 Starting Alice Blue TOTP Login...")

    otp = generate_totp()
    logger.info(f"🔑 Generated TOTP: {otp}")

    try:
        # Step 1: Encrypt password
        url_enc = f"https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/customer/getAPIEncpkey"
        r_enc = requests.get(url_enc)
        enc_key = r_enc.json()["encKey"]
        logger.info("✅ Encryption key fetched")

        # Step 2: Send login request
        url_login = f"https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/customer/login"
        headers = {"Content-Type": "application/json"}
        payload = {
            "userId": USER_ID,
            "userData": {
                "app_id": APP_ID,
                "api_secret": API_SECRET,
                "password": PASSWORD,
                "totp": otp
            }
        }

        res = requests.post(url_login, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            if data.get("stat") == "Ok":
                session_id = data.get("susertoken")
                logger.info("✅ Login successful, session ID obtained.")
                return session_id
            else:
                logger.error(f"Login failed response: {data}")
        else:
            logger.error(f"Login failed, status {res.status_code}")
    except Exception as e:
        logger.error(f"Login failed with error: {e}")
    return None

def run_trading_logic():
    now = datetime.now().strftime("%H:%M:%S")
    logger.info(f"⚙️ Trading logic running at {now}")

def run_bot():
    session_token = alice_login()
    if not session_token:
        logger.error("❌ Bot stopped due to failed login.")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_trading_logic, 'interval', minutes=1)
    scheduler.start()

    logger.info("🤖 Bot Started and running!")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("🛑 Bot Stopped")

if __name__ == "__main__":
    run_bot()
