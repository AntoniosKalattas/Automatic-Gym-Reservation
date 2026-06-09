import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

# ─────────────────────────────────────────────
#  SNIPER CONFIGURATION — edit these
# ─────────────────────────────────────────────
TARGET_DAY   = 8      # Day of the month (e.g. 15)
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
        self.playwright = sync_playwright().start()
        self._init_browser()
        self.page.set_default_timeout(10000)  # Global 10-second timeout for element operations
    def _init_browser(self):
        # Pointing to the actual firefox binary inside the Tor Browser folder
        TOR_EXE_PATH = r"/home/antoniosk/Downloads/tor-browser-linux-x86_64-15.0.15/tor-browser/Browser/firefox" 

        # Launching the Tor Browser (using the Firefox engine)
        self.browser = self.playwright.firefox.launch(
            headless=HEADLESS, 
            executable_path=TOR_EXE_PATH,
            args=["--disable-dev-shm-usage"]
        )
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
    def close(self):
        self.context.close()
        if hasattr(self, 'browser'):
            self.browser.close()
        self.playwright.stop()

    def _click(self, selector: str, timeout: int = 10000):
        try:
            # Playwright automatically waits for visibility and clickability
            self.page.locator(selector).first.click(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    # ── One-time setup: navigate to the time-selection page ──
    def _load_page(self):
        self.page.goto(self.BASE_URL)
        if "login" in self.page.url:
            raise RuntimeError("Login session expired — please log in manually first.")

    def _select_gym(self):
        if not self._click("select option:nth-child(4)"):
            fix_xpath = "xpath=/html/body/div[2]/div/div[2]/div[1]/ul/li[1]/a"
            if self._click(fix_xpath):
                time.sleep(2)
                self.page.goto(self.BASE_URL)
                if not self._click("select option:nth-child(4)"):
                    raise RuntimeError("Could not select Gymnasium even after nav-fix.")
            else:
                raise RuntimeError("Nav-fix click failed.")
        
        self._click("input[type='checkbox']")
        self._click("button[type='submit']")

    def _select_day(self, day: int):
        day_xpath = f"xpath=//button[normalize-space()='{day}']"
        try:
            self.page.locator(day_xpath).click(timeout=5000)
        except PlaywrightTimeoutError:
            try:
                nb = self.page.locator('xpath=//*[@id="contentRow"]/center/table[2]/tbody/tr/td[2]/div/button')
                nb.click()
                time.sleep(3)
                self.page.locator(day_xpath).click(timeout=5000)
            except Exception:
                raise RuntimeError(f"Day {day} not found on calendar.")

    # ── Phase 1: select time, fill form, click first submit (run ONCE) ──
    def _submit_phase1(self, time_opt: int) -> bool:
        try:
            self.page.wait_for_selector("select", timeout=10000)
            self.page.locator(f"xpath=//select/option[{time_opt}]").click()
        except Exception:
            log.error("Time option not found on page.")
            return False

        try:
            self.page.locator("textarea").fill("ak")
        except Exception:
            pass  # optional field

        for xp in [
            "xpath=//button[contains(text(), 'Next')]",
            "xpath=//button[contains(text(), 'Submit')]",
            "xpath=/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button",
            "xpath=//button[@type='submit']",
        ]:
            loc = self.page.locator(xp).first
            try:
                if loc.is_visible():
                    loc.click(force=True)  # force=True replaces JS clicks
                    time.sleep(1)
                    return True
            except Exception:
                continue

        log.error("Phase-1 submit button not found.")
        return False

    # ── Phase 2: click confirm button and check result (retried in loop) ──
    def _retry_confirm(self) -> tuple[bool, str]:
        for xp in [
            "xpath=/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button",
            "xpath=//button[contains(text(), 'Yes') or contains(text(), 'Confirm')]",
            "xpath=//button[@type='submit']",
        ]:
            try:
                loc = self.page.locator(xp).first
                # Wait for it to exist in the DOM
                loc.wait_for(state="attached", timeout=5000)
                loc.scroll_into_view_if_needed()
                time.sleep(0.3)
                loc.click(force=True)
                time.sleep(2)

                # Check result
                elems = self.page.locator(".prntcontent")
                if elems.count() > 0:
                    text = " ".join(elems.all_inner_texts())
                    if "επιτυχία" in text:
                        return True, "Reservation Successful 🎯"
                    
                    # Slot full / rejected — go back ONE page to the confirm page
                    self.page.go_back()
                    time.sleep(1)
                    return False, f"Rejected: {text.strip()[:120]}"

                if "text-danger" in self.page.content():
                    self.page.go_back()
                    time.sleep(1)
                    return False, "Generic error (text-danger)"

                # No recognizable result — go back to be safe
                self.page.go_back()
                time.sleep(1)
                return False, "No status element found"

            except PlaywrightTimeoutError:
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
            self.close()


if __name__ == "__main__":
    sniper = GymSniper()
    sniper.snipe(TARGET_DAY, TARGET_TIME)