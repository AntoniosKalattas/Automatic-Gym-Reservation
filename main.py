import time
import json
import os
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv
from autoReservation import GymReservationBot
from notifications import Notifier

load_dotenv()

# --- CONFIGURATION ---
USER_EMAIL = os.getenv("USER_EMAIL")
STATE_FILE = "reservation_state.json"
MAX_RETRIES = 5
RETRY_DELAY = 60 

# Time Options Reference:
# 1=07:45, 2=09:30, 3=11:15, 4=13:00, 5=14:45, 6=16:45, 7=18:30, 8=20:15
# Saturday: 9=08:45, 10=10:30, 11=12:15

# YOUR CUSTOM SCHEDULE
# 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
WEEKLY_SCHEDULE = {
    0: 1,   # Monday    -> Option 1 (07:45)
    1: 3,   # Tuesday   -> Option 3 (11:15)
    2: 7,   # Wednesday -> Option 7 (18:30)
    3: 7,   # Thursday  -> Option 7
    4: 7,   # Friday    -> Option 7
    5: 11,  # Saturday  -> Option 11 (12:15)
    6: 11   # Sunday    -> Option 11
}

def get_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_state(date_str, status):
    data = get_state()
    data[date_str] = status
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f)

def job():
    today_str = datetime.now().strftime('%Y-%m-%d')
    state = get_state()

    if state.get(today_str) == "SUCCESS":
        print(f"✅ Already booked for {today_str}. Skipping.")
        return

    # 1. Calculate Target Date (5 days from now)
    target_date = datetime.now() + timedelta(days=5)
    target_day_num = target_date.day
    target_weekday = target_date.weekday() # 0 = Monday, 6 = Sunday

    # 2. Get the specific time for that day
    target_time_opt = WEEKLY_SCHEDULE.get(target_weekday, 7) # Default to 7 if missing

    print(f"🚀 Starting reservation for {target_date.strftime('%A %d/%m')} at Time Option {target_time_opt}...")
    
    notifier = Notifier()
    attempt = 0
    success = False
    
    while attempt < MAX_RETRIES and not success:
        attempt += 1
        print(f"Attempt {attempt}/{MAX_RETRIES}...")
        
        # Initialize bot
        bot = GymReservationBot(headless=True)
        
        # Pass the EXACT time option we want
        success, msg = bot.make_reservation(target_time_opt, target_day_num)
        
        if success:
            print(f"✅ Success: {msg}")
            save_state(today_str, "SUCCESS")
            notifier.alert(True, USER_EMAIL, f"Booked {target_date.strftime('%A')} at option {target_time_opt}")
            return
        else:
            print(f"⚠️ Failed: {msg}")
            if "Login" in msg:
                notifier.alert(False, USER_EMAIL, "Login expired! Update profile.")
                return 
            
            time.sleep(RETRY_DELAY)

    save_state(today_str, "FAILED")
    notifier.alert(False, USER_EMAIL, f"Failed after {MAX_RETRIES} attempts.\nLast error: {msg}")

# Run scheduler
print("System Online. Scheduler running...")
schedule.every().day.at("13:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)