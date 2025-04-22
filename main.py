import datetime
import os
from telegram import Bot
from alice_blue import AliceBlue, TransactionType, OrderType, ProductType
import pyotp

from apscheduler.schedulers.blocking import BlockingScheduler

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)
alice_user = os.getenv("ALICEBLUE_USER_ID")
alice_password = os.getenv("ALICEBLUE_PASSWORD")
alice_app_code = os.getenv("ALICEBLUE_APP_CODE")
alice_totp_secret = os.getenv("ALICEBLUE_TOTP_SECRET")
api_secret = os.getenv("ALICEBLUE_API_SECRET")

def get_alice_session():
    totp = pyotp.TOTP(alice_totp_secret).now()
    try:
        def get_alice_session():
    totp = pyotp.TOTP(alice_totp_secret).now()
    try:
        session_id = AliceBlue.login_and_get_sessionID(
            alice_user,
            alice_password,
            alice_app_code,
            totp,
            api_secret
        )
        return AliceBlue(username=alice_user, session_id=session_id)
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise


import pytz
IST = pytz.timezone("Asia/Kolkata")

scheduler = BlockingScheduler(timezone=IST)


last_alert_time = None
next_option_type = "CE"

def is_market_open():
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # Saturday & Sunday
        return False
    if now.hour < 9 or (now.hour == 9 and now.minute < 16):
        return False
    if now.hour > 15 or (now.hour == 15 and now.minute >= 30):
        return False
    return True

def send_alert():
    global last_alert_time, next_option_type

    now = datetime.datetime.now()

    # Skip if not market time
    if not is_market_open():
        return

    # Avoid sending too frequently (set 5 min cool-down)
    if last_alert_time and (now - last_alert_time).total_seconds() < 300:
        return

    strike_price = 101.25  # Dummy value, to be replaced with logic later
    alert_message = (
        f"🟢 Paper Trade Alert:\n"
        f"NIFTY ATM {next_option_type} @ ₹{strike_price}\n"
        f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    bot.send_message(chat_id=chat_id, text=alert_message)
    print(alert_message)
    # Execute real order if REAL_MODE is enabled
if os.getenv("REAL_MODE", "false").lower() == "true":
    from alice_blue import TransactionType, OrderType, ProductType, AliceBlue


    alice = get_alice_session()

    option_symbol = "NIFTY"  # You can later make this dynamic
    strike = strike_price    # This should eventually be live value

    # Determine call or put
    option_type = "CE" if next_option_type == "CE" else "PE"
    order_symbol = f"{option_symbol}{option_type}"

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


    last_alert_time = now
    next_option_type = "PE" if next_option_type == "CE" else "CE"

scheduler.add_job(send_alert, "interval", minutes=1)
scheduler.start()
