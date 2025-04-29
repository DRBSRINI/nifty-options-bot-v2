import os
import time
import logging
import pyotp
import pandas as pd
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Load environment variables
ALICE_USER_ID = os.getenv("ALICE_USER_ID")
ALICE_PASSWORD = os.getenv("ALICE_PASSWORD")
ALICE_TWO_FA_KEY = os.getenv("ALICE_TWO_FA")
ALICE_API_SECRET = os.getenv("ALICE_API_SECRET")
ALICE_APP_ID = os.getenv("ALICE_APP_ID")

# TOTP Generator
def generate_totp():
    return pyotp.TOTP(ALICE_TWO_FA_KEY).now()

# Login Function
def login():
    logging.info("Starting Alice Blue TOTP Login...")
    totp = generate_totp()
    logging.info(f"Generated TOTP: {totp}")
    access_token = AliceBlue.login_and_get_access_token(
        username=ALICE_USER_ID,
        password=ALICE_PASSWORD,
        twoFA=totp,
        api_secret=ALICE_API_SECRET,
        app_id=ALICE_APP_ID
    )
    return AliceBlue(username=ALICE_USER_ID,
                     password=ALICE_PASSWORD,
                     access_token=access_token,
                     master_contracts_to_download=['NSE', 'NFO'])

# Trade Logic (placeholder)
def run_trading_logic():
    logging.info("Running trading logic...")
    # Example check: just show time
    logging.info("Current Time: %s", time.strftime("%H:%M:%S"))

# Health Check
def health_check():
    logging.info("Bot is running... ✅")

# Main Bot Runner
def run_bot():
    try:
        alice = login()
        logging.info("Login successful ✅")

        scheduler = BackgroundScheduler()
        scheduler.add_job(run_trading_logic, 'interval', minutes=1, id='run_trading_logic')
        scheduler.add_job(health_check, 'interval', minutes=5, id='health_check')
        scheduler.start()

        logging.info("Bot Started 🚀")

        while True:
            time.sleep(60)

    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        logging.error("Bot Stopped.")

if __name__ == "__main__":
    run_bot()
