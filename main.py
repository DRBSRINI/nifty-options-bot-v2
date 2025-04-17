import os
import datetime
from telegram import Bot

# Load ENV
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
paper_mode = os.getenv("PAPER_MODE", "true").lower() == "true"

# Time filtering: 9:16 AM to 2:59 PM IST
def is_within_market_time():
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    return now.time() >= datetime.time(9, 16) and now.time() <= datetime.time(14, 59)

# Simulate alternating CE/PE
state_file = "last_signal.txt"
def get_next_signal():
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last = f.read().strip()
    else:
        last = "PE"
    next_signal = "CE" if last == "PE" else "PE"
    with open(state_file, "w") as f:
        f.write(next_signal)
    return next_signal

# Telegram alert
def send_alert(message):
    if telegram_token and chat_id:
        Bot(token=telegram_token).send_message(chat_id=chat_id, text=message)

# Main loop
if __name__ == "__main__":
    if is_within_market_time():
        instrument = f"NIFTY ATM {get_next_signal()}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"🟢 Paper Trade Alert:\n{instrument} @ ₹101.25\nTime: {timestamp}"
        print(msg)
        send_alert(msg)
    else:
        print("⏱ Market closed: No alerts sent.")
