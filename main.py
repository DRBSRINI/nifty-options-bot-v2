import os
from alice_blue import AliceBlue

# Load credentials from Render environment
api_secret = os.getenv("ALICE_API_SECRET")
user_id = os.getenv("ALICE_USER_ID")
two_fa = os.getenv("ALICE_TWO_FA")

# Step 1: Login using ONLY api_secret (as per Alice Blue v2 SDK)
def login_and_get_sessionID(api_secret):
    return AliceBlue.login_and_get_sessionID(api_secret)

# Step 2: Place real trade (update quantity/symbol as needed)
def place_real_trade(symbol):
    try:
        session_id = login_and_get_sessionID(api_secret)
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

# Step 3: Test on startup
if __name__ == "__main__":
    print("🟡 Running live trade test...")
    result = place_real_trade("ITC")  # You can change this symbol
    print(result)
