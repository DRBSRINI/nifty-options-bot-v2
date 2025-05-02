import os
import time
import pytz
import json
import logging
import datetime as dt
from alice_blue import AliceBlue
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from pyotp import TOTP

# ========== Logging Setup ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== ENV Variables ==========
USERNAME = os.getenv("ALICE_USERNAME")
PASSWORD = os.getenv("ALICE_PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")
API_SECRET = os.getenv("ALICE_API_SECRET")
APP_ID = os.getenv("ALICE_APP_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Trading configuration
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "2"))

# ========== Timezone ==========
IST = pytz.timezone("Asia/Kolkata")

# ========== Telegram ==========
def send_telegram_message(message):
    try:
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not configured. Message not sent.")
            return
            
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Telegram message sent: {message}")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

# ========== Login ==========
def login():
    """
    Login to Alice Blue using TOTP authentication
    """
    try:
        if not USERNAME or not PASSWORD or not TOTP_SECRET or not API_SECRET or not APP_ID:
            raise ValueError("Missing required environment variables for login")
            
        logger.info("Starting Alice Blue TOTP Login...")
        totp = TOTP(TOTP_SECRET).now()
        logger.info(f"Generated TOTP: {totp}")
        
        session_id = AliceBlue.login_and_get_sessionID(
            username=USERNAME,
            password=PASSWORD,
            twoFA=totp,
            api_secret=API_SECRET,
            app_id=APP_ID
        )
        
        logger.info("✅ Login successful!")
        send_telegram_message("✅ Successfully logged in to Alice Blue")
        
        return AliceBlue(session_id=session_id, username=USERNAME)
    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(f"❌ {error_msg}")
        raise

# ========== Trading Hours ==========
def is_market_hour():
    """Check if current time is within market trading hours"""
    now = dt.datetime.now(IST)
    
    # Check if it's a weekday (0 is Monday, 6 is Sunday)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Define market hours (9:15 AM to 3:30 PM)
    market_start = dt.time(9, 15, 0)
    market_end = dt.time(15, 30, 0)
    
    current_time = now.time()
    return market_start <= current_time <= market_end

# ========== Strategy Execution ==========
trade_count_ce = 0
trade_count_pe = 0

def run_strategy(alice):
    """Execute the trading strategy"""
    global trade_count_ce, trade_count_pe
    
    if not is_market_hour():
        logger.info("Outside market hours. Strategy not executed.")
        return
    
    try:
        logger.info("Running trading strategy...")
        
        # Here you would implement your actual trading logic
        # This is a placeholder for demonstration
        
        if trade_count_ce < MAX_TRADES_PER_DAY:
            logger.info("🔔 Entry CE condition met (mock)")
            send_telegram_message("🔔 [MOCK] BUY NIFTY ATM CE (1 lot)")
            trade_count_ce += 1
            
        if trade_count_pe < MAX_TRADES_PER_DAY:
            logger.info("🔔 Entry PE condition met (mock)")
            send_telegram_message("🔔 [MOCK] BUY NIFTY ATM PE (1 lot)")
            trade_count_pe += 1
            
    except Exception as e:
        error_msg = f"Strategy execution error: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(f"❌ {error_msg}")

# ========== Main Bot Logic ==========
def run_bot():
    """Main function to run the trading bot"""
    try:
        logger.info("Starting bot execution...")
        alice = login()
        run_strategy(alice)
    except Exception as e:
        error_msg = f"Bot execution failed: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(f"❌ {error_msg}")

# ========== Reset Daily Counters ==========
def reset_daily_counters():
    """Reset trade counters at the start of the day"""
    global trade_count_ce, trade_count_pe
    trade_count_ce = 0
    trade_count_pe = 0
    logger.info("Daily trade counters reset")
    send_telegram_message("🔄 Daily trade counters reset")

# ========== Health Check ==========
def health_check():
    """Send a health check message to confirm the bot is running"""
    logger.info("✅ Health Check Passed - Bot is running")
    send_telegram_message("✅ Health Check: Bot is running")

# ========== Main Execution ==========
if __name__ == "__main__":
    try:
        # Initial notification
        logger.info("🚀 Bot initialization started")
        send_telegram_message("🚀 Nifty Options Bot Starting on Render")
        
        # Set up the scheduler
        scheduler = BackgroundScheduler()
        
        # Schedule main trading function (9:15 AM IST on weekdays)
        scheduler.add_job(run_bot, 'cron', day_of_week='mon-fri', hour=9, minute=15, timezone=IST)
        
        # Schedule additional runs if needed
        # scheduler.add_job(run_bot, 'cron', day_of_week='mon-fri', hour=10, minute=30, timezone=IST)
        # scheduler.add_job(run_bot, 'cron', day_of_week='mon-fri', hour=13, minute=45, timezone=IST)
        
        # Reset counters at 9:00 AM (before market opens)
        scheduler.add_job(reset_daily_counters, 'cron', day_of_week='mon-fri', hour=9, minute=0, timezone=IST)
        
        # Hourly health check
        scheduler.add_job(health_check, 'interval', hours=1, timezone=IST)
        
        # Start the scheduler
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
        
        # Initial login to verify credentials
        try:
            alice = login()
            logger.info("Initial login successful")
        except Exception as e:
            logger.error(f"Initial login failed: {e}")
            send_telegram_message(f"⚠️ Initial login failed. Will retry at scheduled time. Error: {e}")
        
        # Keep the script running
        logger.info("Bot is now running...")
        send_telegram_message("✅ Nifty Options Bot is now active and monitoring the market")
        
        while True:
            time.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutdown initiated")
        send_telegram_message("🛑 Bot is shutting down")
        scheduler.shutdown()
    except Exception as e:
        error_msg = f"Critical error: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(f"❌ {error_msg}")
