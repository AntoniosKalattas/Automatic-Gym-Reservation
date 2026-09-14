# Automatic-Gym-Reservation

Automatic-Gym-Reservation books gym sessions at the University of Cyprus Athletic Center for you. It's a Java app that drives your own Google Chrome with [Playwright](https://playwright.dev/java/), and it reuses your existing Chrome login, so the UCY site doesn't ask you to sign in again.

## Features

- **Automated reservations**: every day at 08:00 it books the day 5 days ahead, at the time you picked for that weekday.
- **Interactive setup**: choose days and times from arrow-key menus.
- **Uses your Chrome login**: works on a copy of your Chrome profile, so no passwords are stored.
- **Sniper mode**: keeps retrying a full slot until someone cancels.
- **Notifications**: Telegram and/or email alerts on success or failure.
- **Self-test and demo**: check everything, or watch the whole flow, without booking anything.

## Prerequisites

- [JDK 17+](https://adoptium.net/) and [Maven](https://maven.apache.org/)
- [Google Chrome](https://www.google.com/chrome/), logged in to the UCY sports-center site

No ChromeDriver is needed.

## Quick start

```bash
git clone https://github.com/AntoniosKalattas/UCYGYM_BOT.git
cd UCYGYM_BOT
./setup.sh            # pick your days & times
./ucygym selftest     # check login + notifications (books nothing)
./ucygym schedule     # start booking every day at 08:00
```

On Windows use `setup.cmd` and `ucygym.cmd` instead. The first run builds the app automatically.

## Choosing days & times

`./setup.sh` walks you through it:

```
✔ Which days do you want to book? Monday, Tuesday, Thursday
? Tuesday — what time?
  1. 07:45
  2. 09:30
  3. 11:15
  4. 13:00
❯ 5. 14:45
  6. 16:45
  7. 18:30
  8. 20:15
  ↑/↓ move · enter select · 1-8 pick · esc cancel
```

Your choices are saved to `schedule.json`. Run `./setup.sh` again anytime to change them; a running scheduler picks up the change at its next run. Days you don't pick are skipped.

## Your Chrome login

Chrome refuses to be automated on its real profile folder, so the bot works on a **copy** of your profile in `~/.ucygym/chrome-profile`:

- The profile is copied automatically on first run.
- If the UCY login expires, the bot re-copies once by itself. If you're logged out in Chrome too, log in to the UCY site in Chrome, then run `./ucygym sync-profile`.
- For the cleanest copy, close Chrome before `sync-profile`.

By default the bot copies Chrome's `Default` profile. To use another profile, open `chrome://version` in Chrome, copy the **Profile Path**, and set it in `.env`:

```
CHROME_PROFILE_PATH="/Users/you/Library/Application Support/Google/Chrome/Profile 1"
```

## Notifications (optional)

Create a `.env` file in the project root. Every notification setting is optional.

```
USER_EMAIL="<where alerts go>"

# Email (sent on failures)
EMAIL_USER="<your_gmail>"
EMAIL_PASSWORD="<your_app_password>"

# Telegram (sent on success and failure)
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN="<bot token>"
TELEGRAM_CHAT_ID="<chat id>"
```

For Gmail you need an **App Password**:
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Create an app password (e.g. "Gym Reservation"): https://myaccount.google.com/apppasswords
3. Put the 16-character password in `EMAIL_PASSWORD`.

## Commands

| Command | What it does |
|---|---|
| `./setup.sh` | Pick days & times |
| `./ucygym schedule` | Book every day at 08:00 (default command) |
| `./ucygym run-once` | Run today's booking right now |
| `./ucygym demo` | Watch the booking flow in slow motion (books nothing) |
| `./ucygym selftest` | Test notifications + navigation (books nothing) |
| `./ucygym snipe --day 15 --time 5` | Keep retrying a full slot until it frees up (`--attempts`, `--delay`, `--headless`) |
| `./ucygym sync-profile` | Re-copy your Chrome profile after logging in again |

To keep the scheduler running in the background, use `nohup ./ucygym schedule &`. The computer has to be awake at 08:00.

## Troubleshooting

- **"Login session expired"**: log in to the UCY site in Chrome, then `./ucygym sync-profile`.
- **"...έχει φτάσει το μέγιστο της χωρητικότητας..."**: the slot is full. Pick another time with `./setup.sh`, or try `./ucygym snipe`.
- **Element not found**: the UCY site may have changed its layout. Update the selectors in `src/main/java/com/ucygym/ReservationBot.java`.
