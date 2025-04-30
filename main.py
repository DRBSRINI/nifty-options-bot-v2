import os
import pytz
import time
import pyotp
import logging
from datetime import datetime
from alice_blue import AliceBlue
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# ========== CONFIG ========== #
LIVE_MODE = True  # Toggle live/paper trading
CAPITAL = 70000
LOT_SIZE = 75
MAX_TRADES_PER_DAY = 5
STOPLOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_POINTS = 5
ENTRY_START = datetime.strptime("09:26:00", "%H:%M:%S").time()
ENTRY_END = datetime.strptime("15:00:00", "%H:%M:%S").time()
IST = pytz.timezone('Asia/Kolkata')

# ========== ENV VARS ========== #
USER_ID = os.getenv("ALICE_USER_ID")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_KEY = os.getenv("ALICE_TOTP")
APP_ID = os.getenv("ALICE_APP_ID")
API_SECRET = os.getenv("ALICE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== LOGGING ========== #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NiftyBot")

# ========== GLOBALS ========== #
alice = None
trade_count_ce = 0
trade_count_pe = 0
bot = Bot(token=TELEGRAM_TOKEN)

# ========== UTILITY ========== #
def send_alert(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Telegram Error: {e}")

# ========== LOGIN ========== #
def login():
    from alice_blue import AliceBlue
import pyotp
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get credentials from environment variables
username = os.getenv("ALICE_USER_ID")
password = os.getenv("ALICE_PASSWORD")
totp_secret = os.getenv("ALICE_TWO_FA")
app_id = os.getenv("ALICE_APP_ID")
api_secret = os.getenv("ALICE_API_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()
logger.info(f"Generated TOTP: {totp}")

# Perform login
try:
    session_id = AliceBlue.login_and_get_sessionID(
        username=username,
        password=password,
        twoFA=totp,
        app_id=app_id,
        api_secret=api_secret
    )
    logger.info(f"Session ID: {session_id}")
except Exception as e:
    logger.error("Login failed", exc_info=True)
    raise SystemExit("❌ Alice Blue login failed. Fix credentials or TOTP.")


# ========== STRATEGY ========== #
def get_atm_option(is_call):
    spot = float(alice.get_instrument_by_symbol("NSE", "NIFTY").ltp)
    strike = round(spot / 50) * 50
    symbol = f"NIFTY{strike}{'CE' if is_call else 'PE'}"
    return alice.get_instrument_for_fno(symbol=symbol, exchange="NFO")

def check_momentum():
    now = datetime.now(IST)
    if not (ENTRY_START <= now.time() <= ENTRY_END):
        return None

    tf_list = ["minute", "5minute", "15minute", "hour"]
    for tf in tf_list:
        hist = alice.get_historical(
            instrument=alice.get_instrument_by_symbol("NSE", "NIFTY"),
            from_datetime=now.replace(hour=9, minute=15),
            to_datetime=now,
            interval=tf
        )
        if len(hist) < 2:
            return None
        if hist[-1]['close'] <= hist[-2]['close']:
            return None
    return True

def place_order(is_call):
    global trade_count_ce, trade_count_pe
    if is_call and trade_count_ce >= MAX_TRADES_PER_DAY:
        return
    if not is_call and trade_count_pe >= MAX_TRADES_PER_DAY:
        return

    instrument = get_atm_option(is_call)
    ltp = float(instrument.ltp)
    sl = ltp - STOPLOSS_POINTS if is_call else ltp + STOPLOSS_POINTS
    tp = ltp + TARGET_POINTS if is_call else ltp - TARGET_POINTS

    if LIVE_MODE:
        order = alice.place_order(
            transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
            instrument=instrument,
            quantity=LOT_SIZE,
            order_type=AliceBlue.ORDER_TYPE_MARKET,
            product_type=AliceBlue.PRODUCT_MIS,
            price=0.0,
            trigger_price=None,
            stop_loss=STOPLOSS_POINTS,
            square_off=TARGET_POINTS,
            trailing_sl=TRAILING_SL_POINTS,
            is_amo=False
        )
    else:
        order = {"mock_order": True, "price": ltp}

    send_alert(f"📈 {'CE' if is_call else 'PE'} Order Placed @ {ltp}\nTP: {tp} SL: {sl}")
    if is_call:
        trade_count_ce += 1
    else:
        trade_count_pe += 1

# ========== BOT LOOP ========== #
def run_strategy():
    if check_momentum():
        if trade_count_ce <= trade_count_pe:
            place_order(is_call=True)
        else:
            place_order(is_call=False)

def health_check():
    now = datetime.now(IST).strftime("%H:%M:%S")
    send_alert(f"✅ Bot alive @ {now}")

# ========== RUN ========== #
def start_bot():
    login()
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(run_strategy, 'interval', minutes=1)
    scheduler.add_job(health_check, 'interval', minutes=30)
    scheduler.start()
    send_alert("🚀 Nifty Bot Started")

if __name__ == "__main__":
    start_bot()
    while True:
        time.sleep(60)
