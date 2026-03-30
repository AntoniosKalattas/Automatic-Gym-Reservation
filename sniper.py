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
TARGET_DAY  = 30      # Day of the month (e.g. 15)
TARGET_TIME = 7       # Time option index (1=07:45 … 8=20:15, Sat: 9-11)
MAX_ATTEMPTS = 500    # How many times to keep hammering before giving up
RETRY_DELAY  = 5      # Seconds to wait between retries (keep ≥3 to avoid bans)
HEADLESS     = False   # Set False to watch the browser
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("sniper")

# ── Time option reference ─────────────────────
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

    # ── Driver ────────────────────────────────
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
            elem = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            elem.click()
            return True
        except TimeoutException:
            return False

    def _js_click(self, elem):
        self.driver.execute_script("arguments[0].click();", elem)

    # ── Navigation helpers ────────────────────
    def _load_page(self):
        self.driver.get(self.BASE_URL)
        if "login" in self.driver.current_url:
            raise RuntimeError("Login session expired — please log in manually first.")

    def _select_gym(self):
        """Select the Gymnasium option and accept the checkbox + submit."""
        if not self._click(By.CSS_SELECTOR, "select option:nth-child(4)"):
            # Home-button fix (matches original bot)
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
            # Try next month
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

    # ── Core sniper step: select time → submit → confirm ──
    def _attempt_booking(self, time_opt: int) -> tuple[bool, str]:
        """
        Called repeatedly.  Assumes we are already on the time-selection page
        (after gym + day have been selected).
        On failure it navigates back ONE step so we land back on the
        time-selection page ready for the next attempt.
        """
        # ── Step A: pick the time slot ──
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            opt = self.driver.find_element(By.XPATH, f"//select/option[{time_opt}]")
            opt.click()
        except Exception:
            return False, "CAPACITY_FULL_OR_GONE"   # slot may have disappeared

        # ── Step B: fill comment + Phase-1 submit ──
        try:
            self.driver.find_element(By.TAG_NAME, "textarea").send_keys("ak")
        except Exception:
            pass  # textarea not always required

        phase1_xpaths = [
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Submit')]",
            "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button",
            "//button[@type='submit']",
        ]
        submitted = False
        for xp in phase1_xpaths:
            try:
                btn = self.driver.find_element(By.XPATH, xp)
                if btn.is_displayed():
                    self._js_click(btn)
                    submitted = True
                    break
            except Exception:
                continue
        if not submitted:
            return False, "Phase-1 button not found"

        time.sleep(1)

        # ── Step C: Phase-2 final confirmation ──
        confirmed = False
        for xp in [
            "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button",
            "//button[contains(text(), 'Yes') or contains(text(), 'Confirm')]",
        ]:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                self._js_click(btn)
                confirmed = True
                break
            except TimeoutException:
                continue

        if not confirmed:
            return False, "Phase-2 confirm button not found"

        # ── Step D: read result ──
        time.sleep(2)
        try:
            elems = self.driver.find_elements(By.CLASS_NAME, "prntcontent")
            if elems:
                text = " ".join(e.text for e in elems)
                if "επιτυχία" in text:
                    return True, "Reservation Successful 🎯"
                else:
                    # ── GO BACK ONE STEP ──────────────────────────
                    self.driver.back()
                    time.sleep(1)
                    return False, f"Full/Rejected: {text.strip()[:120]}"
            else:
                if "text-danger" in self.driver.page_source:
                    self.driver.back()
                    time.sleep(1)
                    return False, "Generic error (text-danger)"
                return False, "No status element found"
        except Exception as e:
            return False, f"Result parse error: {e}"

    # ── Main sniper loop ──────────────────────
    def snipe(self, target_day: int, target_time: int):
        log.info("=" * 55)
        log.info(f"  🎯  GYM SNIPER  |  Day {target_day}  |  Time {TIME_LABELS.get(target_time, target_time)}")
        log.info(f"  Max attempts: {MAX_ATTEMPTS}  |  Retry delay: {RETRY_DELAY}s")
        log.info("=" * 55)

        start = datetime.now()

        try:
            # ── One-time navigation to time-selection page ──
            self._load_page()
            self._select_gym()
            self._select_day(target_day)
            log.info("✅ Reached time-selection page. Sniping begins...\n")

            for attempt in range(1, MAX_ATTEMPTS + 1):
                elapsed = (datetime.now() - start).seconds
                log.info(f"[{attempt}/{MAX_ATTEMPTS}]  elapsed {elapsed}s  — firing...")

                success, msg = self._attempt_booking(target_time)

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
