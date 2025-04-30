import os
import time
import pytz
import logging
import datetime
import csv
from alice_blue import AliceBlue, Instrument, OrderType, TransactionType, ProductType
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from pyotp import TOTP

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
            send_telegram_message("\ud83d\udcc9 No trades were executed today.")
            return

        today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        with open(TRADE_LOG_FILE, mode='r') as file:
            lines = file.readlines()
        today_trades = [line for line in lines if today in line]
        if not today_trades:
            send_telegram_message("\ud83d\udcc9 No trades were executed today.")
            return

        message = "\ud83d\udcca *Today's Trade Summary*\n"
        for line in today_trades:
            parts = line.strip().split(',')
            message += f"{parts[0]} | {parts[1]} | {parts[2]} @ {parts[3]} | {parts[4]}\n"
        send_telegram_message(message)
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")

# ========== Login ==========
def login():
    totp = TOTP(TOTP_SECRET).now()
    logger.info("Starting Alice Blue TOTP Login...")
    session_id = AliceBlue.login_and_get_sessionID(
        username=USERNAME,
        password=PASSWORD,
        twoFA=totp,
        api_secret=API_SECRET,
        app_id=APP_ID
    )
    return AliceBlue(session_id=session_id, username=USERNAME)

# ========== Strategy Execution ==========
def run_bot():
    global alice, trade_count_ce, trade_count_pe
    try:
        if alice is None:
            alice = login()
            send_telegram_message("✅ Bot Logged In Successfully!")

        now = datetime.datetime.now(IST).time()
        if not (ENTRY_START <= now <= ENTRY_END):
            return

        df_1m = alice.get_historical_data(alice.get_instrument_by_symbol("NSE", "NIFTY"), 1, datetime.datetime.now() - datetime.timedelta(minutes=5), datetime.datetime.now())
        df_5m = alice.get_historical_data(alice.get_instrument_by_symbol("NSE", "NIFTY"), 5, datetime.datetime.now() - datetime.timedelta(minutes=30), datetime.datetime.now())
        df_15m = alice.get_historical_data(alice.get_instrument_by_symbol("NSE", "NIFTY"), 15, datetime.datetime.now() - datetime.timedelta(minutes=60), datetime.datetime.now())

        close_1m = df_1m[-1]['close']
        close_1m_prev = df_1m[-2]['close']
        close_5m = df_5m[-1]['close']
        close_5m_prev = df_5m[-2]['close']
        close_15m = df_15m[-1]['close']
        close_15m_prev = df_15m[-2]['close']

        def rsi_calc(closes, period=14):
            import numpy as np
            deltas = pd.Series(closes).diff().dropna()
            gain = deltas[deltas > 0].sum() / period
            loss = -deltas[deltas < 0].sum() / period
            rs = gain / loss if loss != 0 else 0
            return 100 - (100 / (1 + rs))

        rsi_val = rsi_calc([bar['close'] for bar in df_1m][-15:])

        if close_1m > close_1m_prev and close_5m > close_5m_prev and close_15m > close_15m_prev and 30 < rsi_val < 60:
            atm_strike = round(close_1m / 50) * 50

            if trade_count_ce < MAX_TRADES_PER_DAY:
                instrument_ce = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=None, is_fut=False, strike_price=atm_strike, option_type="CE")
                if REAL_MODE:
                    alice.place_order(
                        transaction_type=TransactionType.Buy,
                        instrument=instrument_ce,
                        quantity=75,
                        order_type=OrderType.Market,
                        product_type=ProductType.MIS,
                        price=0.0,
                        trigger_price=None,
                        stop_loss=STOPLOSS_POINTS,
                        square_off=TARGET_POINTS,
                        trailing_sl=TRAILING_SL_POINTS,
                        is_amo=False
                    )
                trade_count_ce += 1
                send_telegram_message(f"✅ CE Buy Executed: {instrument_ce.symbol}")
                log_trade(instrument_ce.symbol, "BUY CE", 0.0, "EXECUTED")

            if trade_count_pe < MAX_TRADES_PER_DAY:
                instrument_pe = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=None, is_fut=False, strike_price=atm_strike, option_type="PE")
                if REAL_MODE:
                    alice.place_order(
                        transaction_type=TransactionType.Buy,
                        instrument=instrument_pe,
                        quantity=75,
                        order_type=OrderType.Market,
                        product_type=ProductType.MIS,
                        price=0.0,
                        trigger_price=None,
                        stop_loss=STOPLOSS_POINTS,
                        square_off=TARGET_POINTS,
                        trailing_sl=TRAILING_SL_POINTS,
                        is_amo=False
                    )
                trade_count_pe += 1
                send_telegram_message(f"✅ PE Buy Executed: {instrument_pe.symbol}")
                log_trade(instrument_pe.symbol, "BUY PE", 0.0, "EXECUTED")

    except Exception as e:
        logger.error(f"Login or execution failed: {e}")
        send_telegram_message(f"❌ Login/Execution Failed: {e}")

# ========== Health Check ==========
def health_check():
    logger.info("✅ Health Check Passed - Bot is running")
    send_telegram_message("✅ Health Check: Bot is running")

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

