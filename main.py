import os
from alice_blue import AliceBlue

# --- Load credentials from environment ---
password = os.getenv("ALICEBLUE_PASSWORD")
two_fa = os.getenv("ALICE_TWO_FA")
app_id = os.getenv("ALICE_APP_ID")
api_secret = os.getenv("ALICEBLUE_API_SECRET")
user_id = os.getenv("ALICEBLUE_USER_ID")

print("DEBUG:", password, two_fa, app_id, api_secret, user_id)

def login():
    session_id = AliceBlue.login_and_get_sessionID(
        password=password,
        twoFA=two_fa,
        app_id=app_id,
        api_secret=api_secret
    )
    alice = AliceBlue(user_id=user_id, session_id=session_id, is_2fa=True)
    print("✅ Logged in")
    return alice

def run_bot():
    alice = login()
    print("🟢 Running live trade test...")
    nifty = alice.get_instrument_by_symbol("NSE", "NIFTY")
    print("NIFTY LTP:", alice.get_ltp(nifty))

if __name__ == "__main__":
    run_bot()
