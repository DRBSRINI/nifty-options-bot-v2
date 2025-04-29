# ✅ FINAL main.py for Nifty Options Bot with TOTP login support

import os
import time
import pyotp
import pandas as pd
from datetime import datetime
from alice_blue import AliceBlue

# --- Telegram Alert Setup ---
from telegram import Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram error: {e}")

# --- Alice Blue Login Setup ---
def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    totp_key = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    totp = pyotp.TOTP(totp_key)
    two_fa = totp.now()
    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")
    print(f"DEBUG: Generated OTP = {two_fa}")

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

# --- Load Instruments ---
def get_instruments(alice):
    return {
        f"{instrument.symbol}-{instrument.instrument_token}": instrument
        for instrument in alice.get_instruments()
        if instrument.exchange == 'NFO'
    }

# --- Core Bot Logic ---

def run_bot():
    alice = login()
    instruments_master = get_instruments(alice)

    capital = 70000  # base capital
    max_trades_per_side = 5
    ce_trades = 0
    pe_trades = 0
    last_side = None  # Alternate CE and PE

    today = datetime.now().date()
    csv_filename = f"trades_{today}.csv"

    # Setup CSV if not exist
    if not os.path.exists(csv_filename):
        df = pd.DataFrame(columns=["Date", "Time", "Symbol", "Side", "Qty", "EntryPrice", "ExitPrice", "PnL"])
        df.to_csv(csv_filename, index=False)

    print("🚀 Bot started...")

    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time < "09:30" or current_time > "15:15":
            time.sleep(30)
            continue

        # Find dynamic Nifty ATM
        spot = alice.get_ltp('NSE', 'NIFTY 50')['ltp']
        atm_strike = round(spot / 50) * 50

        expiry = datetime.now().strftime("%d%b%y").upper()
        ce_symbol = f"NIFTY{expiry}{atm_strike}CE"
        pe_symbol = f"NIFTY{expiry}{atm_strike}PE"

        ce_token = None
        pe_token = None
        for key in instruments_master.keys():
            if ce_symbol in key:
                ce_token = instruments_master[key]
            if pe_symbol in key:
                pe_token = instruments_master[key]

        if not ce_token or not pe_token:
            print("Unable to find tokens, retrying...")
            time.sleep(30)
            continue

        # Fetch LTP
        ce_ltp = alice.get_ltp(ce_token.exchange, ce_token.symbol)['ltp']
        pe_ltp = alice.get_ltp(pe_token.exchange, pe_token.symbol)['ltp']

        qty = int(capital / ce_ltp)
        qty = max(1, qty)

        # Multi-timeframe momentum check (Simple Close > Previous Close)
        latest_candle = alice.get_scrip_candle_data(ce_token.symbol, '1minute', 2)
        prev_close = latest_candle[-2]['close']
        latest_close = latest_candle[-1]['close']

        # --- ENTRY RULE ---
        if latest_close > prev_close:
            if (last_side != "CE" and ce_trades < max_trades_per_side):
                # Place CE Order
                try:
                    order_id = alice.place_order(
                        transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
                        instrument=ce_token,
                        quantity=qty,
                        order_type=AliceBlue.ORDER_TYPE_MARKET,
                        product_type=AliceBlue.PRODUCT_MIS
                    )
                    print(f"✅ CE Bought {ce_symbol} Qty={qty} at {ce_ltp}")
                    send_telegram_message(f"✅ CE Bought {ce_symbol} Qty={qty} at {ce_ltp}")
                    ce_trades += 1
                    last_side = "CE"
                    # Save to CSV
                    df = pd.read_csv(csv_filename)
                    df.loc[len(df)] = [today, current_time, ce_symbol, "BUY", qty, ce_ltp, "", ""]
                    df.to_csv(csv_filename, index=False)
                except Exception as e:
                    print(f"Order Error: {e}")
        else:
            if (last_side != "PE" and pe_trades < max_trades_per_side):
                # Place PE Order
                try:
                    order_id = alice.place_order(
                        transaction_type=AliceBlue.TRANSACTION_TYPE_BUY,
                        instrument=pe_token,
                        quantity=qty,
                        order_type=AliceBlue.ORDER_TYPE_MARKET,
                        product_type=AliceBlue.PRODUCT_MIS
                    )
                    print(f"✅ PE Bought {pe_symbol} Qty={qty} at {pe_ltp}")
                    send_telegram_message(f"✅ PE Bought {pe_symbol} Qty={qty} at {pe_ltp}")
                    pe_trades += 1
                    last_side = "PE"
                    # Save to CSV
                    df = pd.read_csv(csv_filename)
                    df.loc[len(df)] = [today, current_time, pe_symbol, "BUY", qty, pe_ltp, "", ""]
                    df.to_csv(csv_filename, index=False)
                except Exception as e:
                    print(f"Order Error: {e}")

        # Stop when max trades done
        if ce_trades >= max_trades_per_side and pe_trades >= max_trades_per_side:
            print("🎯 Target trades completed. Bot will now sleep.")
            send_telegram_message("🎯 Target trades completed. Bot sleeping.")
            time.sleep(3600)

        time.sleep(60)

if __name__ == "__main__":
    run_bot()
