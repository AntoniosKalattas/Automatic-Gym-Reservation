import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  SNIPER CONFIGURATION — edit these
# ─────────────────────────────────────────────
TARGET_DAY   = 3     # Day of the month (e.g. 15)
TARGET_TIME  = 5      # Time option index (1=07:45 … 8=20:15, Sat: 9-11)
MAX_ATTEMPTS = 500    # How many times to keep hammering before giving up
RETRY_DELAY  = 5      # Seconds to wait between retries (keep ≥3 to avoid bans)
HEADLESS     = False  # Set True to run in background
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("sniper")

TIME_LABELS = {
    1: "07:45", 2: "09:30", 3: "11:15", 4: "13:00",
    5: "14:45", 6: "16:45", 7: "18:30", 8: "20:15",
    9: "08:45 (Sat)", 10: "10:30 (Sat)", 11: "12:15 (Sat)"
}


class GymSniper:
    BASE_URL = (
        "https://applications2.ucy.ac.cy/sportscenter/"
        "online_reservations_pck2.insert_reservation?p_lang="
    )

    def __init__(self):
        self.driver = self._init_driver()
        self.wait   = WebDriverWait(self.driver, 10)

    def _init_driver(self):
        opts = Options()
        for arg in ["--no-sandbox", "--disable-gpu",
                     "--disable-extensions", "--disable-dev-shm-usage"]:
            opts.add_argument(arg)
        if HEADLESS:
            opts.add_argument("--headless=new")

        profile_path = os.getenv("CHROME_PROFILE_PATH")
        profile_dir  = os.getenv("CHROME_PROFILE_FOLDER", "Default")
        if profile_path:
            opts.add_argument(f"--user-data-dir={profile_path}")
            opts.add_argument(f"--profile-directory={profile_dir}")

        return webdriver.Chrome(options=opts)

    def _click(self, by, value, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            ).click()
            return True
        except TimeoutException:
            return False

    def _js_click(self, elem):
        self.driver.execute_script("arguments[0].click();", elem)

    # ── One-time setup: navigate to the time-selection page ──
    def _load_page(self):
        self.driver.get(self.BASE_URL)
        if "login" in self.driver.current_url:
            raise RuntimeError("Login session expired — please log in manually first.")

    def _select_gym(self):
        if not self._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
            fix_xpath = "/html/body/div[2]/div/div[2]/div[1]/ul/li[1]/a"
            if self._click(By.XPATH, fix_xpath):
                time.sleep(2)
                self.driver.get(self.BASE_URL)
                if not self._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
                    raise RuntimeError("Could not select Gymnasium even after nav-fix.")
            else:
                raise RuntimeError("Nav-fix click failed.")
        self._click(By.CSS_SELECTOR, "input[type='checkbox']")
        self._click(By.CSS_SELECTOR, "button[type='submit']")

    def _select_day(self, day: int):
        day_xpath = f"//button[normalize-space()='{day}']"
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath))).click()
        except TimeoutException:
            try:
                nb = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="contentRow"]/center/table[2]/tbody/tr/td[2]/div/button'
                )
                nb.click()
                time.sleep(3)
                self.wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath))).click()
            except Exception:
                raise RuntimeError(f"Day {day} not found on calendar.")

    # ── Phase 1: select time, fill form, click first submit (run ONCE) ──
    def _submit_phase1(self, time_opt: int) -> bool:
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            self.driver.find_element(By.XPATH, f"//select/option[{time_opt}]").click()
        except Exception:
            log.error("Time option not found on page.")
            return False

        try:
            self.driver.find_element(By.TAG_NAME, "textarea").send_keys("ak")
        except Exception:
            pass  # optional field

        for xp in [
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Submit')]",
            "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button",
            "//button[@type='submit']",
        ]:
            try:
                btn = self.driver.find_element(By.XPATH, xp)
                if btn.is_displayed():
                    self._js_click(btn)
                    time.sleep(1)
                    return True
            except Exception:
                continue

        log.error("Phase-1 submit button not found.")
        return False

    # ── Phase 2: click confirm button and check result (retried in loop) ──
    def _retry_confirm(self) -> tuple[bool, str]:
        # Try to find and click the confirm button on the current page
        for xp in [
            "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button",
            "//button[contains(text(), 'Yes') or contains(text(), 'Confirm')]",
            "//button[@type='submit']",
        ]:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                self._js_click(btn)
                time.sleep(2)

                # Check result
                elems = self.driver.find_elements(By.CLASS_NAME, "prntcontent")
                if elems:
                    text = " ".join(e.text for e in elems)
                    if "επιτυχία" in text:
                        return True, "Reservation Successful 🎯"
                    # Slot full / rejected — go back ONE page to the confirm page
                    self.driver.back()
                    time.sleep(1)
                    return False, f"Rejected: {text.strip()[:120]}"

                if "text-danger" in self.driver.page_source:
                    self.driver.back()
                    time.sleep(1)
                    return False, "Generic error (text-danger)"

                # No recognizable result — go back to be safe
                self.driver.back()
                time.sleep(1)
                return False, "No status element found"

            except TimeoutException:
                continue

        return False, "Confirm button not found on page"

    # ── Main sniper loop ──
    def snipe(self, target_day: int, target_time: int):
        log.info("=" * 55)
        log.info(f"  🎯  GYM SNIPER  |  Day {target_day}  |  Time {TIME_LABELS.get(target_time, target_time)}")
        log.info(f"  Max attempts : {MAX_ATTEMPTS}  |  Retry delay : {RETRY_DELAY}s")
        log.info("=" * 55)

        start = datetime.now()

        try:
            # ── Navigate to time-selection page (once) ──
            self._load_page()
            self._select_gym()
            self._select_day(target_day)

            # ── Phase 1: select time and submit form (once) ──
            if not self._submit_phase1(target_time):
                log.error("🔴  Phase 1 failed — couldn't reach confirm page.")
                return False

            log.info("✅ On confirm page. Hammering confirm button...\n")

            # ── Phase 2: retry the confirm click until it works ──
            for attempt in range(1, MAX_ATTEMPTS + 1):
                elapsed = int((datetime.now() - start).total_seconds())
                log.info(f"[{attempt}/{MAX_ATTEMPTS}]  {elapsed}s elapsed  — firing...")

                success, msg = self._retry_confirm()

                if success:
                    log.info(f"\n🟢  {msg}")
                    log.info(f"   Total attempts : {attempt}")
                    log.info(f"   Total time     : {elapsed}s")
                    return True

                log.info(f"   ↩  {msg}  — retrying in {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY)

            log.warning(f"\n🔴  Gave up after {MAX_ATTEMPTS} attempts.")
            return False

        except RuntimeError as e:
            log.error(f"🔴  Fatal: {e}")
            return False
        finally:
            self.driver.quit()


if __name__ == "__main__":
    sniper = GymSniper()
    sniper.snipe(TARGET_DAY, TARGET_TIME)