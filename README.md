# LockIn Timer

> A dark-themed study timer for people who take their focus seriously.

LockIn helps you build structured study sessions, track your progress across multiple profiles, and stay motivated with XP, levels, and daily challenges — all in a clean desktop app with no internet connection required.

---

## Features

### ⏱ Scheduled Mode
Build a custom session by stacking work and break blocks in any order. A live countdown clock, progress bar, and block queue keep you oriented while you study. Full pause, skip, and stop controls at all times.

### 🆓 Free Mode
A stopwatch-based mode for open-ended study sessions. Start the timer and go — take breaks manually whenever you need, get milestone pings every 25 minutes, and end the session when you're done.

### 👤 Multiple Profiles
Each profile has its own color, avatar, default durations, inactivity timeout, study history, and goal settings. All data is saved locally as JSON — no accounts, no cloud.

### 📊 My Stats
Per-profile stats including total study time, streak, session count, average session length, and a bar chart of daily hours (7-day and 30-day toggle).

### 🌐 General Stats
A combined view across all profiles — total hours, sessions, streaks, and a merged daily bar chart showing your full study activity.

### 🏆 Goals & Rewards
- **XP & Levels** — earn 100 XP per hour studied, progress through 6 levels from 🌱 Beginner to 👑 Legend
- **Daily Challenge** — a new challenge every day with bonus XP on completion, resets at midnight
- **Streaks** — per-profile flame tracker (❄️ → 🔥 → 🔥🔥 → 🔥🔥🔥) with a 7-day dot history
- **Badges** — 15 unlockable achievements including First Step, Night Owl, Marathon, Week Warrior, and Legend

### 🪟 Mini Window
A compact always-on-top floating widget you can keep visible over other apps. Shows the current block type, live timer, pause button, and (in Free Mode) a break toggle. Pulses orange on inactivity and green when a session completes, then auto-closes after 5 seconds.

### 🔔 Inactivity Detection
If there's no keyboard or mouse activity for a configurable period, the timer auto-pauses and an alert dialog fires. Dismissing the alert auto-resumes. Timeout is set per profile (default: 60 seconds).

### 🎵 Procedural Lo-Fi Sounds
Soft synthesized tones for session start, break start, completion, and inactivity alerts. No audio files — all generated in real time. Master volume adjustable in `sound_service.py`.

---

## Getting Started

### Run from source

```bash
# Clone the repo
git clone https://github.com/your-username/lockin-timer.git
cd lockin-timer

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

**Requirements:** Python 3.10+, Windows (pynput activity detection is Windows-optimized)

### Download the executable

Pre-built releases are available on the [Releases](../../releases) page — no Python installation needed.

---

## Building the Executable

```bash
pip install pyinstaller
cd lockin-timer
build.bat
```

Output: `dist/LockIn-vX.X.X.exe`

---

## Project Structure

```
lockin-timer/
├── main.py                        # Entry point
├── config.py                      # Colors, fonts, constants
├── requirements.txt
├── build.bat                      # One-click PyInstaller build script
├── lockin.spec                    # PyInstaller spec
├── icon/
│   └── logo_icon.ico              # App icon
├── data/
│   ├── profiles/                  # Per-profile JSON files (auto-created)
│   └── _app_data.json             # Challenge XP, claimed rewards (auto-created)
├── models/
│   ├── profile.py                 # Profile dataclass + stat helpers
│   ├── schedule.py                # Schedule and Block models
│   └── session.py                 # Session record model
├── services/
│   ├── storage_service.py         # Load/save profiles and app data
│   ├── timer_service.py           # Countdown timer with tick callbacks
│   ├── schedule_service.py        # Drives blocks through a schedule
│   ├── activity_service.py        # Background inactivity watcher
│   └── sound_service.py           # Procedural audio synthesis
└── ui/
    ├── main_window.py             # App shell, navigation, tab management
    ├── profile_screen.py          # Profile select, create, edit, delete
    ├── mode_select_screen.py      # Scheduled vs Free Mode picker
    ├── timer_screen.py            # Scheduled session UI
    ├── free_mode_screen.py        # Free mode stopwatch UI
    ├── schedule_builder.py        # Block list builder widget
    ├── mini_window.py             # Floating always-on-top widget
    ├── stats_screen.py            # Per-profile stats
    ├── general_stats_screen.py    # Cross-profile combined stats
    ├── rewards_screen.py          # XP, levels, badges, daily challenge
    └── alert_dialog.py            # Inactivity alert popup
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Dark-themed tkinter UI components |
| `pynput` | Global keyboard/mouse activity detection |
| `sounddevice` | Real-time audio output |
| `numpy` | Waveform generation for procedural sounds |
| `Pillow` | App icon loading |

Install all at once:
```bash
pip install customtkinter pynput sounddevice numpy Pillow
```

---

## Customization

All core constants live in `config.py`:

```python
INACTIVITY_TIMEOUT = 60        # Default inactivity alert timeout (seconds)
DEFAULT_WORK_DURATION = 1500   # 25 minutes
DEFAULT_BREAK_DURATION = 300   # 5 minutes
COLORS = { ... }               # Full dark theme palette
```

Per-profile overrides (inactivity timeout, work/break defaults) are editable from the profile edit screen inside the app.

Master volume is set in `services/sound_service.py`:
```python
MASTER_VOLUME = 0.3  # 0.0 – 1.0
```

---

## Changelog

| Version | Highlights |
|---|---|
| v1.1.2 | Challenge XP fix, mini window holds 5s on completion, volume reduced to 0.3 |
| v1.1.1 | Goals & Rewards, General Stats, Free Mode, Mode Select, Mini Window overhaul, profile editing, tab switching without killing timer |
| v1.0.0 | Initial release — scheduled timer, profiles, inactivity detection, lo-fi sounds |

---

## License

MIT