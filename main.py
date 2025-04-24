import os
from alice_blue import AliceBlue

# Environment variables from Render
client_id = os.getenv("ALICE_CLIENT_ID")
api_key = os.getenv("ALICE_API_KEY")
api_secret = os.getenv("ALICE_API_SECRET")
user_id = os.getenv("ALICE_USER_ID")
two_fa = os.getenv("ALICE_TWO_FA")

# Login using positional arguments (required by AliceBlue SDK)
def login_and_get_sessionID(api_secret):
    return AliceBlue.login_and_get_sessionID(
        client_id,
        api_key,
        api_secret,
        two_fa
    )

# Place a real trade (MIS market order — change as needed)
def place_real_trade(symbol):
    try:
        session_id = login_and_get_sessionID(api_secret)
        print(f"✅ Logged in with session: {session_id}")

        alice = AliceBlue(user_id=user_id, session_id=session_id, is_2fa=True)

        order = alice.place_order(
            transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
            instrument=alice.get_instrument_by_symbol('NSE', symbol),
            quantity=1,  # Modify as per your lot size or capital logic
            order_type=AliceBlue.ORDER_TYPE_MARKET,
            product_type=AliceBlue.PRODUCT_INTRADAY,  # Or PRODUCT_CNC for delivery
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

# 🔧 Entry point to test login & trading
if __name__ == "__main__":
    print("🟡 Running live trade test...")
    result = place_real_trade("ITC")  # You can change this to any stock symbol
    print(result)
