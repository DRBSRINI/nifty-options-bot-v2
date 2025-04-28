import time
import datetime

def run_bot():
    alice = login()
    print("✅ Bot started, waiting for signals...")

    while True:
        now = datetime.datetime.now()
        if now.time() >= datetime.time(9, 16) and now.time() <= datetime.time(15, 15):
            try:
                # Step 1: Fetch latest 1-min, 5-min, 15-min candles
                instrument_ce = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=None, is_fut=False, strike_price=0, right="CE")
                instrument_pe = alice.get_instrument_for_fno(symbol="NIFTY", expiry_date=None, is_fut=False, strike_price=0, right="PE")

                hist_1m = alice.get_historical(instrument_ce, datetime.datetime.now() - datetime.timedelta(minutes=5), datetime.datetime.now(), "1Minute")
                hist_5m = alice.get_historical(instrument_ce, datetime.datetime.now() - datetime.timedelta(minutes=25), datetime.datetime.now(), "5Minute")
                hist_15m = alice.get_historical(instrument_ce, datetime.datetime.now() - datetime.timedelta(minutes=75), datetime.datetime.now(), "15Minute")

                # Step 2: Check conditions
                if (hist_1m[-1]['close'] > hist_1m[-2]['close']) and (hist_5m[-1]['close'] > hist_5m[-2]['close']) and (hist_15m[-1]['close'] > hist_15m[-2]['close']):
                    print("✅ Signal Detected: BUY CE")
                    # Here you can place CE Buy Order (Later we add)

                # Similarly check for PE signal
                hist_1m_pe = alice.get_historical(instrument_pe, datetime.datetime.now() - datetime.timedelta(minutes=5), datetime.datetime.now(), "1Minute")
                hist_5m_pe = alice.get_historical(instrument_pe, datetime.datetime.now() - datetime.timedelta(minutes=25), datetime.datetime.now(), "5Minute")
                hist_15m_pe = alice.get_historical(instrument_pe, datetime.datetime.now() - datetime.timedelta(minutes=75), datetime.datetime.now(), "15Minute")

                if (hist_1m_pe[-1]['close'] < hist_1m_pe[-2]['close']) and (hist_5m_pe[-1]['close'] < hist_5m_pe[-2]['close']) and (hist_15m_pe[-1]['close'] < hist_15m_pe[-2]['close']):
                    print("✅ Signal Detected: BUY PE")
                    # Here you can place PE Buy Order (Later we add)

            except Exception as e:
                print(f"⚠️ Error while fetching data or checking signal: {e}")

        else:
            print("⏳ Market closed or not in time range. Waiting...")
        
        time.sleep(60)  # Wait 1 minute
