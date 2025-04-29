import os
import time
import pyotp
from alice_blue import AliceBlue

import os
import pyotp
from alice_blue import AliceBlue

import os
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    # 👇 Instead of fetching TOTP, paste your manually generated OTP here
    two_fa = "123456"  # <-- IMPORTANT: Replace 123456 with your fresh 6-digit OTP generated manually

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        two_fa = "448711",
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("✅ Successfully logged into Alice Blue")
    return alice

       


def run_bot():
    alice = login()

    while True:
        print("🔄 Fetching latest NIFTY LTP...")
        try:
            nifty = alice.get_instrument_by_symbol('NSE', 'NIFTY')
            ltp = alice.get_ltp(nifty)
            print(f"🔹 NIFTY Spot LTP: {ltp['ltp']}")
        except Exception as e:
            print(f"❌ Error fetching LTP: {e}")
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
