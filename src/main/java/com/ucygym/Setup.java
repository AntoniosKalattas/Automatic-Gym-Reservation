package com.ucygym;

import java.io.IOException;
import java.time.DayOfWeek;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import static com.ucygym.TerminalUi.*;

/** Interactive {@code setup}: pick which days to book and the time slot for each (saved to schedule.json). */
final class Setup {
    private Setup() {}

    static void run() throws IOException {
        Map<DayOfWeek, Integer> current = Config.weeklySchedule();
        List<DayOfWeek> days = Config.BOOKABLE_DAYS;

        try (TerminalUi ui = new TerminalUi()) {
            ui.println("");
            ui.println(BOLD + "🏋️  UCY Gym Bot · Setup" + RESET);
            ui.println(DIM + "Pick the days to book and a time for each. Every day at " + Config.RUN_AT
                    + " the bot books the day " + Config.DAYS_AHEAD + " days ahead." + RESET);
            ui.println("");

            List<String> names = new ArrayList<>();
            List<String> details = new ArrayList<>();
            Set<Integer> checked = new TreeSet<>();
            for (int i = 0; i < days.size(); i++) {
                DayOfWeek day = days.get(i);
                names.add(name(day));
                details.add(current.containsKey(day) ? Config.timeLabel(current.get(day), day) : null);
                if (current.containsKey(day)) checked.add(i);
            }
            Set<Integer> chosen = ui.multiSelect("Which days do you want to book?", names, details, checked);

            Map<DayOfWeek, Integer> schedule = new EnumMap<>(DayOfWeek.class);
            for (int i : chosen) {
                DayOfWeek day = days.get(i);
                int picked = ui.select(name(day) + " — what time?", Config.timeSlots(day), current.getOrDefault(day, 1) - 1);
                schedule.put(day, picked + 1);
            }

            ui.println("");
            ui.println(BOLD + "Your schedule" + RESET);
            schedule.forEach((day, option) ->
                    ui.println("  " + String.format("%-10s", name(day)) + CYAN + Config.timeLabel(option, day) + RESET));
            ui.println("");

            if (!ui.confirm("Save this schedule?")) {
                ui.println(YELLOW + "Nothing saved." + RESET);
                return;
            }
            Config.saveWeeklySchedule(schedule);
            ui.println(GREEN + "✔ Saved to " + Config.SCHEDULE_FILE.getFileName() + RESET);
            ui.println(DIM + "Next: ./ucygym demo (dry run) · ./ucygym schedule (start booking)" + RESET);
            ui.println("");
        } catch (TerminalUi.Cancelled e) {
            System.out.println("Setup cancelled — nothing saved.");
        }
    }

    private static String name(DayOfWeek day) {
        return day.getDisplayName(TextStyle.FULL, Locale.ENGLISH);
    }
}
