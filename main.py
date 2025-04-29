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
        url_login = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/customer/login"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "userId": USER_ID,
            "password": PASSWORD,
            "twoFA": otp,
            "vendorCode": USER_ID,
            "apiKey": APP_ID,
            "clientID": USER_ID,
            "source": "API",
        }

        logger.info("📤 Sending login request to Alice Blue...")
        response = requests.post(url_login, headers=headers, json=payload)
        response_text = response.text.strip()

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception as json_err:
                logger.error(f"❌ JSON decode error: {json_err}")
                logger.error(f"Raw response: {response_text}")
                return None

            if data.get("stat") == "Ok":
                session_id = data.get("susertoken") or data.get("sessionID")
                logger.info("✅ Login successful.")
                return session_id
            else:
                logger.error(f"❌ Login rejected: {data}")
        else:
            logger.error(f"❌ Login failed. Status: {response.status_code}")
            logger.error(f"Raw response: {response_text}")

    except Exception as e:
        logger.error(f"❌ Login failed with error: {e}")

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
