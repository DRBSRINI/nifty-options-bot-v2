import os
import time
import pytz
import logging
import datetime as dt
from threading import Thread
from flask import Flask
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from pyotp import TOTP

# ========== Flask Server for Render Health Checks ==========
app = Flask(__name__)

@app.route('/health')
def health_check():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

# ========== Constants ==========
ENTRY_START = dt.time(9, 15)    # 9:15 AM IST
ENTRY_END = dt.time(15, 30)     # 3:30 PM IST
MAX_TRADES_PER_DAY = 5
IST = pytz.timezone("Asia/Kolkata")

# ========== Logging Setup ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Environment Validation ==========
REQUIRED_ENV_VARS = {
    "ALICE_USERNAME": "Alice Blue username",
    "ALICE_PASSWORD": "Alice Blue password",
    "TOTP_SECRET": "TOTP secret key",
    "ALICE_API_SECRET": "Alice Blue API secret",
    "ALICE_APP_ID": "Alice Blue app ID",
    "TELEGRAM_BOT_TOKEN": "Telegram bot token",
    "TELEGRAM_CHAT_ID": "Telegram chat ID"
}

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    error_msg = "Missing environment variables:\n" + "\n".join(missing_vars)
    raise EnvironmentError(error_msg)

# ========== Global Config ==========
telegram_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
trade_counts = {'CE': 0, 'PE': 0}

# ========== Telegram Functions ==========
def send_alert(message):
    try:
        telegram_bot.send_message(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            text=f"[{dt.datetime.now(IST).strftime('%H:%M')}] {message}"
        )
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")

# ========== Alice Blue Auth ==========
def get_alice_session():
    try:
        totp = TOTP(os.getenv("TOTP_SECRET")).now()
        logger.info("Initiating Alice Blue login...")
        
        session_id = AliceBlue.login_and_get_sessionID(
            username=os.getenv("ALICE_USERNAME"),
            password=os.getenv("ALICE_PASSWORD"),
            twoFA=totp,
            api_secret=os.getenv("ALICE_API_SECRET"),
            app_id=os.getenv("ALICE_APP_ID"),
            timeout=10
        )
        
        send_alert("✅ Login successful")
        return AliceBlue(session_id=session_id, username=os.getenv("ALICE_USERNAME"))
    
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        send_alert(f"🔴 Critical login failure: {str(e)}")
        raise

# ========== Trading Logic ==========
def reset_trades():
    global trade_counts
    trade_counts = {'CE': 0, 'PE': 0}
    send_alert("🔄 Daily trade counters reset")
    logger.info("Trade counters reset")

def execute_trades(alice):
    now = dt.datetime.now(pytz.utc).astimezone(IST)
    current_time = now.time()
    
    if not (ENTRY_START <= current_time <= ENTRY_END):
        logger.info("Outside trading hours")
        return

    # Mock trading logic
    for option_type in ['CE', 'PE']:
        if trade_counts[option_type] < MAX_TRADES_PER_DAY:
            trade_counts[option_type] += 1
            alert_msg = f"🔔 Mock {option_type} order placed (Total: {trade_counts[option_type]}/{MAX_TRADES_PER_DAY})"
            send_alert(alert_msg)
            logger.info(alert_msg)

# ========== Scheduler Setup ==========
def init_scheduler():
    scheduler = BackgroundScheduler(timezone=IST)
    
    # Main trading schedule
    scheduler.add_job(
        lambda: execute_trades(get_alice_session()),
        'cron',
        day_of_week='mon-fri',
        hour='9-15',
        minute='15,30,45'
    )
    
    # Daily reset
    scheduler.add_job(
        reset_trades,
        'cron',
        day_of_week='mon-fri',
        hour=15,
        minute=30
    )
    
    # System health ping
    scheduler.add_job(
        lambda: send_alert("🏥 System heartbeat: Normal"),
        'interval',
        minutes=30
    )
    
    scheduler.start()
    return scheduler

# ========== Main Execution ==========
if __name__ == "__main__":
    try:
        # Start Flask server in background
        Thread(target=run_flask).start()
        
        # Initialize trading system
        send_alert("🚀 Trading system initializing...")
        scheduler = init_scheduler()
        send_alert("✅ System operational - Monitoring markets")
        
        # Keep main thread alive
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        send_alert("🛑 Manual shutdown initiated")
        logger.info("Shutdown by user")
    except Exception as e:
        send_alert(f"🔥 Critical failure: {str(e)}")
        logger.error(f"System crash: {str(e)}")
        raise
