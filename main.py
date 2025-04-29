import os
import datetime as dt
import pandas as pd
import pytz
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from telegram import Bot
import holidays
import pyotp

# --- CONFIGURATION ---
capital = 70000
entry_start_time = dt.time(9, 26)
entry_end_time = dt.time(15, 0)
max_trades_per_day = 5
sl_points = 50
tp_points = 25
tsl_points = 5
lot_size = 75
ist = timezone('Asia/Kolkata')

# --- TELEGRAM SETUP ---
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=telegram_bot_token)

def send_alert(msg):
    try:
        bot.send_message(chat_id=telegram_chat_id, text=msg)
    except:
        print("Failed to send Telegram message")

# --- LOGIN ---
print("\U0001F680 Logging in to Alice Blue")
alice = AliceBlue.login_and_get_sessionID(
    user_id=os.getenv("ALICE_USER_ID"),
    password=os.getenv("ALICE_PASSWORD"),
    twoFA=pyotp.TOTP(os.getenv("ALICE_TOTP")).now(),
    app_id=os.getenv("ALICE_APP_ID")
)
print("\U0001F7E2 Logged in")

# --- TRADE TRACKING ---
trade_count_ce = 0
trade_count_pe = 0

# --- INSTRUMENT FETCH ---
def get_nifty_atm_option(is_call=True):
    spot = float(alice.get_instrument_by_symbol('NSE', 'NIFTY').ltp)
    atm_strike = int(round(spot / 50) * 50)
    symbol = f"NIFTY{atm_strike}{'CE' if is_call else 'PE'}"
    return alice.get_instrument_for_fno(symbol=symbol, exchange="NFO", expiry_date=None)

# --- SIGNAL GENERATION ---
def is_signal():
    try:
        now = dt.datetime.now(ist)
        if not (entry_start_time <= now.time() <= entry_end_time):
            return None

        df_1m = pd.DataFrame(alice.get_historical(instrument="NIFTY", from_datetime=now - dt.timedelta(minutes=2), to_datetime=now, interval="minute")).tail(2)
        df_5m = pd.DataFrame(alice.get_historical(instrument="NIFTY", from_datetime=now - dt.timedelta(minutes=10), to_datetime=now, interval="5minute")).tail(2)
        df_15m = pd.DataFrame(alice.get_historical(instrument="NIFTY", from_datetime=now - dt.timedelta(minutes=30), to_datetime=now, interval="15minute")).tail(2)

        cond1 = df_1m['close'].iloc[-1] > df_1m['close'].iloc[-2]
        cond2 = df_5m['close'].iloc[-1] > df_5m['close'].iloc[-2]
        cond3 = df_15m['close'].iloc[-1] > df_15m['close'].iloc[-2]

        if cond1 and cond2 and cond3:
            return True
        return False
    except Exception as e:
        print("Signal error:", e)
        return False

# --- ORDER PLACEMENT ---
def place_order(is_call):
    global trade_count_ce, trade_count_pe
    if (is_call and trade_count_ce >= max_trades_per_day) or (not is_call and trade_count_pe >= max_trades_per_day):
        return

    instrument = get_nifty_atm_option(is_call)
    ltp = float(instrument.ltp)
    sl = ltp - sl_points if is_call else ltp + sl_points
    tp = ltp + tp_points if is_call else ltp - tp_points

    alice.place_order(
        transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
        instrument=instrument,
        quantity=lot_size,
        order_type=AliceBlue.ORDER_TYPE_MARKET,
        product_type=AliceBlue.PRODUCT_MIS,
        price=0.0,
        trigger_price=None,
        stop_loss=sl,
        square_off=tp,
        trailing_sl=tsl_points,
        is_amo=False
    )

    direction = 'CE' if is_call else 'PE'
    send_alert(f"\u2705 Trade Executed: {direction}\nEntry: {ltp}\nSL: {sl}\nTP: {tp}")
    if is_call:
        trade_count_ce += 1
    else:
        trade_count_pe += 1

# --- SCHEDULER ---
def run_bot():
    if is_signal():
        if trade_count_ce <= trade_count_pe:
            place_order(is_call=True)
        else:
            place_order(is_call=False)

def health_check():
    now = dt.datetime.now(ist).strftime("%H:%M:%S")
    send_alert(f"\uD83D\uDC8A Health Check OK at {now}")

scheduler = BackgroundScheduler()
scheduler.add_job(run_bot, 'interval', minutes=1)
scheduler.add_job(health_check, 'interval', minutes=30)
scheduler.start()

send_alert("\uD83D\uDE80 Nifty Options Bot Started Successfully")
