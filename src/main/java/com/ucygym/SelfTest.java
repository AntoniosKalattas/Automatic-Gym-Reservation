package com.ucygym;

import com.ucygym.ReservationBot.Result;

import java.time.LocalDate;

/** Checks notifications and walks the booking flow up to the confirm page without booking. */
final class SelfTest {
    private SelfTest() {}

    static boolean run() {
        System.out.println("**************************************************");
        System.out.println("          UCY GYM BOT - SELF DIAGNOSTIC           ");
        System.out.println("**************************************************");

        System.out.println("\n--- 1. Testing Notifications ---");
        Notifier notifier = new Notifier();
        report("Telegram", notifier.sendTelegram("🔥Yoh, the UCY Gym Bot is connected!"));
        report("Email", notifier.sendEmail(Config.get("USER_EMAIL"), "test", "self test email."));

        System.out.println("\n--- 2. Testing Website Navigation ---");
        System.out.println("🚀 Launching Chrome (visible, test mode — nothing gets booked)...");
        int day = LocalDate.now().plusDays(Config.DAYS_AHEAD).getDayOfMonth();
        Result result = ReservationBot.runInFreshBrowser(4, day, false, true);
        System.out.println((result.success() ? "✅ " : "❌ ") + result.message());

        System.out.println(result.success() ? "✅✅ SELF TEST PASSED ✅✅" : "❌❌ SELF TEST FAILED ❌❌");
        return result.success();
    }

    private static void report(String channel, boolean sent) {
        System.out.println(sent ? "✅ " + channel + " sent" : "⚠️ " + channel + " not sent (disabled or failed)");
    }
}
