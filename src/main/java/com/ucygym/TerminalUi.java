package com.ucygym;

import org.jline.terminal.Attributes;
import org.jline.terminal.Terminal;
import org.jline.terminal.TerminalBuilder;
import org.jline.utils.NonBlockingReader;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

/** Arrow-key pickers for the terminal, in the style of Claude Code / other CLI prompts. */
final class TerminalUi implements AutoCloseable {
    static final String RESET = "\033[0m";
    static final String BOLD = "\033[1m";
    static final String DIM = "\033[2m";
    static final String CYAN = "\033[36m";
    static final String GREEN = "\033[32m";
    static final String YELLOW = "\033[33m";

    private static final String HIDE_CURSOR = "\033[?25l";
    private static final String SHOW_CURSOR = "\033[?25h";
    private static final String CLEAR_TO_END = "\033[J";
    private static final String CLEAR_LINE_END = "\033[K";

    /** Thrown when the user presses Esc, q or Ctrl-C. */
    static final class Cancelled extends RuntimeException {
        Cancelled() {
            super("cancelled");
        }
    }

    private enum Key { UP, DOWN, SPACE, ENTER, CANCEL, CHAR }

    private record KeyPress(Key key, char ch) {
        static KeyPress of(Key key) {
            return new KeyPress(key, '\0');
        }
    }

    private final Terminal terminal;
    private final Attributes savedAttributes;
    private final PrintWriter out;
    private final NonBlockingReader in;
    /** Lines of the live (still-editable) prompt currently on screen, redrawn in place on each key. */
    private int liveLines;

    TerminalUi() throws IOException {
        terminal = TerminalBuilder.builder().system(true).build();
        if (terminal.getType().startsWith(Terminal.TYPE_DUMB)) {
            terminal.close();
            throw new IllegalStateException("Setup needs an interactive terminal — run ./setup.sh directly.");
        }
        savedAttributes = terminal.enterRawMode();
        // Keep Ctrl-C as a key (char 3) so we can restore the terminal before exiting.
        Attributes raw = terminal.getAttributes();
        raw.setLocalFlag(Attributes.LocalFlag.ISIG, false);
        terminal.setAttributes(raw);

        out = terminal.writer();
        in = terminal.reader();
        out.print(HIDE_CURSOR);
        out.flush();
    }

    @Override
    public void close() {
        out.print(SHOW_CURSOR);
        out.flush();
        terminal.setAttributes(savedAttributes);
        try {
            terminal.close();
        } catch (IOException ignored) {
            // nothing useful to do while shutting down
        }
    }

    /** Prints a static line below the prompts. */
    void println(String line) {
        out.print(line + CLEAR_LINE_END + "\r\n");
        out.flush();
        liveLines = 0;
    }

    /** Single choice. Arrows + Enter, or press the option's number. Returns the chosen index. */
    int select(String question, List<String> options, int initial) {
        boolean numbered = options.size() <= 9;
        int cursor = Math.max(0, Math.min(initial, options.size() - 1));
        while (true) {
            List<String> lines = new ArrayList<>();
            lines.add(questionLine(question));
            for (int i = 0; i < options.size(); i++) {
                String label = (numbered ? (i + 1) + ". " : "") + options.get(i);
                lines.add(i == cursor ? CYAN + "❯ " + label + RESET : "  " + label);
            }
            lines.add(DIM + "  ↑/↓ move · enter select" + (numbered ? " · 1-" + options.size() + " pick" : "")
                    + " · esc cancel" + RESET);
            draw(lines);

            KeyPress key = readKey();
            switch (key.key()) {
                case UP -> cursor = (cursor - 1 + options.size()) % options.size();
                case DOWN -> cursor = (cursor + 1) % options.size();
                case ENTER -> {
                    answered(question, options.get(cursor));
                    return cursor;
                }
                case CANCEL -> throw new Cancelled();
                case CHAR -> {
                    int picked = key.ch() - '1';
                    if (numbered && picked >= 0 && picked < options.size()) {
                        answered(question, options.get(picked));
                        return picked;
                    }
                }
                default -> { }
            }
        }
    }

    /**
     * Multiple choice with checkboxes. Space toggles, "a" toggles all, Enter confirms (at least one required).
     * {@code details} (nullable entries) are shown dimmed after each option.
     */
    Set<Integer> multiSelect(String question, List<String> options, List<String> details, Set<Integer> initiallyChecked) {
        Set<Integer> checked = new TreeSet<>(initiallyChecked);
        int cursor = 0;
        String warning = null;
        while (true) {
            List<String> lines = new ArrayList<>();
            lines.add(questionLine(question));
            for (int i = 0; i < options.size(); i++) {
                String box = checked.contains(i) ? GREEN + "◉" + RESET : "◯";
                String detail = details.get(i) != null ? DIM + "  " + details.get(i) + RESET : "";
                String label = i == cursor ? CYAN + options.get(i) + RESET : options.get(i);
                lines.add((i == cursor ? CYAN + "❯ " + RESET : "  ") + box + " " + label + detail);
            }
            if (warning != null) lines.add(YELLOW + "  " + warning + RESET);
            lines.add(DIM + "  ↑/↓ move · space toggle · a all · enter confirm · esc cancel" + RESET);
            draw(lines);

            KeyPress key = readKey();
            warning = null;
            switch (key.key()) {
                case UP -> cursor = (cursor - 1 + options.size()) % options.size();
                case DOWN -> cursor = (cursor + 1) % options.size();
                case SPACE -> toggle(checked, cursor);
                case ENTER -> {
                    if (checked.isEmpty()) {
                        warning = "Pick at least one (space to toggle).";
                        continue;
                    }
                    List<String> names = new ArrayList<>();
                    for (int i : checked) names.add(options.get(i));
                    answered(question, String.join(", ", names));
                    return checked;
                }
                case CANCEL -> throw new Cancelled();
                case CHAR -> {
                    if (key.ch() == 'a') {
                        if (checked.size() == options.size()) {
                            checked.clear();
                        } else {
                            for (int i = 0; i < options.size(); i++) checked.add(i);
                        }
                    } else {
                        int picked = key.ch() - '1';
                        if (picked >= 0 && picked < options.size()) {
                            cursor = picked;
                            toggle(checked, picked);
                        }
                    }
                }
                default -> { }
            }
        }
    }

    boolean confirm(String question) {
        return select(question, List.of("Yes", "No"), 0) == 0;
    }

    private static void toggle(Set<Integer> checked, int index) {
        if (!checked.remove(index)) checked.add(index);
    }

    private static String questionLine(String question) {
        return CYAN + "? " + RESET + BOLD + question + RESET;
    }

    /** Collapses the live prompt into a one-line summary, like "✔ Monday — what time? 13:00". */
    private void answered(String question, String answer) {
        draw(List.of(GREEN + "✔ " + RESET + BOLD + question + RESET + " " + CYAN + answer + RESET));
        liveLines = 0;
    }

    private void draw(List<String> lines) {
        StringBuilder frame = new StringBuilder();
        if (liveLines > 0) frame.append("\033[").append(liveLines).append('F'); // back to the prompt's first line
        frame.append(CLEAR_TO_END);
        for (String line : lines) frame.append(line).append(CLEAR_LINE_END).append("\r\n");
        out.print(frame);
        out.flush();
        liveLines = lines.size();
    }

    private KeyPress readKey() {
        try {
            int c = in.read();
            switch (c) {
                case 27 -> { // Esc alone, or the start of an arrow-key sequence (ESC [ A / ESC O A)
                    int next = in.read(50L);
                    if (next == '[' || next == 'O') {
                        int code = in.read(50L);
                        if (code == 'A') return KeyPress.of(Key.UP);
                        if (code == 'B') return KeyPress.of(Key.DOWN);
                        return new KeyPress(Key.CHAR, '\0');
                    }
                    return KeyPress.of(Key.CANCEL);
                }
                case '\r', '\n' -> {
                    return KeyPress.of(Key.ENTER);
                }
                case ' ' -> {
                    return KeyPress.of(Key.SPACE);
                }
                case 3, 'q', -1 -> { // Ctrl-C, q, end of input
                    return KeyPress.of(Key.CANCEL);
                }
                case 'k' -> {
                    return KeyPress.of(Key.UP);
                }
                case 'j' -> {
                    return KeyPress.of(Key.DOWN);
                }
                default -> {
                    return new KeyPress(Key.CHAR, (char) c);
                }
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
