import os
import datetime
import time
from alice_blue import AliceBlue

# === Load environment variables ===
password = os.getenv("ALICE_PASSWORD")
two_fa = os.getenv("ALICE_TWO_FA")
app_id = os.getenv("ALICE_APP_ID")
api_secret = os.getenv("ALICE_API_SECRET")
user_id = os.getenv("ALICE_USER_ID")

# === Trade Configuration ===
MAX_CAPITAL = 70000
LOT_SIZE = 75  # Nifty
MAX_TRADES_PER_SIDE = 5
SL_PERCENT = 5
TSL_PERCENT = 2
TP_PERCENT = 999
START_TIME = datetime.time(9, 30)
END_TIME = datetime.time(15, 15)

trade_count = {"CE": 0, "PE": 0}

# === Login ===
def login():
    password = os.getenv("ALICE_PASSWORD")
    two_fa = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    user_id = os.getenv("ALICE_USER_ID")

    print("DEBUG:", password, two_fa, app_id, api_secret, user_id)  # Optional debug

    session_id = AliceBlue.login_and_get_sessionID(
        password,
        two_fa,
        app_id,
        api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id, is_2fa=True)
    print("✅ Logged in")
    return alice


# === Determine Weekly Expiry ===
def get_weekly_expiry():
    today = datetime.date.today()
    days_ahead = (3 - today.weekday() + 7) % 7  # Thursday
    expiry = today + datetime.timedelta(days=days_ahead or 7)
    return expiry.strftime("%y%m%d")

# === Round spot to nearest 50 ===
def round_to_nearest_50(n):
    return int(round(n / 50.0)) * 50

# === Get dynamic CE/PE instrument ===
def get_option_instrument(alice, strike, option_type):
    expiry = get_weekly_expiry()
    symbol = f"NIFTY{expiry}{strike}{option_type}"
    return alice.get_instrument_for_fno(symbol=symbol, exchange="NFO")

# === Multitimeframe mock (replace with real logic or TradingView webhook integration) ===
def momentum_check():
    return True  # Always true for demo; replace with real multitimeframe condition

# === Place order ===
def place_order(alice, instrument, side):
    global trade_count
    if trade_count[side] >= MAX_TRADES_PER_SIDE:
        print(f"🚫 Max {side} trades reached.")
        return

    capital_per_trade = MAX_CAPITAL // LOT_SIZE
    order = alice.place_order(
        transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
        instrument=instrument,
        quantity=LOT_SIZE,
        order_type=AliceBlue.ORDER_TYPE_MARKET,
        product_type=AliceBlue.PRODUCT_INTRADAY,
        price=0.0,
        trigger_price=None,
        stop_loss=None,
        square_off=None,
        trailing_sl=None,
        is_amo=False
    )
    trade_count[side] += 1
    print(f"✅ Order placed for {side}: {order['norenordno']}")

# === Main logic ===
def run_bot():
    alice = login()
    while True:
        now = datetime.datetime.now().time()
        if now < START_TIME or now > END_TIME:
            print("⏳ Outside trading time window.")
            time.sleep(60)
            continue

        if momentum_check():
            spot = alice.get_instrument_by_symbol("NSE", "NIFTY")
            ltp = alice.get_ltp(spot)["ltp"]
            strike = round_to_nearest_50(ltp)

            if trade_count["CE"] < MAX_TRADES_PER_SIDE:
                ce_instrument = get_option_instrument(alice, strike, "CE")
                place_order(alice, ce_instrument, "CE")

            if trade_count["PE"] < MAX_TRADES_PER_SIDE:
                pe_instrument = get_option_instrument(alice, strike, "PE")
                place_order(alice, pe_instrument, "PE")

        time.sleep(60)

if __name__ == "__main__":
    run_bot()
