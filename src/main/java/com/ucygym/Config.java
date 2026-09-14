package com.ucygym;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;
import com.google.gson.reflect.TypeToken;
import io.github.cdimascio.dotenv.Dotenv;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Type;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import static java.time.DayOfWeek.*;

/** Shared configuration: .env values, the weekly schedule and site constants. */
public final class Config {
    public static final String RESERVATION_URL =
            "https://applications2.ucy.ac.cy/sportscenter/online_reservations_pck2.insert_reservation?p_lang=";

    /** Project root, where .env, schedule.json and reservation_state.json live. */
    public static final Path PROJECT_ROOT = findProjectRoot();
    public static final Path STATE_FILE = PROJECT_ROOT.resolve("reservation_state.json");
    /** Days and times to book, written by {@code setup}. */
    public static final Path SCHEDULE_FILE = PROJECT_ROOT.resolve("schedule.json");

    // --- Scheduler ---
    public static final LocalTime RUN_AT = LocalTime.of(8, 0);
    public static final int DAYS_AHEAD = 5;
    public static final int MAX_RETRIES = 5;
    public static final int RETRY_DELAY_SECONDS = 60;

    /** The gym takes bookings Monday to Saturday. */
    public static final List<DayOfWeek> BOOKABLE_DAYS = List.of(MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY);

    /** Used until {@code setup} writes schedule.json. */
    private static final Map<DayOfWeek, Integer> DEFAULT_SCHEDULE = Map.of(
            MONDAY, 4,
            TUESDAY, 5,
            WEDNESDAY, 8,
            THURSDAY, 4,
            FRIDAY, 4,
            SATURDAY, 3
    );

    // A time option is the n-th entry (1-based) of the site's time dropdown for that day.
    private static final List<String> WEEKDAY_TIMES =
            List.of("07:45", "09:30", "11:15", "13:00", "14:45", "16:45", "18:30", "20:15");
    private static final List<String> SATURDAY_TIMES = List.of("08:45", "10:30", "12:15");

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Type SCHEDULE_TYPE = new TypeToken<Map<String, Integer>>() {}.getType();

    private static final Dotenv ENV = Dotenv.configure()
            .directory(PROJECT_ROOT.toString())
            .ignoreIfMissing()
            .load();

    private Config() {}

    /** Value from the process environment or .env, or null if unset/blank. */
    public static String get(String key) {
        String value = ENV.get(key);
        return value == null || value.isBlank() ? null : value.trim();
    }

    public static String get(String key, String fallback) {
        String value = get(key);
        return value != null ? value : fallback;
    }

    /**
     * Day → time option to book; days not in the map are skipped. Re-read on every call, so a
     * running scheduler picks up changes from {@code setup} without a restart.
     */
    public static Map<DayOfWeek, Integer> weeklySchedule() {
        if (!Files.exists(SCHEDULE_FILE)) return new EnumMap<>(DEFAULT_SCHEDULE);
        try {
            Map<String, Integer> raw = GSON.fromJson(Files.readString(SCHEDULE_FILE), SCHEDULE_TYPE);
            Map<DayOfWeek, Integer> schedule = new EnumMap<>(DayOfWeek.class);
            if (raw != null) {
                raw.forEach((day, option) -> {
                    if (option != null) schedule.put(DayOfWeek.valueOf(day.toUpperCase(Locale.ROOT)), option);
                });
            }
            return schedule;
        } catch (IOException | JsonParseException | IllegalArgumentException e) {
            throw new IllegalStateException("Can't read " + SCHEDULE_FILE + " — run ./setup.sh again (" + e.getMessage() + ")", e);
        }
    }

    public static void saveWeeklySchedule(Map<DayOfWeek, Integer> schedule) {
        Map<String, Integer> raw = new LinkedHashMap<>();
        new EnumMap<>(schedule).forEach((day, option) -> raw.put(day.name(), option));
        try {
            Files.writeString(SCHEDULE_FILE, GSON.toJson(raw) + "\n");
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    /** The time dropdown's entries for a day, in order. */
    public static List<String> timeSlots(DayOfWeek day) {
        return day == SATURDAY ? SATURDAY_TIMES : WEEKDAY_TIMES;
    }

    /** Human label for a time option, e.g. 4 on a weekday → "13:00". */
    public static String timeLabel(int option, DayOfWeek day) {
        List<String> times = timeSlots(day);
        return option >= 1 && option <= times.size() ? times.get(option - 1) : "option " + option;
    }

    /** Next date (today or later) falling on the given day of the month, or null if none within two months. */
    public static LocalDate nextDateWithDay(int dayOfMonth) {
        LocalDate date = LocalDate.now();
        for (int i = 0; i < 62; i++, date = date.plusDays(1)) {
            if (date.getDayOfMonth() == dayOfMonth) return date;
        }
        return null;
    }

    /** UCYGYM_HOME, else the nearest of cwd / its parents (3 levels) holding pom.xml or .env. */
    private static Path findProjectRoot() {
        String home = System.getenv("UCYGYM_HOME");
        if (home != null && !home.isBlank()) return Paths.get(home).toAbsolutePath();

        Path cwd = Paths.get("").toAbsolutePath();
        Path dir = cwd;
        for (int i = 0; i < 3 && dir != null; i++, dir = dir.getParent()) {
            if (Files.exists(dir.resolve("pom.xml")) || Files.exists(dir.resolve(".env"))) return dir;
        }
        return cwd;
    }
}
