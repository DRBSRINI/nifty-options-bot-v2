import datetime
import os
from telegram import Bot
from alice_blue import AliceBlue, TransactionType, OrderType, ProductType
import pyotp
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

# === ENV SETUP ===
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)
alice_user = os.getenv("ALICEBLUE_USER_ID")
alice_password = os.getenv("ALICEBLUE_PASSWORD")
alice_totp_secret = os.getenv("ALICEBLUE_TOTP_SECRET")
api_secret = os.getenv("ALICEBLUE_API_SECRET")
alice_app_code = os.getenv("ALICEBLUE_APP_CODE")

# === AliceBlue Session ===
def get_alice_session():
    print("🔄 Starting bot... Getting AliceBlue session")
    totp = pyotp.TOTP(alice_totp_secret).now()
    print(f"✅ Generated TOTP: {totp}")
    try:
        session_id = AliceBlue.login_and_get_sessionID(
            username=alice_user,
            password=alice_password,
            twoFA=totp,
            vendor_code=alice_app_code,
            api_secret=api_secret
        )
        print(f"🟢 Raw Response from API: {session_id}")
        return AliceBlue(username=alice_user, session_id=session_id)
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise

# === TIMEZONE ===
IST = pytz.timezone("Asia/Kolkata")
scheduler = BlockingScheduler(timezone=IST)

# === Market Timing Check ===
def is_market_open():
    now = datetime.datetime.now(IST)
    if now.weekday() >= 5:
        return False
    if now.hour < 9 or (now.hour == 9 and now.minute < 16):
        return False
    if now.hour > 15 or (now.hour == 15 and now.minute >= 30):
        return False
    return True

# === GLOBAL FLAGS ===
last_alert_time = None
next_option_type = "CE"

# === Main Alert Function ===
def send_alert():
    global last_alert_time, next_option_type
    now = datetime.datetime.now(IST)

    if not is_market_open():
        return

    if last_alert_time and (now - last_alert_time).total_seconds() < 60:
        return

    strike_price = 101.25  # dummy strike
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
            print(f"✅ Order Placed: {order_id}")
        except Exception as e:
            print(f"❌ Order Failed: {e}")
    else:
        print(f"⚠️ Skipping real trade. REAL_MODE not enabled.")

    last_alert_time = now
    next_option_type = "PE" if next_option_type == "CE" else "CE"

scheduler.add_job(send_alert, "interval", minutes=1)
scheduler.start()
