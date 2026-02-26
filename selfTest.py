import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notifications import Notifier
from autoReservation import GymReservationBot
from selenium.webdriver.common.by import By

load_dotenv()

def test_notifications(notifier:Notifier):
    print("\n--- 1. Testing Notifications ---")
    if(notifier.send_telegram("🔥Yoh, the UCY Gym Bot is connected!") and  notifier.send_email(os.getenv("USER_EMAIL"),"test", "self test email.")):
        return True
    return False

def test_navigation():
    print("\n--- 2. Testing Website Navigation ---")
    print("🚀 Launching Browser (Visible Mode)...")
    
    bot = GymReservationBot(headless=False, testMode=True)
    try:
        return bot.make_reservation(4, (datetime.now() + timedelta(days=5)).day)


    except Exception as e:
        print(f"❌ Crash: {e}")
        return False
    finally:
        bot.driver.quit()

def run_self_test():
    print("**************************************************")
    print("          UCY GYM BOT - SELF DIAGNOSTIC           ")
    print("**************************************************")
    notifier = Notifier()
    test_notifications(notifier)
    if(test_navigation()):
        print("✅✅ SELF TEST PASSED ✅✅")
    else:
        print("❌❌ SELF TEST FAILED ❌❌")

if __name__ == "__main__":
    run_self_test()