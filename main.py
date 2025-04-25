import os
import csv
from datetime import datetime
from alice_blue import AliceBlue

# === Trade Logging ===
def log_trade_to_csv(timestamp, action, symbol, price, quantity, sl, tp, tsl, status):
    file_path = "trades.csv"
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Action", "Symbol", "Price", "Quantity", "StopLoss", "TakeProfit", "TrailingSL", "Status"])
        writer.writerow([timestamp, action, symbol, price, quantity, sl, tp, tsl, status])

# === Alice Blue Login ===
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

# === Example Trade Execution + Logging ===
def execute_trade():
    alice = login()
    symbol = "NIFTY"
    quantity = 75
    price = 200.5
    sl = 5  # percent
    tp = 999  # percent
    tsl = 2  # percent
    status = "EXECUTED"

    log_trade_to_csv(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        action="BUY",
        symbol=symbol,
        price=price,
        quantity=quantity,
        sl=sl,
        tp=tp,
        tsl=tsl,
        status=status
    )
    print(f"✅ Trade for {symbol} logged at {price}")

if __name__ == "__main__":
    execute_trade()
