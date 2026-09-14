package com.ucygym;

import com.google.gson.Gson;
import com.google.gson.JsonParseException;
import com.google.gson.reflect.TypeToken;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Type;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/** Per-day SUCCESS/FAILED history in reservation_state.json. */
final class StateStore {
    static final String SUCCESS = "SUCCESS";
    static final String FAILED = "FAILED";

    private static final Gson GSON = new Gson();
    private static final Type MAP_TYPE = new TypeToken<LinkedHashMap<String, String>>() {}.getType();

    private final Path file;

    StateStore(Path file) {
        this.file = file;
    }

    String get(String date) {
        return read().get(date);
    }

    void put(String date, String status) {
        Map<String, String> state = read();
        state.put(date, status);
        try {
            Files.writeString(file, GSON.toJson(state));
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private Map<String, String> read() {
        if (!Files.exists(file)) return new LinkedHashMap<>();
        try {
            Map<String, String> state = GSON.fromJson(Files.readString(file), MAP_TYPE);
            return state != null ? state : new LinkedHashMap<>();
        } catch (IOException | JsonParseException e) {
            return new LinkedHashMap<>();
        }
    }
}
