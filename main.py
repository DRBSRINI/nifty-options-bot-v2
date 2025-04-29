import os
import pyotp
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    two_fa_secret = os.getenv("ALICE_TWO_FA")  # This must be your TOTP Secret Key (not OTP directly)

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

    # Generate the dynamic TOTP from secret
    totp = pyotp.TOTP(two_fa_secret)
    otp_now = totp.now()
    print(f"DEBUG: Generated OTP = {otp_now}")

    # Login with fresh OTP
    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=otp_now,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("✅ Successfully logged into Alice Blue")
    return alice

def run_bot():
    alice = login()

    # Later you can add your signal generation + trading logic here
    while True:
        print("✅ Bot running after successful login...")
        break  # Remove this break once you add your full bot logic

if __name__ == "__main__":
    run_bot()
