import os
import time
import pytz
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from alice_blue import AliceBlue
import pyotp

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
ALICE_USER_ID = os.getenv("ALICE_USER_ID")
ALICE_PASSWORD = os.getenv("ALICE_PASSWORD")
ALICE_TWO_FA = os.getenv("ALICE_TWO_FA")
ALICE_API_SECRET = os.getenv("ALICE_API_SECRET")
ALICE_APP_ID = os.getenv("ALICE_APP_ID")
REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

# TOTP Generation
def generate_otp(secret):
    totp = pyotp.TOTP(secret)
    return totp.now()

# Login function
def login():
    from alice_blue import AliceBlue
import pyotp
import os

username = os.getenv("ALICE_USER_ID")
password = os.getenv("ALICE_PASSWORD")
app_id = os.getenv("ALICE_APP_ID")
api_secret = os.getenv("ALICE_API_SECRET")
totp_key = os.getenv("ALICE_TWO_FA")

# Generate TOTP
totp = pyotp.TOTP(totp_key).now()

# Login flow using new method
session = AliceBlue.login_and_get_sessionID(
    username=username,
    password=password,
    twoFA=totp,
    app_id=app_id,
    api_secret=api_secret
)

print("✅ Login session:", session)

# Trading Logic Placeholder
def run_trading_logic():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    logger.info(f"Running trade logic at {now.strftime('%H:%M:%S')}...")
    # Place your real trading logic here

# Health Check
def health_check():
    logger.info("✅ Bot is running smoothly...")

# Run Bot

def run_bot():
    try:
        alice = login()
    except Exception as e:
        logger.error(f"Login failed: {e}")
        logger.error("❌ Bot Stopped.")
        return

    # Schedule tasks
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(run_trading_logic, "interval", minutes=5, id="run_trading_logic")
    scheduler.add_job(health_check, "interval", minutes=10, id="health_check")
    scheduler.start()
    logger.info("🤖 Bot Started 🚀")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Interrupted. Shutting down bot...")
        scheduler.shutdown()

if __name__ == "__main__":
    run_bot()
