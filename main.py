import os
import pyotp
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")
    totp_secret = os.getenv("ALICE_TWO_FA")

    # Generate dynamic OTP from TOTP key
    totp = pyotp.TOTP(totp_secret)
    otp_now = totp.now()

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")
    print(f"DEBUG: Generated OTP = {otp_now}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=otp_now,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("✅ Successfully logged into Alice Blue")
    return alice
    
    Strategy Execution
    now = datetime.datetime.now(IST).time()
    if not (ENTRY_START <= now <= ENTRY_END):
        return

    hist_data = kite.historical_data(instrument_token=256265, interval='minute', from_date=datetime.datetime.now() - datetime.timedelta(minutes=60), to_date=datetime.datetime.now())
    df = pd.DataFrame(hist_data)

    if df.empty or len(df) < 15:
        return

    close_1m = df.iloc[-1]['close']
    close_1m_prev = df.iloc[-2]['close']
    close_5m = df.iloc[-5]['close']
    close_5m_prev = df.iloc[-6]['close']
    close_15m = df.iloc[-15]['close']
    close_15m_prev = df.iloc[-16]['close']

    def rsi_calc(closes, period=14):
        deltas = pd.Series(closes).diff().dropna()
        gain = deltas[deltas > 0].sum() / period
        loss = -deltas[deltas < 0].sum() / period
        rs = gain / loss if loss != 0 else 0
        return 100 - (100 / (1 + rs))

    rsi_val = rsi_calc(df['close'].tolist()[-15:])

    if close_1m > close_1m_prev and close_5m > close_5m_prev and close_15m > close_15m_prev and 30 < rsi_val < 60:
        atm_strike = round(close_1m / 50) * 50
        price_with_buffer = round(close_1m + ORDER_BUFFER, 2)

        if trade_count_ce < MAX_TRADES_PER_DAY:
            symbol_ce = f"NIFTY{atm_strike}CE"
            if REAL_MODE:
                kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NFO,
                    tradingsymbol=symbol_ce,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=75,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    product=kite.PRODUCT_MIS,
                    price=price_with_buffer
                )
            trade_count_ce += 1
            send_telegram_message(f"✅ CE Limit Buy Executed: {symbol_ce} @ {price_with_buffer}")
            log_trade(symbol_ce, "BUY CE", price_with_buffer, "EXECUTED")

        if trade_count_pe < MAX_TRADES_PER_DAY:
            symbol_pe = f"NIFTY{atm_strike}PE"
            if REAL_MODE:
                kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NFO,
                    tradingsymbol=symbol_pe,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=75,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    product=kite.PRODUCT_MIS,
                    price=price_with_buffer
                )
            trade_count_pe += 1
            send_telegram_message(f"✅ PE Limit Buy Executed: {symbol_pe} @ {price_with_buffer}")
            log_trade(symbol_pe, "BUY PE", price_with_buffer, "EXECUTED")

except Exception as e:
    logger.error(f"Login or execution failed: {e}")
    send_telegram_message(f"❌ Login/Execution Failed: {e}")
