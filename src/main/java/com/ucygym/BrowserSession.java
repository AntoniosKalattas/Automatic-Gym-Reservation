package com.ucygym;

import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;
import java.util.stream.Stream;

import static java.nio.file.StandardCopyOption.COPY_ATTRIBUTES;
import static java.nio.file.StandardCopyOption.REPLACE_EXISTING;

/**
 * Real Chrome driven by Playwright, running on a private copy of the user's Chrome profile so
 * existing logins and cookies carry over. Chrome 136+ refuses automation on its default
 * user-data dir (and a running Chrome locks it), so we never point Playwright at the original.
 */
public final class BrowserSession implements AutoCloseable {
    private static final Logger log = Logger.getLogger(BrowserSession.class.getName());

    /** Marks a directory as ours, so a re-sync only ever deletes a folder we created. */
    private static final String MARKER = ".ucygym-profile";

    /** Profile subfolders not needed for logins: caches, old tabs, extensions (disabled anyway). */
    private static final Set<String> SKIP_DIRS = Set.of("Sessions", "Extensions", "Crashpad");
    private static final Set<String> SKIP_FILES =
            Set.of("LOCK", "lockfile", "Current Session", "Current Tabs", "Last Session", "Last Tabs");

    /** Playwright defaults that would stop Chrome from decrypting the copied cookies with the OS keychain. */
    private static final List<String> IGNORED_DEFAULT_ARGS = List.of("--use-mock-keychain", "--password-store=basic");

    private final Playwright playwright;
    private final BrowserContext context;
    private final Page page;

    public BrowserSession(boolean headless) {
        this(headless, 0);
    }

    /** @param slowMoMs delay added to every browser action, to make runs watchable */
    public BrowserSession(boolean headless, double slowMoMs) {
        Path profile = profileDir();
        if (!Files.isDirectory(profile.resolve("Default"))) {
            log.info("No bot profile yet — copying your Chrome profile first.");
            syncProfile();
        }

        // We drive the installed Chrome, so skip downloading Playwright's bundled browsers.
        playwright = Playwright.create(new Playwright.CreateOptions()
                .setEnv(Map.of("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD", "1")));
        try {
            context = playwright.chromium().launchPersistentContext(profile,
                    new BrowserType.LaunchPersistentContextOptions()
                            .setChannel("chrome")
                            .setHeadless(headless)
                            .setSlowMo(slowMoMs)
                            .setIgnoreDefaultArgs(IGNORED_DEFAULT_ARGS)
                            .setArgs(List.of("--no-sandbox", "--disable-dev-shm-usage")));
        } catch (RuntimeException e) {
            playwright.close();
            throw e;
        }
        context.setDefaultTimeout(10_000);
        page = context.pages().isEmpty() ? context.newPage() : context.pages().get(0);
    }

    public Page page() {
        return page;
    }

    @Override
    public void close() {
        try {
            context.close();
        } finally {
            playwright.close();
        }
    }

    // ── Profile copy ──

    /** Where the bot's copy of the profile lives (UCYGYM_PROFILE_DIR, default ~/.ucygym/chrome-profile). */
    public static Path profileDir() {
        String custom = Config.get("UCYGYM_PROFILE_DIR");
        return custom != null ? expandHome(custom) : Paths.get(System.getProperty("user.home"), ".ucygym", "chrome-profile");
    }

    /**
     * (Re)copies the real Chrome profile named by CHROME_PROFILE_PATH / CHROME_PROFILE_FOLDER into
     * {@link #profileDir()}. Run it again whenever the UCY login expires: log in with normal Chrome, then sync.
     */
    public static synchronized void syncProfile() {
        ChromeProfile source = sourceProfile();
        if (!Files.isDirectory(source.profile())) {
            throw new IllegalStateException("Chrome profile not found at " + source.profile()
                    + " — set CHROME_PROFILE_PATH (and CHROME_PROFILE_FOLDER) in .env; see chrome://version → Profile Path.");
        }
        if (chromeRunning(source.userDataDir())) {
            log.warning("⚠️ Chrome looks like it's running — close it for a clean copy (recent cookies may be missing).");
        }

        Path dest = profileDir();
        log.info("Copying Chrome profile " + source.profile() + " → " + dest);
        try {
            deleteOwnDir(dest);
            Files.createDirectories(dest);
            Files.createFile(dest.resolve(MARKER));

            // Local State holds the cookie encryption key on Windows/Linux.
            Path localState = source.userDataDir().resolve("Local State");
            if (Files.exists(localState)) Files.copy(localState, dest.resolve("Local State"), REPLACE_EXISTING);

            copyTree(source.profile(), dest.resolve("Default"));
        } catch (IOException e) {
            throw new UncheckedIOException("Profile copy failed: " + e.getMessage(), e);
        }
        log.info("✅ Profile copied.");
    }

    private record ChromeProfile(Path userDataDir, Path profile) {}

    private static ChromeProfile sourceProfile() {
        String path = Config.get("CHROME_PROFILE_PATH");
        String folder = Config.get("CHROME_PROFILE_FOLDER", "Default");
        if (path == null) {
            Path userData = defaultUserDataDir();
            return new ChromeProfile(userData, userData.resolve(folder));
        }
        Path p = expandHome(path);
        // chrome://version shows the profile folder itself (".../Chrome/Profile 1"); accept that too.
        if (Files.exists(p.resolve("Preferences"))) return new ChromeProfile(p.getParent(), p);
        return new ChromeProfile(p, p.resolve(folder));
    }

    private static Path defaultUserDataDir() {
        String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
        Path home = Paths.get(System.getProperty("user.home"));
        if (os.contains("mac")) return home.resolve("Library/Application Support/Google/Chrome");
        if (os.contains("win")) {
            String local = System.getenv("LOCALAPPDATA");
            Path base = local != null ? Paths.get(local) : home.resolve("AppData/Local");
            return base.resolve("Google/Chrome/User Data");
        }
        return home.resolve(".config/google-chrome");
    }

    private static boolean chromeRunning(Path userDataDir) {
        return Files.exists(userDataDir.resolve("SingletonLock"), LinkOption.NOFOLLOW_LINKS)
                || Files.exists(userDataDir.resolve("lockfile"));
    }

    private static void copyTree(Path src, Path dest) throws IOException {
        Files.walkFileTree(src, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                String name = dir.getFileName().toString();
                if (!dir.equals(src) && (SKIP_DIRS.contains(name) || name.contains("Cache"))) {
                    return FileVisitResult.SKIP_SUBTREE;
                }
                Files.createDirectories(dest.resolve(src.relativize(dir).toString()));
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                String name = file.getFileName().toString();
                if (attrs.isSymbolicLink() || name.startsWith("Singleton") || SKIP_FILES.contains(name)) {
                    return FileVisitResult.CONTINUE;
                }
                try {
                    Files.copy(file, dest.resolve(src.relativize(file).toString()), REPLACE_EXISTING, COPY_ATTRIBUTES);
                } catch (IOException e) {
                    log.warning("Skipped " + file + ": " + e.getMessage());
                }
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFileFailed(Path file, IOException e) {
                log.warning("Skipped " + file + ": " + e.getMessage());
                return FileVisitResult.CONTINUE;
            }
        });
    }

    /** Deletes a previous copy — refusing to touch any non-empty folder we didn't create. */
    private static void deleteOwnDir(Path dir) throws IOException {
        if (!Files.exists(dir)) return;
        try (Stream<Path> entries = Files.list(dir)) {
            if (!Files.exists(dir.resolve(MARKER)) && entries.findAny().isPresent()) {
                throw new IOException(dir + " exists and isn't a ucygym profile copy — refusing to overwrite it.");
            }
        }
        try (Stream<Path> walk = Files.walk(dir)) {
            for (Path p : walk.sorted(Comparator.reverseOrder()).toList()) Files.delete(p);
        }
    }

    private static Path expandHome(String path) {
        return Paths.get(path.startsWith("~") ? System.getProperty("user.home") + path.substring(1) : path);
    }
}
