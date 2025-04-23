import os
import datetime
import pytz
import pyotp
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from alice_blue import AliceBlue, TransactionType, OrderType, ProductType

# --- Load Environment Variables ---
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
alice_user = os.getenv("ALICEBLUE_USER_ID")
alice_password = os.getenv("ALICEBLUE_PASSWORD")
alice_app_code = os.getenv("ALICEBLUE_APP_CODE")
alice_totp_secret = os.getenv("ALICEBLUE_TOTP_SECRET")
api_secret = os.getenv("ALICEBLUE_API_SECRET")

# --- Setup Telegram Bot ---
bot = Bot(token=bot_token)

# --- Get AliceBlue Session ---
def get_alice_session():
    print("\U0001F504 Starting bot... Getting AliceBlue session")
    totp = pyotp.TOTP(alice_totp_secret).now()
    print(f"\u2705 Generated TOTP: {totp}")
    try:
        session_id = AliceBlue.login_and_get_sessionID(
            username=alice_user,
            password=alice_password,
            twoFA=totp,
            vendor_code=alice_app_code,
            api_secret=api_secret
        )
        print(f"\U0001F7E2 Raw Response from API: {session_id}")
        return AliceBlue(username=alice_user, session_id=session_id)
    except Exception as e:
        print(f"\u274C Login failed: {e}")
        raise

# --- Timezone & Scheduler ---
IST = pytz.timezone("Asia/Kolkata")
scheduler = BlockingScheduler(timezone=IST)

# --- Market Alert Logic ---
last_alert_time = None
next_option_type = "CE"

def is_market_open():
    now = datetime.datetime.now(IST)
    return now.weekday() < 5 and datetime.time(9, 16) <= now.time() <= datetime.time(14, 59)

def send_alert():
    global last_alert_time, next_option_type

    now = datetime.datetime.now(IST)
    if not is_market_open():
        return
    if last_alert_time and (now - last_alert_time).total_seconds() < 60:
        return

    strike_price = 101.25  # Dummy fixed value
    option_symbol = "NIFTY"
    option_type = "CE" if next_option_type == "CE" else "PE"
    order_symbol = f"{option_symbol}{option_type}"

    if os.getenv("REAL_MODE", "false").lower() == "true":
        alice = get_alice_session()
        try:
            order_id = alice.place_order(
                transaction_type=TransactionType.Buy,
                instrument=alice.get_instrument_by_symbol("NFO", order_symbol),
                quantity=75,
                order_type=OrderType.Market,
                product_type=ProductType.Intraday,
                price=0.0,
                trigger_price=None,
                stop_loss=None,
                square_off=None,
                trailing_sl=None,
                is_amo=False
            )
            print(f"\u2705 Order Placed: {order_id}")
        except Exception as e:
            print(f"\u274C Order Failed: {e}")
    else:
        print("\u26A1 REAL_MODE is FALSE: No order placed")

    last_alert_time = now
    next_option_type = "PE" if next_option_type == "CE" else "CE"

scheduler.add_job(send_alert, "interval", minutes=1)
scheduler.start()
