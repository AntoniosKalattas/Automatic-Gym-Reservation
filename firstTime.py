from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
import time


link = "https://applications2.ucy.ac.cy/pub_sportscenter/"

path_to_profile = "/Users/admin/Library/Application Support/Google/Chrome/" #path to chrome profile (si you won't need to login).
profile_name = "Default"                                                    #name of the profile folder

options = webdriver.ChromeOptions()                                         #set up chrome options
options.add_argument('--no-sandbox')                                        # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')                             # Overcome limited resource problems
options.add_argument('--disable-gpu')                                       # Disable GPU (important for headless)
options.add_argument('--window-size=1920,1080')                             #  Set window size to avoid issues with headless mode
options.add_argument(f"user-data-dir={path_to_profile}")                    # Set the profile directory
options.add_argument(f"profile-directory={profile_name}")                   # same thing here

driver = webdriver.Chrome(options=options)                                  # Optional argument, if not specified will search path.
driver.get(link)
try:
    while True:
        try:
            driver.title
        except (NoSuchWindowException, WebDriverException):
            print("Browser Closed")
            break
    time.sleep(1)
finally:
    driver.quit()

