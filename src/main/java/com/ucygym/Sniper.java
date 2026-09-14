package com.ucygym;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.PlaywrightException;
import com.microsoft.playwright.options.WaitForSelectorState;
import com.ucygym.ReservationBot.Result;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.logging.Logger;

/** Reaches the confirm page once, then keeps firing confirm until a slot frees up. */
public final class Sniper {
    private static final Logger log = Logger.getLogger(Sniper.class.getName());

    // ─────────────────────────────────────────────
    //  SNIPER DEFAULTS — or pass --day/--time/--attempts/--delay
    // ─────────────────────────────────────────────
    public static final int TARGET_DAY = 3;           // Day of the month (e.g. 15)
    public static final int TARGET_TIME = 5;          // Time option index (see Config time reference)
    public static final int MAX_ATTEMPTS = 500;       // How many times to keep hammering before giving up
    public static final int RETRY_DELAY_SECONDS = 5;  // Seconds between retries (keep ≥3 to avoid bans)

    private static final List<String> CONFIRM_BUTTONS = List.of(
            ReservationBot.FINAL_CONFIRM_XPATH,
            ReservationBot.CONFIRM_FALLBACK_XPATH,
            "//button[@type='submit']");

    private final Page page;
    private final ReservationBot bot;
    private final int maxAttempts;
    private final int retryDelaySeconds;

    public Sniper(Page page, int maxAttempts, int retryDelaySeconds) {
        this.page = page;
        this.bot = new ReservationBot(page, false);
        this.maxAttempts = maxAttempts;
        this.retryDelaySeconds = retryDelaySeconds;
    }

    public boolean snipe(int day, int timeOpt) throws InterruptedException {
        LocalDate date = Config.nextDateWithDay(day);
        String label = date != null ? Config.timeLabel(timeOpt, date.getDayOfWeek()) : "option " + timeOpt;
        log.info("=".repeat(55));
        log.info(String.format("  🎯  GYM SNIPER  |  Day %d  |  Time %s", day, label));
        log.info(String.format("  Max attempts : %d  |  Retry delay : %ds", maxAttempts, retryDelaySeconds));
        log.info("=".repeat(55));

        Instant start = Instant.now();
        try {
            // ── Navigate to the time-selection page and submit the form (once) ──
            bot.open();
            bot.selectGym();
            bot.selectDay(day);
            if (!bot.selectTime(timeOpt)) {
                log.severe("🔴  Time option not found on page.");
                return false;
            }
            bot.fillComment();
            if (!bot.submitPhase1()) {
                log.severe("🔴  Phase 1 failed — couldn't reach confirm page.");
                return false;
            }
            page.waitForTimeout(1000);
            log.info("✅ On confirm page. Hammering confirm button...");

            // ── Retry the confirm click until it works ──
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                long elapsed = Duration.between(start, Instant.now()).toSeconds();
                log.info(String.format("[%d/%d]  %ds elapsed  — firing...", attempt, maxAttempts, elapsed));

                Result result = retryConfirm();
                if (result.success()) {
                    log.info("🟢  " + result.message() + " 🎯");
                    log.info("   Total attempts : " + attempt);
                    log.info("   Total time     : " + elapsed + "s");
                    return true;
                }
                log.info(String.format("   ↩  %s  — retrying in %ds", result.message(), retryDelaySeconds));
                Thread.sleep(retryDelaySeconds * 1000L);
            }
            log.warning("🔴  Gave up after " + maxAttempts + " attempts.");
            return false;
        } catch (ReservationBot.StepFailed | PlaywrightException e) {
            log.severe("🔴  Fatal: " + e.getMessage());
            return false;
        }
    }

    /** Clicks confirm on the current page; on rejection steps back to the confirm page for the next try. */
    private Result retryConfirm() {
        for (String xpath : CONFIRM_BUTTONS) {
            Locator button = page.locator("xpath=" + xpath).first();
            try {
                button.waitFor(new Locator.WaitForOptions().setState(WaitForSelectorState.ATTACHED).setTimeout(5000));
            } catch (PlaywrightException e) {
                continue;
            }
            try {
                button.scrollIntoViewIfNeeded();
                page.waitForTimeout(300);
                ReservationBot.jsClick(button);
                page.waitForTimeout(2000);

                Result result = bot.readResult();
                if (!result.success()) {
                    // Slot full / rejected — go back ONE page to the confirm page.
                    page.goBack();
                    page.waitForTimeout(1000);
                }
                return result;
            } catch (PlaywrightException e) {
                return Result.fail("Error: " + e.getMessage());
            }
        }
        return Result.fail("Confirm button not found on page");
    }
}
