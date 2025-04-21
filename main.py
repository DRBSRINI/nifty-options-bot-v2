import datetime
import os
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)

scheduler = BlockingScheduler()

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

    last_alert_time = now
    next_option_type = "PE" if next_option_type == "CE" else "CE"

scheduler.add_job(send_alert, "interval", minutes=1)
scheduler.start()
