import os
import pyotp
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    totp_secret = os.getenv("ALICE_TWO_FA")

    # Generate dynamic OTP from TOTP key
    totp = pyotp.TOTP(totp_secret)
    otp_now = totp.now()

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")
    print(f"DEBUG: Generated OTP = {otp_now}")

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
