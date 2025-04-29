import os
import pyotp
from alice_blue import AliceBlue

def login_aliceblue():
    print("🚀 Starting Alice Blue TOTP Login...")

    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    totp_secret = os.getenv("ALICE_TWO_FA")

    # Generate current TOTP
    totp = pyotp.TOTP(totp_secret).now()
    print("✅ Generated TOTP:", totp)

    try:
        session_id = AliceBlue.login_and_get_sessionID(
            user_id=user_id,
            password=password,
            twoFA=totp,
            app_id=app_id,
            api_secret=api_secret
        )
        print("✅ Login successful!")
        return session_id

    except Exception as e:
        print("❌ Login failed:", e)
        return None

def run_bot():
    session_id = login_aliceblue()
    if session_id:
        print("📡 Bot live. Use session ID:", session_id)
        # Your trading logic here
    else:
        print("❌ Bot stopped. Login failed.")

if __name__ == "__main__":
    run_bot()
