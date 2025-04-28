import os
import datetime
import time
import csv
from alice_blue import AliceBlue

# ----------------- LOGIN -----------------
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
    print("✅ Successfully logged into Alice Blue")
    return alice

# ----------------- FETCH CANDLE -----------------
def get_candle_data(alice, symbol, interval, last_count=2):
    try:
        candles = alice.get_historical(
            instrument=symbol,
            from_datetime=datetime.datetime.now() - datetime.timedelta(minutes=15),
            to_datetime=datetime.datetime.now(),
            interval=interval,
            indices=True
        )
        return candles[-last_count:]
    except Exception as e:
        print(f"Error fetching candles: {e}")
        return None

# ----------------- MAIN TRADING LOGIC -----------------
def run_bot():
    alice = login()

    # Instrument fetching
    nifty_ce = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=datetime.date(2025, 4, 30), is_fut=False, strike=24300, is_CE=True)
    nifty_pe = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=datetime.date(2025, 4, 30), is_fut=False, strike=24300, is_CE=False)

    print("✅ Instruments fetched")

    while True:
        now = datetime.datetime.now().time()

        if now >= datetime.time(9, 30) and now <= datetime.time(15, 15):
            print(f"Checking market at {now}")

            # Get latest candles
            candle_1m = get_candle_data(alice, nifty_ce, "1minute")
            candle_5m = get_candle_data(alice, nifty_ce, "5minute")
            candle_15m = get_candle_data(alice, nifty_ce, "15minute")

            if candle_1m and candle_5m and candle_15m:
                c1_now = candle_1m[-1][4]
                c1_prev = candle_1m[-2][4]

                c5_now = candle_5m[-1][4]
                c5_prev = candle_5m[-2][4]

                c15_now = candle_15m[-1][4]
                c15_prev = candle_15m[-2][4]

                # Multi-timeframe check
                if c1_now > c1_prev and c5_now > c5_prev and c15_now > c15_prev:
                    print("🚀 BUY CE SIGNAL GENERATED!")

                elif c1_now < c1_prev and c5_now < c5_prev and c15_now < c15_prev:
                    print("📉 BUY PE SIGNAL GENERATED!")
                
                else:
                    print("❌ No Trade Condition Met")
            else:
                print("⚠️ Candle fetching issue")

        else:
            print("🔒 Market Closed or Outside Trade Time")

        time.sleep(60)  # Wait 1 min before checking again

# ----------------- RUN -----------------
if __name__ == "__main__":
    run_bot()
