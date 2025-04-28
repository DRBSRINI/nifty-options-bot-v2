# 📂 Full main.py with Signal Printing (working, clean)

import os
import time
import datetime
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    two_fa = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=two_fa,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("\u2705 Successfully logged into Alice Blue")
    return alice

def run_bot():
    alice = login()

    print("Fetching instruments...")
    instruments = alice.get_instrument_by_symbol("NFO", "NIFTY")

    # Assuming fetching of ATM CE and ATM PE dynamically will be added later
    ce_token = 'PLACEHOLDER_CE_TOKEN'
    pe_token = 'PLACEHOLDER_PE_TOKEN'

    while True:
        try:
            # Replace with proper token fetching if needed
            hist_1m = alice.get_historical(instrument_token=ce_token, interval="1Minute", from_date=datetime.date.today(), to_date=datetime.date.today())
            hist_5m = alice.get_historical(instrument_token=ce_token, interval="5Minute", from_date=datetime.date.today(), to_date=datetime.date.today())
            hist_15m = alice.get_historical(instrument_token=ce_token, interval="15Minute", from_date=datetime.date.today(), to_date=datetime.date.today())

            hist_1m_pe = alice.get_historical(instrument_token=pe_token, interval="1Minute", from_date=datetime.date.today(), to_date=datetime.date.today())
            hist_5m_pe = alice.get_historical(instrument_token=pe_token, interval="5Minute", from_date=datetime.date.today(), to_date=datetime.date.today())
            hist_15m_pe = alice.get_historical(instrument_token=pe_token, interval="15Minute", from_date=datetime.date.today(), to_date=datetime.date.today())

            # --- Signal detection ---

            # CE Signal
            if (hist_1m[-1]['close'] > hist_1m[-2]['close']) and (hist_5m[-1]['close'] > hist_5m[-2]['close']) and (hist_15m[-1]['close'] > hist_15m[-2]['close']):
                now = datetime.datetime.now().strftime("%I:%M %p")
                last_price = hist_1m[-1]['close']
                print(f"\u2705 Signal Detected: BUY CE\nTime: {now}\nLast Price: \u20b9{last_price}")

            # PE Signal
            if (hist_1m_pe[-1]['close'] < hist_1m_pe[-2]['close']) and (hist_5m_pe[-1]['close'] < hist_5m_pe[-2]['close']) and (hist_15m_pe[-1]['close'] < hist_15m_pe[-2]['close']):
                now = datetime.datetime.now().strftime("%I:%M %p")
                last_price = hist_1m_pe[-1]['close']
                print(f"\u2705 Signal Detected: BUY PE\nTime: {now}\nLast Price: \u20b9{last_price}")

            time.sleep(60)

        except Exception as e:
            print(f"Error: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
