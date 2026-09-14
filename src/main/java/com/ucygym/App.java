package com.ucygym;

import com.microsoft.playwright.Page;
import com.ucygym.ReservationBot.Result;

import java.nio.file.Paths;
import java.time.DayOfWeek;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.TextStyle;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/** CLI entry point; {@code schedule} (the default) books every day at {@link Config#RUN_AT}. */
public final class App {
    static {
        System.setProperty("java.util.logging.SimpleFormatter.format", "%1$tH:%1$tM:%1$tS  %5$s%6$s%n");
    }

    private static final Logger log = Logger.getLogger(App.class.getName());

    private static final String USAGE = """
            Usage: ./ucygym <command> [options]

              setup          Pick which days to book and the time for each
              schedule       Book automatically every day at 08:00 (default)
              run-once       Run today's booking job right now
              snipe          Keep firing at one slot until it frees up
                               --day N --time T [--attempts N] [--delay SECONDS] [--headless]
              selftest       Test notifications + navigation (books nothing)
              demo           Watch the scheduled booking flow in slow motion (books nothing)
                               [--screenshot FILE]
              sync-profile   Re-copy your Chrome profile (after logging in again in Chrome)
            """;

    private App() {}

    public static void main(String[] args) throws Exception {
        String command = args.length > 0 ? args[0] : "schedule";
        Map<String, String> flags = parseFlags(args);
        switch (command) {
            case "setup" -> Setup.run();
            case "schedule" -> runScheduler();
            case "run-once" -> runJob();
            case "snipe" -> System.exit(snipe(flags) ? 0 : 1);
            case "selftest" -> System.exit(SelfTest.run() ? 0 : 1);
            case "demo" -> System.exit(demo(flags) ? 0 : 1);
            case "sync-profile" -> BrowserSession.syncProfile();
            default -> {
                System.out.print(USAGE);
                if (!command.matches("help|-h|--help")) System.exit(2);
            }
        }
    }

    // ── Scheduler ──

    private static void runScheduler() {
        System.out.println("System Online. Scheduler running (daily at " + Config.RUN_AT + ")...");
        scheduleNext(Executors.newSingleThreadScheduledExecutor());
    }

    /** Re-computed every day rather than a fixed 24h rate, so DST changes don't shift the run time. */
    private static void scheduleNext(ScheduledExecutorService executor) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime next = now.toLocalDate().atTime(Config.RUN_AT);
        if (!next.isAfter(now)) next = next.plusDays(1);

        executor.schedule(() -> {
            try {
                runJob();
            } catch (Exception e) {
                log.log(Level.SEVERE, "Job crashed", e);
            } finally {
                scheduleNext(executor);
            }
        }, Duration.between(now, next).toMillis(), TimeUnit.MILLISECONDS);
    }

    private static void runJob() throws InterruptedException {
        String today = LocalDate.now().toString();
        StateStore state = new StateStore(Config.STATE_FILE);
        if (StateStore.SUCCESS.equals(state.get(today))) {
            log.info("✅ Already booked for " + today + ". Skipping.");
            return;
        }

        LocalDate target = LocalDate.now().plusDays(Config.DAYS_AHEAD);
        String dayName = target.getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH);
        Integer timeOpt = Config.weeklySchedule().get(target.getDayOfWeek());
        if (timeOpt == null) {
            log.info(String.format("📅 Nothing scheduled for %s %02d/%02d — skipping (change days with ./setup.sh).",
                    dayName, target.getDayOfMonth(), target.getMonthValue()));
            return;
        }
        String timeLabel = Config.timeLabel(timeOpt, target.getDayOfWeek());
        log.info(String.format("🚀 Starting reservation for %s %02d/%02d at %s (option %d)...",
                dayName, target.getDayOfMonth(), target.getMonthValue(), timeLabel, timeOpt));

        Notifier notifier = new Notifier();
        String recipient = Config.get("USER_EMAIL");
        boolean resynced = false;
        Result result = null;

        for (int attempt = 1; attempt <= Config.MAX_RETRIES; attempt++) {
            log.info("Attempt " + attempt + "/" + Config.MAX_RETRIES + "...");
            result = ReservationBot.runInFreshBrowser(timeOpt, target.getDayOfMonth(), true, false);

            if (result.success()) {
                log.info("✅ Success: " + result.message());
                state.put(today, StateStore.SUCCESS);
                notifier.alert(true, recipient, "Booked " + dayName + " at " + timeLabel);
                return;
            }
            log.warning("⚠️ Failed: " + result.message());

            if (result.loginExpired()) {
                // The copy may just be stale — real Chrome is often still logged in. Re-copy once and retry.
                if (!resynced && tryResync()) {
                    resynced = true;
                    continue;
                }
                notifier.alert(false, recipient,
                        "Login expired! Log in to the UCY site in Chrome, then run: ./ucygym sync-profile");
                return;
            }
            Thread.sleep(Config.RETRY_DELAY_SECONDS * 1000L);
        }

        state.put(today, StateStore.FAILED);
        notifier.alert(false, recipient,
                "Failed after " + Config.MAX_RETRIES + " attempts.\nLast error: " + result.message());
    }

    private static boolean tryResync() {
        log.info("🔄 Login expired — re-copying the Chrome profile and retrying...");
        try {
            BrowserSession.syncProfile();
            return true;
        } catch (RuntimeException e) {
            log.warning("Profile re-sync failed: " + e.getMessage());
            return false;
        }
    }

    // ── Demo ──

    /**
     * A scheduled slot in a visible slowed-down browser, stopping at the confirm page. Uses the scheduler's
     * target (5 days ahead), or the nearest earlier scheduled day if that one isn't scheduled.
     */
    private static boolean demo(Map<String, String> flags) {
        Map<DayOfWeek, Integer> schedule = Config.weeklySchedule();
        LocalDate target = null;
        Integer timeOpt = null;
        for (int ahead = Config.DAYS_AHEAD; ahead >= 1 && timeOpt == null; ahead--) {
            target = LocalDate.now().plusDays(ahead);
            timeOpt = schedule.get(target.getDayOfWeek());
        }
        if (timeOpt == null) {
            log.warning("No scheduled day in the next " + Config.DAYS_AHEAD + " days — run ./setup.sh first.");
            return false;
        }
        log.info(String.format("🎬 Demo: %s %02d/%02d at %s (option %d) — test mode, nothing gets booked",
                target.getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH), target.getDayOfMonth(),
                target.getMonthValue(), Config.timeLabel(timeOpt, target.getDayOfWeek()), timeOpt));

        try (BrowserSession session = new BrowserSession(false, 700)) {
            Page page = session.page();
            Result result = new ReservationBot(page, true).reserve(timeOpt, target.getDayOfMonth());
            log.info((result.success() ? "✅ " : "❌ ") + result.message());

            String screenshot = flags.get("screenshot");
            if (screenshot != null) {
                page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get(screenshot)).setFullPage(true));
                log.info("📸 Screenshot saved to " + screenshot);
            }
            log.info("Keeping the window open for 15s...");
            page.waitForTimeout(15_000);
            return result.success();
        }
    }

    // ── Sniper ──

    private static boolean snipe(Map<String, String> flags) throws InterruptedException {
        int day = intFlag(flags, "day", Sniper.TARGET_DAY);
        int time = intFlag(flags, "time", Sniper.TARGET_TIME);
        int attempts = intFlag(flags, "attempts", Sniper.MAX_ATTEMPTS);
        int delay = intFlag(flags, "delay", Sniper.RETRY_DELAY_SECONDS);
        try (BrowserSession session = new BrowserSession(flags.containsKey("headless"))) {
            return new Sniper(session.page(), attempts, delay).snipe(day, time);
        }
    }

    /** "--key value" pairs and bare "--flag" switches after the command. */
    private static Map<String, String> parseFlags(String[] args) {
        Map<String, String> flags = new HashMap<>();
        for (int i = 1; i < args.length; i++) {
            if (!args[i].startsWith("--")) continue;
            String key = args[i].substring(2);
            boolean hasValue = i + 1 < args.length && !args[i + 1].startsWith("--");
            flags.put(key, hasValue ? args[++i] : "true");
        }
        return flags;
    }

    private static int intFlag(Map<String, String> flags, String key, int fallback) {
        String value = flags.get(key);
        return value == null ? fallback : Integer.parseInt(value);
    }
}
