import os
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from dotenv import load_dotenv

load_dotenv()

class GymReservationBot:
    def __init__(self, headless=True, testMode=False):
        self.url = "https://applications2.ucy.ac.cy/sportscenter/online_reservations_pck2.insert_reservation?p_lang="
        self.logger = self._setup_logging()
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 10) 
        self.testMode = testMode

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

    def _init_driver(self, headless):
        options = Options()
        args = ['--no-sandbox', '--disable-gpu', '--disable-extensions', '--disable-dev-shm-usage']
        
        for arg in args:
            options.add_argument(arg)

        profile_path = os.getenv("CHROME_PROFILE_PATH")
        profile_dir = os.getenv("CHROME_PROFILE_FOLDER", "Default")
        
        if profile_path:
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument(f"--profile-directory={profile_dir}")

        return webdriver.Chrome(options=options)

    def _click(self, by, value):
        try:
            elem = self.wait.until(EC.element_to_be_clickable((by, value)))
            elem.click()
            return True
        except TimeoutException:
            return False

    def make_reservation(self, target_time: int, target_day: int) -> tuple[bool, str]:
        try:
            self.driver.get(self.url)

            # 1. Login Check
            if "login" in self.driver.current_url:
                return False, "Login session expired. Please manual login."

            # 2. Select Gym
            if not self._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
                self.logger.warning("Applying 'Home Button' fix...")
                fix_xpath = "/html/body/div[2]/div/div[2]/div[1]/ul/li[1]/a"
                if self._click(By.XPATH, fix_xpath):
                    time.sleep(2)
                    self.driver.get(self.url)
                    if not self._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
                        return False, "Could not select Gymnasium."
                else:
                    return False, "Nav fix failed."

            self._click(By.CSS_SELECTOR, "input[type='checkbox']")
            self._click(By.CSS_SELECTOR, "button[type='submit']")

            # 3. Select Day
            try:
                day_xpath = f"//button[normalize-space()='{target_day}']"
                self.wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath))).click()
            except TimeoutException:
                try:
                    next_month_btn = self.driver.find_element(By.XPATH, '//*[@id="contentRow"]/center/table[2]/tbody/tr/td[2]/div/button') 
                    next_month_btn.click()
                    time.sleep(4)
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath))).click()
                except:
                    return False, f"Day {target_day} not found."

            # 4. Select Time
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            try:
                option_xpath = f"//select/option[{target_time}]"
                self.driver.find_element(By.XPATH, option_xpath).click()
            except:
                return False, f"Time option {target_time} full or unavailable."

            # 5. Comment & Submit (Phase 1)
            try:
                self.driver.find_element(By.TAG_NAME, "textarea").send_keys("ak")
                
                strategies = [
                    "//button[contains(text(), 'Next')]",
                    "//button[contains(text(), 'Submit')]",
                    "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button",
                    "//button[@type='submit']"
                ]
                
                phase1_success = False
                for xpath in strategies:
                    try:
                        btn = self.driver.find_element(By.XPATH, xpath)
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            phase1_success = True
                            break
                    except:
                        continue
                
                if not phase1_success:
                    return False, "Phase 1 Submit button not found"

                time.sleep(1)

                # 6. FINAL CONFIRMATION (Phase 2)
                final_button_xpath = "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button"
                
                try:
                    confirm_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, final_button_xpath)))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", confirm_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    
                except TimeoutException:
                    try:
                        fallback_xpath = "//button[contains(text(), 'Yes') or contains(text(), 'Confirm')]"
                        confirm_btn = self.driver.find_element(By.XPATH, fallback_xpath)
                        self.driver.execute_script("arguments[0].click();", confirm_btn)
                    except:
                        if(self.testMode):
                            return True
                        return False, "Final Confirm button not found."

            except Exception as e:
                if(self.testMode):
                    return True
                return False, f"Error during submission: {str(e)}"

            if(self.testMode):
                return True
            # 7. Verification (FINAL CORRECTED VERSION)
            time.sleep(2)
            
            try:
                # Find ALL elements with class 'prntcontent'
                # This catches both <p class='prntcontent'> (Success) 
                # AND <li class='prntcontent'> (Error/Reason)
                status_elements = self.driver.find_elements(By.CLASS_NAME, "prntcontent")
                
                if status_elements:
                    # Combine text from all found elements to handle lists
                    full_text = " ".join([elem.text for elem in status_elements])
                    
                    if "επιτυχία" in full_text:
                        return True, "Reservation Successful"
                    else:
                        # Return the exact Greek error message found on the page
                        return False, f"Failed: {full_text}"
                else:
                    # Fallback if the class isn't found at all
                    if "text-danger" in self.driver.page_source:
                         return False, "Failed (Generic Error)"
                    return False, "Unknown Result (No status message found)"

            except Exception as e:
                return False, f"Error parsing result: {str(e)}"

        except Exception as e:
            return False, f"Crash: {str(e)}"
        finally:
            self.driver.quit()