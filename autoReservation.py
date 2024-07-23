import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from colorama import init, Fore, Back, Style
from datetime import datetime
from tqdm import tqdm
import sys
path_to_profile = "/Users/admin/Library/Application Support/Google/Chrome/" #path to chrome profile (si you won't need to login).
profile_name = "Default"                                                    #name of the profile folder
#time options: 1    2    3     4     5     6     7     8
#              7:45 9:30 11:15 13:00 14:45 16:45 18:30 20:15
time_option = str(6)
web_site = "https://applications2.ucy.ac.cy/sportscenter/online_reservations_pck2.insert_reservation?p_lang="# website link
current_datetime = datetime.now()       #current time
current_day = str(current_datetime.day+1) #current day
print("Day: "+ current_day)
data =[]

# Initialize tqdm progress bar with the expected number of try blocks
total_tries = 6  # Update this number based on the actual number of try blocks
pbar = tqdm(total=total_tries)

options = webdriver.ChromeOptions()
options.add_argument('--headless')                          # Enable headless mode
options.add_argument('--no-sandbox')                        # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')             # Overcome limited resource problems
options.add_argument('--disable-gpu')                       # Disable GPU (important for headless)
options.add_argument('--window-size=1920,1080')             #  Set window size to avoid issues with headless mode
options.add_argument(f"user-data-dir={path_to_profile}")    # Set the profile directory
options.add_argument(f"profile-directory={profile_name}")   # same thing here

driver = webdriver.Chrome(options=options)  # Optional argument, if not specified will search path.
driver.get(web_site)
time.sleep(5)
##try:
##    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[4]/td[2]")
##    print(Fore.RED + "FATAL ERROR: "+ Style.RESET_ALL+" Profile not found")
##    driver.quit()   
##except NoSuchElementException:
##    print(Fore.GREEN+"Profile Found!")


#Screen 1
driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td[2]/select/option[4]").click() #select the "Γυμναστιριο"
driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[4]/td[2]/input").click()            #tick the terms
driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td[2]/div/button").click()       #click the submit button
time.sleep(5)
#Screen 2
flag = False
for i in range(2):
    try:
        driver.find_element(By.XPATH, "//button[text()='"+current_day+ "']").click()
        pbar.update(1)
    except NoSuchElementException:
        print(Fore.RED +"ERROR: "+Style.RESET_ALL +"blue button with the day, could be found in the page. Please check again for any changes in the website.")
        flag = True
    if flag==False:
        break
    else:
        time.sleep(5)
#Screen 3
time.sleep(3)
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td/table/tbody/tr/td[3]/select").click()             #click the time dropdown box
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[2]/td/table/tbody/tr/td[3]/select/option["+time_option+"]").click()   #choose the time
    pbar.update(1)
except NoSuchElementException:
    print(Fore.RED + "ERROR: " +Style.RESET_ALL + "No such time found, check website for any changes.", file=sys.stderr)
    sys.exit(1)
try:
    driver.find_element(By.XPATH, "//*[@id='textarea']").send_keys("ak")
    pbar.update(1)
except NoSuchElementException:
    print(Fore.RED + "ERROR: " +Style.RESET_ALL + "No textbox found, check website for any changes.", file=sys.stderr)
    sys.exit(1)
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button").click()
    pbar.update(1)
except NoSuchElementException:
    print(Fore.RED + "ERROR: " + Style.RESET_ALL + "No KATAXORISI button found, check website for any changes.", file=sys.stderr)
    sys.exit(1)
time.sleep(2)
try:
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button").click()
    pbar.update(1)
except NoSuchElementException:
    print(Fore.RED + "ERROR: " + Style.RESET_ALL + "No second KATAXORISI button found, check website for any changes.", file=sys.stderr)
    sys.exit(1)
time.sleep(3)
flaG = False
li = ""
try:
    not_okay = driver.find_element(By.CLASS_NAME, "text-danger")
    #faild_label = driver.find_element(By.XPATH, "//label[text()='{Οι κρατήσεις δεν έχουν γίνει για τους εξής λόγους:}']")
    if not_okay:
        li = driver.find_element(By.CLASS_NAME, "prntcontent")
        print(Fore.RED + "ERROR: " + Style.RESET_ALL + li.text, file=sys.stderr)
        flaG = True
    else:
        print(Fore.GREEN + "DONE")
except NoSuchElementException:
    pbar.update(1)
    print(Fore.GREEN + "DONE")
driver.quit()
