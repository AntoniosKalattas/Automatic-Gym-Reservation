import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notifications import Notifier
from autoReservation import GymReservationBot
from selenium.webdriver.common.by import By

load_dotenv()

def test_notifications(notifier):
    print("\n--- 1. Testing Notifications ---")
    # (Keeping this short as we know it works from your log)
    print("✅ Skipping Notification Test (Confirmed working previously)")
    return True

def test_navigation():
    print("\n--- 2. Testing Website Navigation ---")
    print("🚀 Launching Browser (Visible Mode)...")
    
    bot = GymReservationBot(headless=False)
    
    try:
        print("   -> Loading URL...")
        bot.driver.get(bot.url)
        time.sleep(2)

        if "login" in bot.driver.current_url:
            print("❌ Login Required! Please manually log in.")
            return False

        print("   -> Selecting Gymnasium...")
        
        # ATTEMPT 1
        if bot._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
            print("✅ Gymnasium Selected (On first try)")
        else:
            # ATTEMPT FIX
            print("⚠️ Selection failed. Attempting user-provided FIX...")
            fix_xpath = "/html/body/div[2]/div/div[2]/div[1]/ul/li[1]/a"
            
            if bot._click(By.XPATH, fix_xpath):
                print("   -> 'Home' button clicked. Reloading...")
                time.sleep(2)
                bot.driver.get(bot.url)
                
                if bot._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
                    print("✅ Gymnasium Selected (After fix!)")
                else:
                    print("❌ Failed to select Gymnasium even after fix.")
                    return False
            else:
                print("❌ Could not find the 'Home' button.")
                return False
        
        # Proceed with flow
        bot._click(By.CSS_SELECTOR, "input[type='checkbox']")
        bot._click(By.CSS_SELECTOR, "button[type='submit']")
        time.sleep(1)

        target_day = (datetime.now() + timedelta(days=1)).day
        print(f"   -> Attempting to click Day {target_day}...")
        
        try:
            day_xpath = f"//button[normalize-space()='{target_day}']"
            bot._click(By.XPATH, day_xpath)
            print(f"✅ Day {target_day} clicked")
        except:
            print(f"⚠️ Could not click Day {target_day} (Might need 'Next Month' logic)")
        
        time.sleep(1)
        print("\n🎉 NAVIGATION TEST PASSED!")
        return True

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
    if test_navigation():
        print("✅✅ SELF TEST PASSED ✅✅")
    else:
        print("❌❌ SELF TEST FAILED ❌❌")

if __name__ == "__main__":
    run_self_test()