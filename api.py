import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SCHEDULE_FILE = "schedule.json"
STATE_FILE = "reservation_state.json"

DEFAULT_SCHEDULE = {
    "0": 4,   # Monday
    "1": 6,   # Tuesday
    "2": 3,   # Wednesday
    "3": 4,   # Thursday
    "4": 6,   # Friday
    "5": 11,  # Saturday
}

WEEKDAY_TIME_OPTIONS = [
    {"value": 1, "label": "07:45"},
    {"value": 2, "label": "09:30"},
    {"value": 3, "label": "11:15"},
    {"value": 4, "label": "13:00"},
    {"value": 5, "label": "14:45"},
    {"value": 6, "label": "16:45"},
    {"value": 7, "label": "18:30"},
    {"value": 8, "label": "20:15"},
]

SATURDAY_TIME_OPTIONS = [
    {"value": 1, "label": "08:45"},
    {"value": 2, "label": "10:30"},
    {"value": 3, "label": "12:15"},
]

DAY_NAMES = {
    "0": "Monday",
    "1": "Tuesday",
    "2": "Wednesday",
    "3": "Thursday",
    "4": "Friday",
    "5": "Saturday",
}


def read_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        save_schedule(DEFAULT_SCHEDULE)
        return DEFAULT_SCHEDULE.copy()
    with open(SCHEDULE_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return DEFAULT_SCHEDULE.copy()


def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)


def read_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


@app.route("/schedule", methods=["GET"])
def get_schedule():
    schedule = read_schedule()
    return jsonify({
        "schedule": schedule,
        "day_names": DAY_NAMES,
        "weekday_options": WEEKDAY_TIME_OPTIONS,
        "saturday_options": SATURDAY_TIME_OPTIONS,
    })


@app.route("/schedule", methods=["POST"])
def update_schedule():
    data = request.get_json(silent=True)
    if not data or "schedule" not in data:
        return jsonify({"error": "Missing 'schedule' key"}), 400

    incoming = data["schedule"]
    validated = {}
    for day_str, option in incoming.items():
        if str(day_str) not in DAY_NAMES:
            return jsonify({"error": f"Invalid day key: {day_str}"}), 400
        try:
            validated[str(day_str)] = int(option)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid option for day {day_str}"}), 400

    save_schedule(validated)
    return jsonify({"success": True, "schedule": validated})


@app.route("/status", methods=["GET"])
def get_status():
    state = read_state()
    # Return sorted by date descending, last 14 entries
    sorted_entries = sorted(state.items(), reverse=True)[:14]
    return jsonify({"status": dict(sorted_entries)})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"API running on http://0.0.0.0:{port}")
    print("Point ngrok at this port: ngrok http 5001")
    app.run(host="0.0.0.0", port=port, debug=False)
