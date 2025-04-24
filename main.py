import os
from alice_blue import AliceBlue

# Load credentials from environment
password = os.getenv("ALICE_PASSWORD")
two_fa = os.getenv("ALICE_TWO_FA")
app_id = os.getenv("ALICE_APP_ID")
api_secret = os.getenv("ALICE_API_SECRET")
user_id = os.getenv("ALICE_USER_ID")

# Step 1: Login using all 4 required values
def login_and_get_sessionID():
    return AliceBlue.login_and_get_sessionID(
        password,
        two_fa,
        app_id,
        api_secret
    )

# Step 2: Place a real trade
def place_real_trade(symbol):
    try:
        session_id = login_and_get_sessionID()
        print(f"✅ Logged in with session: {session_id}")

        alice = AliceBlue(user_id=user_id, session_id=session_id, is_2fa=True)

        order = alice.place_order(
            transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
            instrument=alice.get_instrument_by_symbol('NSE', symbol),
            quantity=1,
            order_type=AliceBlue.ORDER_TYPE_MARKET,
            product_type=AliceBlue.PRODUCT_INTRADAY,
            price=0.0,
            trigger_price=None,
            stop_loss=None,
            square_off=None,
            trailing_sl=None,
            is_amo=False
        )

        return f"✅ Order placed: {order['norenordno']}"

    except Exception as e:
        print(f"❌ Trade failed: {e}")
        return str(e)

# Test entry point
if __name__ == "__main__":
    print("🟡 Running live trade test...")
    result = place_real_trade("ITC")
    print(result)
