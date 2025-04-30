import os
import time
import pytz
import logging
import datetime
import csv
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from pyotp import TOTP
from alice_blue import Instrument, OrderType, TransactionType, ProductType, Variety

# ========== Logging ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NiftyBot")

# ========== ENV Variables ==========
USERNAME = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_SECRET = os.getenv("ALICE_TOTP")
API_SECRET = os.getenv("ALICE_API_SECRET")
APP_ID = os.getenv("ALICE_APP_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

# ========== Bot Constants ==========
MAX_TRADES_PER_DAY = 5
ENTRY_START = datetime.datetime.strptime("09:26:00", "%H:%M:%S").time()
ENTRY_END = datetime.datetime.strptime("15:00:00", "%H:%M:%S").time()
IST = pytz.timezone("Asia/Kolkata")
STOPLOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_POINTS = 5
TRADE_LOG_FILE = "trade_log.csv"

# ========== Globals ==========
alice = None
trade_count_ce = 0
trade_count_pe = 0

# ========== Telegram ==========
def send_telegram_message(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

# ========== CSV Logger ==========
def log_trade(symbol, action, price, status):
    with open(TRADE_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            action,
            price,
            status
        ])

def send_daily_summary():
    try:
        if not os.path.exists(TRADE_LOG_FILE):
            send_telegram_message("📉 No trades were executed today.")
            return

        today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        with open(TRADE_LOG_FILE, mode='r') as file:
            lines = file.readlines()
        today_trades = [line for line in lines if today in line]
        if not today_trades:
            send_telegram_message("📉 No trades were executed today.")
            return

        message = "📊 *Today's Trade Summary*\n"
        for line in today_trades:
            parts = line.strip().split(',')
            message += f"{parts[0]} | {parts[1]} | {parts[2]} @ {parts[3]} | {parts[4]}\n"
        send_telegram_message(message)
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")

# ========== Login ==========
# (unchanged login function here)

# ========== Strategy Execution ==========
# (unchanged strategy-related functions here)

# ========== Scheduler ==========
scheduler = BackgroundScheduler()
scheduler.add_job(run_bot, 'interval', minutes=1, timezone=IST)
scheduler.add_job(health_check, 'cron', hour=11, minute=0, timezone=IST)
scheduler.add_job(send_daily_summary, 'cron', hour=15, minute=20, timezone=IST)
scheduler.start()

logger.info("🚀 Nifty Options Bot Started")
send_telegram_message("🚀 Nifty Options Bot Started on Render")

# ========== Keep Alive ==========
while True:
    time.sleep(60)

