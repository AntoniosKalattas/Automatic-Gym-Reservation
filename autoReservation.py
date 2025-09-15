#!/usr/bin/env python3
"""
autoReservation.py - Gym Reservation Automation Script
Automates the process of making reservations at UCY Sports Center
Called by scheduler with arguments: time_option, saturday_time_option, day
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException
)
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init(autoreset=True)

@dataclass
class ReservationConfig:
    """Configuration for reservation parameters"""
    website_url: str = "https://applications2.ucy.ac.cy/sportscenter/online_reservations_pck2.insert_reservation?p_lang="
    profile_path_file: str = "chromeProfilePath.txt"
    profile_directory: str = "Default"
    timeout: int = 10
    comment_text: str = "ak"

class GymReservationBot:
    """Automated gym reservation booking system"""
    
    def __init__(self, config: ReservationConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.progress_bar: Optional[tqdm] = None
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('reservation_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_chrome_profile_path(self) -> str:
        """Load Chrome profile path from file"""
        try:
            profile_path = Path(self.config.profile_path_file)
            if not profile_path.exists():
                raise FileNotFoundError(f"Profile path file not found: {self.config.profile_path_file}")
            
            with open(profile_path, 'r', encoding='utf-8') as file:
                path = file.read().strip()
                
            if not path:
                raise ValueError("Profile path is empty")
                
            return path
            
        except Exception as e:
            self.logger.error(f"Failed to load Chrome profile path: {e}")
            raise
    
    def create_chrome_options(self, headless: bool = False) -> Options:
        """Create Chrome options with proper configuration"""
        options = Options()
        
        # Performance and security options
        chrome_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Faster loading
            '--disable-javascript',  # Only if site works without JS
        ]
        
        if headless:
            chrome_args.append('--headless')
        
        for arg in chrome_args:
            options.add_argument(arg)
        
        # Profile configuration
        profile_path = self.load_chrome_profile_path()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument(f"--profile-directory={self.config.profile_directory}")
        
        return options
    
    def initialize_driver(self, headless: bool = True) -> bool:
        """Initialize Chrome driver with error handling"""
        try:
            options = self.create_chrome_options(headless)
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.config.timeout)
            return True
            
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            return False
    
    def element_exists(self, by: By, value: str) -> bool:
        """Check if element exists without raising exceptions"""
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
    
    def wait_and_click(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """Wait for element and click it with error handling"""
        try:
            timeout = timeout or self.config.timeout
            element = self.wait.until(
                EC.element_to_be_clickable((by, value)),
                timeout
            )
            element.click()
            return True
            
        except TimeoutException:
            self.logger.error(f"Timeout waiting for clickable element: {by}={value}")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking element {by}={value}: {e}")
            return False
    
    def handle_login_check(self) -> bool:
        """Handle login verification and redirect if needed"""
        self.driver.get(self.config.website_url)
        time.sleep(3)
        
        if self.element_exists(By.CLASS_NAME, "login-paginated-page"):
            self.logger.warning("Login required - opening browser for manual login")
            self.driver.quit()
            
            # Open non-headless browser for login
            if not self.initialize_driver(headless=False):
                return False
            
            self.driver.get(self.config.website_url)
            
            # Wait for user to login
            print(f"{Fore.YELLOW}Please login manually. Waiting for login completion...")
            
            while True:
                if self.element_exists(By.ID, "ds_calclass"):
                    print(f"{Fore.GREEN}Login detected!")
                    break
                time.sleep(2)
            
            self.driver.quit()
            return self.initialize_driver(headless=True)
        
        return True
    
    def select_gymnasium(self) -> bool:
        """Select gymnasium option"""
        try:
            # Handle potential redirect
            if not self.element_exists(By.XPATH, "//select/option[4]"):
                self.logger.info("Redirecting to main page")
                home_link = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//ul/li[1]"))
                )
                home_link.click()
                time.sleep(3)
                self.driver.get(self.config.website_url)
            
            # Select gymnasium
            gym_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//select/option[4]"))
            )
            gym_option.click()
            
            # Accept terms
            terms_checkbox = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
            )
            terms_checkbox.click()
            
            # Submit
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            submit_btn.click()
            
            return True
            
        except TimeoutException as e:
            self.logger.error(f"Timeout during gymnasium selection: {e}")
            return False
    
    def select_day(self, day: str) -> bool:
        """Select the reservation day"""
        time.sleep(3)
        
        for attempt in range(2):
            try:
                day_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[text()='{day}']"))
                )
                day_button.click()
                return True
                
            except TimeoutException:
                if attempt == 0:
                    # Try clicking next month button
                    try:
                        next_btn = self.driver.find_element(
                            By.XPATH, "//div/button[@type='button']"
                        )
                        next_btn.click()
                        time.sleep(2)
                    except NoSuchElementException:
                        pass
                else:
                    self.logger.error(f"Day button '{day}' not found after {attempt + 1} attempts")
                    return False
        
        return False
    
    def select_time_and_submit(self, time_option: str, saturday_time_option: str) -> bool:
        """Select time slot and submit reservation"""
        time.sleep(2)
        
        try:
            # Click time dropdown
            time_dropdown = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//select"))
            )
            time_dropdown.click()
            
            # Try regular time option first, then Saturday option
            time_selected = False
            for option in [time_option, saturday_time_option]:
                try:
                    time_option_element = self.driver.find_element(
                        By.XPATH, f"//select/option[{option}]"
                    )
                    time_option_element.click()
                    time_selected = True
                    break
                except NoSuchElementException:
                    continue
            
            if not time_selected:
                self.logger.error("No valid time option found")
                return False
            
            # Add comment
            comment_box = self.wait.until(
                EC.presence_of_element_located((By.ID, "textarea"))
            )
            comment_box.send_keys(self.config.comment_text)
            
            # Submit reservation
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button"))
            )
            submit_btn.click()
            time.sleep(2)
            
            # Confirm submission
            confirm_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button"))
            )
            confirm_btn.click()
            
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            self.logger.error(f"Error during time selection and submission: {e}")
            return False
    
    def check_reservation_result(self, test: bool = False) -> Tuple[bool, str]:
        """Check if reservation was successful"""
        time.sleep(3)

        try:
            error_element = self.driver.find_element(By.CLASS_NAME, "text-danger")
            if error_element:
                error_content = self.driver.find_element(By.CLASS_NAME, "prntcontent")
                error_message = error_content.text if error_content else "Unknown error"
                if test:
                    return True, "Done"
                else:
                    return False, error_message
                
        except NoSuchElementException:
            return True, "Reservation completed successfully"
        
        return True, "Reservation completed successfully"
    
    def make_reservation(self, time_option: str, saturday_time_option: str, day: str, headless: bool, test: bool = False) -> bool:
        """Main method to execute the reservation process"""
        self.progress_bar = tqdm(total=6, desc="Reservation Progress")

        print(f"{Fore.CYAN}Starting gym reservation bot...")
        print(f"Daily time option: {time_option}")
        print(f"Saturday time option: {saturday_time_option}")
        print(f"Day: {day}")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Headless switch: {'true' if headless else 'false'}")
        
        try:
            # Initialize driver
            if not self.initialize_driver(headless = headless):
                return False
            self.progress_bar.update(1)
            
            # Handle login
            if not self.handle_login_check():
                return False
            self.progress_bar.update(1)
            
            # Select gymnasium
            if not self.select_gymnasium():
                return False
            self.progress_bar.update(1)
            
            # Select day
            if not self.select_day(day):
                return False
            self.progress_bar.update(1)
            
            # Select time and submit
            if not self.select_time_and_submit(time_option, saturday_time_option):
                return False
            self.progress_bar.update(1)
            
            # Check result
            success, message = self.check_reservation_result(test)
            self.progress_bar.update(1)
            
            if success:
                print(f"{Fore.GREEN}SUCCESS: {message}")
                self.logger.info(f"Reservation successful: {message}")
            else:
                print(f"{Fore.RED}ERROR: {message}")
                self.logger.error(f"Reservation failed: {message}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Unexpected error during reservation: {e}")
            print(f"{Fore.RED}FATAL ERROR: {e}")
            return False
            
        finally:
            if self.progress_bar:
                self.progress_bar.close()
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Driver closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing driver: {e}")
