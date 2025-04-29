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
    logger.info("Starting Alice Blue TOTP Login...")
    otp = generate_otp(ALICE_TWO_FA)
    logger.info(f"Generated TOTP: {otp}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=ALICE_USER_ID,
        password=ALICE_PASSWORD,
        twoFA=otp,
        api_secret=ALICE_API_SECRET,
        app_id=ALICE_APP_ID
    )

    alice = AliceBlue(
        username=ALICE_USER_ID,
        session_id=session_id
    )
    logger.info("✅ Login successful")
    return alice

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
