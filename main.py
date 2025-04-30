import os
import json
import pytz
import pyotp
import logging
import datetime
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

# ========= STRATEGY SETTINGS ========= #
CAPITAL = 70000
LOT_SIZE = 1
MAX_TRADES_PER_DAY = 5
STOPLOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_POINTS = 5
ENTRY_START = datetime.datetime.strptime("09:26:00", "%H:%M:%S").time()
ENTRY_END = datetime.datetime.strptime("15:00:00", "%H:%M:%S").time()
IST = pytz.timezone('Asia/Kolkata')

# ========= ENV VARS ========= #
USER_ID = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_SECRET = os.getenv("ALICE_TOTP")
APP_ID = os.getenv("ALICE_APP_ID")
API_SECRET = os.getenv("ALICE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

if not TOTP_SECRET:
    raise ValueError("❌ TOTP_SECRET (ALICE_TOTP) is missing from environment variables.")

# ========= LOGGING ========= #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NiftyBot")

# ========= TELEGRAM ========== #
bot = Bot(token=TELEGRAM_TOKEN)
def send_alert(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Telegram Error: {e}")

# ========= ALICE LOGIN ========== #
def generate_totp():
    return pyotp.TOTP(TOTP_SECRET).now()

def login_to_alice():
    try:
        otp = generate_totp()
        session = AliceBlue.login_and_get_sessionID(
            username=USER_ID,
            password=PASSWORD,
            twoFA=otp,
            app_id=APP_ID,
            api_secret=API_SECRET
        )
        alice = AliceBlue(
            username=USER_ID,
            session_id=session,
            app_id=APP_ID,
            api_secret=API_SECRET
        )
        logger.info("✅ Alice Blue Login Successful")
        send_alert("✅ Bot Started & Logged in Successfully")
        return alice
    except Exception as e:
        logger.error("❌ Login failed")
        logger.error(str(e))
        send_alert("❌ Alice Blue Login Failed")
        return None

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

# ========= HEALTH CHECK ========== #
def health_check():
    send_alert("✅ Bot is alive and monitoring")

# ========= MAIN ========= #
if __name__ == "__main__":
    logger.info("🚀 Starting main.py...")
    alice = login_to_alice()

    if alice is None:
        exit(1)

    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(run_bot, 'interval', minutes=1, id='run_bot')
    scheduler.add_job(health_check, 'cron', hour=12, minute=0, id='health_check')
    scheduler.start()

    logger.info("📈 Bot Started and Scheduler Running")
    send_alert("📢 Nifty Options Bot is LIVE")
