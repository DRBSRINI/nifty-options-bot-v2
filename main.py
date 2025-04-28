import os
import time
import pyotp
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    two_fa_secret = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    if not all([user_id, password, two_fa_secret, app_id, api_secret]):
        raise Exception("❌ Missing environment variable. Check Render dashboard Environment settings.")

    # Generate dynamic TOTP from secret
    totp = pyotp.TOTP(two_fa_secret)
    two_fa = totp.now()

    print(f"DEBUG: Logging in with user_id={user_id}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=two_fa,
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
