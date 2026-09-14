package com.ucygym;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.PlaywrightException;
import com.microsoft.playwright.options.SelectOption;
import com.microsoft.playwright.options.WaitForSelectorState;

import java.util.List;
import java.util.Locale;
import java.util.logging.Logger;

/** Books one gym slot on the UCY sports-center site. */
public final class ReservationBot {
    private static final Logger log = Logger.getLogger(ReservationBot.class.getName());

    private static final String HOME_FIX_XPATH = "/html/body/div[2]/div/div[2]/div[1]/ul/li[1]/a";
    private static final String NEXT_MONTH_XPATH = "//*[@id=\"contentRow\"]/center/table[2]/tbody/tr/td[2]/div/button";
    private static final List<String> PHASE1_BUTTONS = List.of(
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Submit')]",
            "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div/button",
            "//button[@type='submit']");
    static final String FINAL_CONFIRM_XPATH = "/html/body/div[2]/div/div[4]/form/table/tbody/tr[5]/td/div[1]/button";
    static final String CONFIRM_FALLBACK_XPATH = "//button[contains(text(), 'Yes') or contains(text(), 'Confirm')]";
    private static final String SUCCESS_TEXT = "επιτυχία";

    public record Result(boolean success, String message, boolean loginExpired) {
        static Result ok(String message) {
            return new Result(true, message, false);
        }

        static Result fail(String message) {
            return new Result(false, message, false);
        }
    }

    /** A step that can't continue; the message is the user-facing reason. */
    static final class StepFailed extends RuntimeException {
        final boolean loginExpired;

        StepFailed(String message) {
            this(message, false);
        }

        StepFailed(String message, boolean loginExpired) {
            super(message);
            this.loginExpired = loginExpired;
        }
    }

    private final Page page;
    private final boolean testMode;

    /** In test mode the bot stops at the confirm page and books nothing. */
    public ReservationBot(Page page, boolean testMode) {
        this.page = page;
        this.testMode = testMode;
    }

    /** Opens a fresh Chrome on the bot profile, tries one reservation, closes it. */
    public static Result runInFreshBrowser(int timeOpt, int day, boolean headless, boolean testMode) {
        try (BrowserSession session = new BrowserSession(headless)) {
            return new ReservationBot(session.page(), testMode).reserve(timeOpt, day);
        } catch (RuntimeException e) {
            return Result.fail("Crash: " + e.getMessage());
        }
    }

    public Result reserve(int timeOpt, int day) {
        try {
            open();
            selectGym();
            selectDay(day);
            if (!selectTime(timeOpt)) return Result.fail("Time option " + timeOpt + " full or unavailable.");
            fillComment();
            if (!submitPhase1()) return Result.fail("Phase 1 Submit button not found");
            page.waitForTimeout(1000);

            Locator confirm = findConfirmButton();
            if (confirm == null) return Result.fail("Final Confirm button not found.");
            if (testMode) return Result.ok("Test mode: reached the confirm page (nothing booked).");

            confirm.scrollIntoViewIfNeeded();
            page.waitForTimeout(500);
            jsClick(confirm);
            page.waitForTimeout(2000);
            return readResult();
        } catch (StepFailed e) {
            return new Result(false, e.getMessage(), e.loginExpired);
        } catch (PlaywrightException e) {
            return Result.fail("Crash: " + e.getMessage());
        }
    }

    // ── Steps (package-private so Sniper can reuse them) ──

    void open() {
        page.navigate(Config.RESERVATION_URL);
        if (page.url().toLowerCase(Locale.ROOT).contains("login")) {
            throw new StepFailed("Login session expired. Log in to the UCY site in Chrome, then run sync-profile.", true);
        }
    }

    void selectGym() {
        if (!trySelectGym()) {
            log.warning("Applying 'Home Button' fix...");
            if (!tryStep(() -> page.locator("xpath=" + HOME_FIX_XPATH).click())) throw new StepFailed("Nav fix failed.");
            page.waitForTimeout(2000);
            page.navigate(Config.RESERVATION_URL);
            if (!trySelectGym()) throw new StepFailed("Could not select Gymnasium.");
        }
        tryStep(() -> page.locator("input[type='checkbox']").first().check());
        tryStep(() -> page.locator("button[type='submit']").first().click());
    }

    private boolean trySelectGym() {
        // Gymnasium is the 4th option of the facility dropdown.
        return tryStep(() -> page.locator("select:has(option:nth-child(4))").first()
                .selectOption(new SelectOption().setIndex(3)));
    }

    void selectDay(int day) {
        Locator dayButton = page.locator("xpath=//button[normalize-space()='" + day + "']").first();
        if (tryStep(dayButton::click)) return;

        // Not on this month's calendar — flip to next month and try again.
        boolean found = tryStep(() -> {
            page.locator("xpath=" + NEXT_MONTH_XPATH).click(new Locator.ClickOptions().setTimeout(2000));
            page.waitForTimeout(3000);
            dayButton.click();
        });
        if (!found) throw new StepFailed("Day " + day + " not found.");
    }

    boolean selectTime(int option) {
        if (!tryStep(() -> page.locator("select").first().waitFor())) return false;
        return tryStep(() -> page.locator("xpath=//select[option[" + option + "]]").first()
                .selectOption(new SelectOption().setIndex(option - 1), new Locator.SelectOptionOptions().setTimeout(3000)));
    }

    void fillComment() {
        Locator comment = page.locator("textarea");
        if (comment.count() > 0) comment.first().fill("ak");
    }

    boolean submitPhase1() {
        for (String xpath : PHASE1_BUTTONS) {
            Locator button = page.locator("xpath=" + xpath).first();
            if (button.count() > 0 && button.isVisible()) {
                jsClick(button);
                return true;
            }
        }
        return false;
    }

    /** The final confirm button (waiting up to the default timeout for it), or null. */
    Locator findConfirmButton() {
        Locator primary = page.locator("xpath=" + FINAL_CONFIRM_XPATH).first();
        if (tryStep(() -> primary.waitFor(new Locator.WaitForOptions().setState(WaitForSelectorState.ATTACHED)))) {
            return primary;
        }
        Locator fallback = page.locator("xpath=" + CONFIRM_FALLBACK_XPATH).first();
        return fallback.count() > 0 ? fallback : null;
    }

    /**
     * Reads the result page: <p|li class="prntcontent"> holds the success text or the rejection reason.
     * The confirm POST can still be navigating/redirecting when we get here, so retry until the page settles.
     */
    Result readResult() {
        for (int attempt = 1; ; attempt++) {
            try {
                page.waitForLoadState();
                List<String> texts = page.locator(".prntcontent").allInnerTexts();
                if (!texts.isEmpty()) {
                    String full = String.join(" ", texts).trim();
                    return full.contains(SUCCESS_TEXT) ? Result.ok("Reservation Successful") : Result.fail("Failed: " + full);
                }
                if (page.content().contains("text-danger")) return Result.fail("Failed (Generic Error)");
                if (attempt >= 5) return Result.fail("Unknown Result (No status message found)");
            } catch (PlaywrightException e) {
                if (attempt >= 5 || !isNavigationError(e)) throw e;
            }
            page.waitForTimeout(1000);
        }
    }

    private static boolean isNavigationError(PlaywrightException e) {
        String message = String.valueOf(e.getMessage());
        return message.contains("Execution context was destroyed") || message.contains("navigat");
    }

    /** JS click — works even when the button is covered or off-screen. */
    static void jsClick(Locator element) {
        try {
            element.evaluate("el => el.click()");
        } catch (PlaywrightException e) {
            // The click can navigate away and destroy the JS context mid-call; that still counts.
            if (!isNavigationError(e)) throw e;
        }
    }

    private static boolean tryStep(Runnable step) {
        try {
            step.run();
            return true;
        } catch (PlaywrightException e) {
            return false;
        }
    }
}
