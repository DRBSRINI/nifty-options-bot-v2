import datetime
import os
import pytz
import pyotp
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram import Bot
from alice_blue import AliceBlue, TransactionType, OrderType, ProductType

# === ENV VARS ===
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
alice_user = os.getenv("ALICEBLUE_USER_ID")
alice_password = os.getenv("ALICEBLUE_PASSWORD")
alice_totp_secret = os.getenv("ALICEBLUE_TOTP_SECRET")
alice_app_code = os.getenv("ALICEBLUE_APP_CODE")  # ✅ correct key
api_secret = os.getenv("ALICEBLUE_API_SECRET")

REAL_MODE = os.getenv("REAL_MODE", "false").lower() == "true"

bot = Bot(token=bot_token)

# === AliceBlue Session ===
def get_alice_session():
    totp = pyotp.TOTP(alice_totp_secret).now()
    print(f"✅ Generated TOTP: {totp}")
    print("🔄 Starting bot... Getting AliceBlue session")

    try:
        session_id = AliceBlue.login_and_get_sessionID(
            username=alice_user,
            password=alice_password,
            twoFA=totp,
            vendor_code=alice_app_code,  # ✅ correct key name
            api_secret=api_secret
        )
        print(f"🟢 Raw Response from API: {session_id}")
        return AliceBlue(username=alice_user, session_id=session_id)
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise

# === Timezone Setup ===
IST = pytz.timezone("Asia/Kolkata")
scheduler = BlockingScheduler(timezone=IST)

# === Market Logic ===
last_alert_time = None
next_option_type = "CE"

def is_market_open():
    now = datetime.datetime.now(IST)
    return now.weekday() < 5 and datetime.time(9, 16) <= now.time() <= datetime.time(15, 30)

# === Alert + Trade ===
def send_alert():
    global last_alert_time, next_option_type

    now = datetime.datetime.now(IST)
    if not is_market_open():
        return
    if last_alert_time and (now - last_alert_time).total_seconds() < 300:
        return

    strike_price = 101.25  # Dummy value
    option_symbol = "NIFTY"
    option_type = "CE" if next_option_type == "CE" else "PE"
    order_symbol = f"{option_symbol}{option_type}"

    # Paper Alert
    alert_message = (
        f"🟢 Paper Trade Alert:\n"
        f"{option_symbol} ATM {option_type} @ ₹{strike_price}\n"
        f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    bot.send_message(chat_id=chat_id, text=alert_message)
    print(alert_message)

    # Real Order
    if REAL_MODE:
        try:
            alice = get_alice_session()
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
            print(f"✅ Order Placed: {order_id}")
        except Exception as e:
            print(f"❌ Order Failed: {e}")

    # Flip CE/PE for next time
    last_alert_time = now
    next_option_type = "PE" if next_option_type == "CE" else "CE"

# === Scheduler Start ===
scheduler.add_job(send_alert, "interval", minutes=1)
scheduler.start()
