import os
import pyotp
import requests
import json
import time

def login_aliceblue():
    print("🚀 Starting Alice Blue TOTP Login...")

    # Load credentials from environment
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    two_fa_secret = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    # Generate TOTP
    totp = pyotp.TOTP(two_fa_secret).now()
    print(f"✅ Generated TOTP: {totp}")

    login_url = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/customer/login"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "userId": user_id,
        "userData": {
            "password": password,
            "twoFA": totp,
            "vendorCode": user_id,
            "apiKey": app_id,
            "source": "API",
            "userId": user_id
        }
    }

    try:
        response = requests.post(login_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "Success":
            print("✅ Login successful!")
            return data["sessionID"]
        else:
            print("❌ Login failed:", data)
            return None

    except Exception as e:
        print("🔥 Exception during login:", e)
        return None


def run_bot():
    session_id = login_aliceblue()
    if not session_id:
        print("❌ Login failed, bot stopping.")
        return

    print("📡 Bot logic would start here using session ID:", session_id)
    # TODO: Add trading logic here using session_id


if __name__ == "__main__":
    run_bot()
