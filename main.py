from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from colorama import init, Fore, Back, Style
init()
#############variables##########
day = "10"

#############

# Path to your Firefox profile (ensure this is the correct and actual path)
profile_path = "/Users/admin/Library/Application Support/Firefox/Profiles/2dev84lv.default-release-1"
geckodriver_path = "/Users/admin/Documents/Automations/Gym_Cy/python_ver/geckodriver"
# Set up Firefox options
options = Options()
options.set_preference("profile", profile_path)
# options.add_argument('--headless')  # Uncomment to run in headless mode

# Set up Firefox service
service = Service(executable_path=geckodriver_path)

# Create a webdriver instance (for Firefox)
driver = webdriver.Firefox(service=service, options=options)

# Open the target website
link = "https://applications.ucy.ac.cy/pub_sportscenter/online_reservations_pck2.insert_reservation?p_lang="
driver.get(link)
time.sleep(5)

# Perform the necessary actions on the website



current_datetime = datetime.now()
current_day = str(current_datetime.day + 6)
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/table/tbody/tr/td")
    print(Fore.RED + "FATAL ERROR: "+ Style.RESET_ALL+" Profile not found")
    driver.quit()   
except NoSuchElementException:
    print(Fore.GREEN+"Profile Found!")

driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td[2]/select/option[4]").click()
driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[4]/td[2]/input").click()
driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td[2]/div/button").click()
time.sleep(3)
try:
    driver.find_element(By.XPATH, "//button[text()='"+current_day+ "']").click()
except NoSuchElementException:
    print(Fore.RED +"ERROR: "+Style.RESET_ALL +"blue button with the day, could be found in the page. Please check again for any changes in the website.")
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td/table/tbody/tr/td[3]/select").click()
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td/table/tbody/tr/td[3]/select/option[4]").click()
except NoSuchElementException:
    print(Fore.RED + "ERROR: " +Style.RESET_ALL + "No such time found, check website for any changes.")
try:
    driver.find_element(By.XPATH, "//*[@id='textarea']").send_keys("ak")
except NoSuchElementException:
    print(Fore.RED + "ERROR: " +Style.RESET_ALL + "No textbox found, check website for any changes.")
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button").click()
except NoSuchElementException:
    print(Fore.RED + "ERROR: " + Style.RESET_ALL + "No KATAXORISI button found, check website for any changes.")
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button").click()
except NoSuchElementException:
    print(Fore.RED + "ERROR: " + Style.RESET_ALL + "No second KATAXORISI button found, check website for any changes.")
not_okay = driver.find_element(By.CLASS_NAME, "text-danger")
faild_label = driver.find_element(By.XPATH, "//label[text()='{Οι κρατήσεις δεν έχουν γίνει για τους εξής λόγους:}']")
if faild_label:
    print(Fore.RED + "ERROR: " + Style.RESET_ALL + "Gym is FULL or wrong time.")
else:
    print(Fore.GREEN + "DONE")
# Add further actions as needed
# driver.find_element(By.XPATH, "").click()
# driver.find_element(By.XPATH, "").click()
# driver.find_element(By.XPATH, "").click()
# driver.find_element(By.XPATH, "").click()
# driver.find_element(By.XPATH, "").click()

# Close the browser
# driver.quit()
