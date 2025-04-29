# main.py

import os
import time
import pyotp
from alice_blue import AliceBlue

# Function to generate TOTP
def generate_totp(totp_key):
    totp = pyotp.TOTP(totp_key)
    otp = totp.now()
    print(f"DEBUG: Generated OTP = {otp}")
    return otp

# Function to login into Alice Blue
def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    totp_key = os.getenv("ALICE_TWO_FA")

    otp = generate_totp(totp_key)
    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=otp,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("✅ Successfully logged into Alice Blue!")
    return alice

# Dummy trading signal function
def generate_dummy_signals():
    while True:
        print("🔔 Dummy Signal: BUY_CE")
        time.sleep(60)

# Bot start function
def run_bot():
    alice = login()
    generate_dummy_signals()

if __name__ == "__main__":
    run_bot()
