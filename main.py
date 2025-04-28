import os
import time
import pyotp
from alice_blue import AliceBlue

# Login function
def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    two_fa_secret = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    # Generate dynamic TOTP code from secret
    totp = pyotp.TOTP(two_fa_secret)
    two_fa = totp.now()

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

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

# Bot main logic
def run_bot():
    alice = login()

    while True:
        print("🔄 Fetching latest NIFTY Option Prices...")

        try:
            nifty_spot = alice.get_instrument_by_symbol('NSE', 'NIFTY')
            ltp = alice.get_ltp(nifty_spot)

            print(f"NIFTY Spot LTP: {ltp['ltp']}")

            # Here you can add logic for CE/PE signals

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(60)  # Check every 1 min

if __name__ == "__main__":
    run_bot()
