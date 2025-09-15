import schedule
import time
import subprocess
from datetime import datetime, timedelta
import autoReservation
from emailSystem import send_email

##########################################################################
# Monday to Friday
# time options: 1    2    3     4     5     6     7     8
#               7:45 9:30 11:15 13:00 14:45 16:45 18:30 20:15
time_option = 7

# Saturday
# time options: 9    10    11
#               8:45 10:30 12:15
time_option2 = 11

userEmail = "example@host.com"
##########################################################################

# Global variable to track reservation success
reservation_successful = False
sendEmailNotif = False
last_attempt_date = None

def run_main_script() -> bool:
    """Run the reservation script and return success status"""
    global reservation_successful, last_attempt_date
    
    today = datetime.now()
    
    # Reset success flag if it's a new day
    if last_attempt_date != today.date():
        reservation_successful = False
        sendEmailNotif = (userEmail == "example@host.com");
        last_attempt_date = today.date()
    
    # If already successful today, skip
    if reservation_successful:
        print(f"Reservation already successful today ({today.strftime('%Y-%m-%d')}). Skipping...")
        return True
    
    future_date = today + timedelta(days=5)
    next5day = future_date.day
    
    print(f"Running reservation script at {today.strftime('%H:%M:%S')}...")
    
    try:
        config = autoReservation.ReservationConfig()
        bot = autoReservation.GymReservationBot(config)
        success = bot.make_reservation(time_option, time_option2, next5day, headless=True)
        
        if success:
            reservation_successful = True
            print("✅ Reservation successful!")
            return True
        else:
            print("❌ Reservation failed")
            if(sendEmailNotif== False): 
                send_email(userEmail)
                sendEmailNotif = True
            return False
            
    except Exception as e:
        print(f"❌ Error during reservation: {e}")
        if(sendEmailNotif== False): 
            send_email(userEmail, e)
            sendEmailNotif = True
        return False

def run_retry_script() -> bool:
    """Run script only if previous attempts failed"""
    if reservation_successful:
        print("Reservation already successful today. Skipping retry...")
        return True
    
    print("Previous attempt failed. Retrying...")
    return run_main_script()

# Schedule the primary attempt at 8:00 AM
schedule.every().day.at("08:00").do(run_main_script)

# Schedule retry attempts only if previous failed
schedule.every().day.at("08:06").do(run_retry_script)
schedule.every().day.at("08:08").do(run_retry_script)
schedule.every().day.at("08:12").do(run_retry_script)

# Keep the script running
print("Scheduler started. Waiting for the scheduled time...")
print("Primary attempt: 08:00")
print("Retry attempts: 08:06, 08:08, 08:12 (only if previous failed)")

while True:
    schedule.run_pending()
    time.sleep(1)