# ====================
# Final Corrected main.py
# ====================

import os
import time
import pyotp
from alice_blue import AliceBlue
from datetime import datetime
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Login function
def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    totp_secret = os.getenv("ALICE_TWO_FA")

    # Generate current OTP from TOTP secret
    totp = pyotp.TOTP(totp_secret)
    otp_now = totp.now()

    logging.info(f"Logging in with user_id={user_id} and app_id={app_id}")
    logging.info(f"Generated OTP: {otp_now}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=otp_now,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    logging.info("✅ Successfully logged into Alice Blue")
    return alice

# Signal Generation Function (Dummy, you can modify)
def generate_signal():
    now = datetime.now()
    current_minute = now.minute
    # Very simple fake logic: buy CE if even minute, buy PE if odd minute
    if current_minute % 2 == 0:
        return "BUY_CE"
    else:
        return "BUY_PE"

# Main Bot Loop
def run_bot():
    alice = login()
    while True:
        try:
            signal = generate_signal()
            logging.info(f"Signal generated: {signal}")
            # ✅ Here you will place order logic later

            # For now just wait 60 seconds
            time.sleep(60)
        except Exception as e:
            logging.error(f"Exception occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
