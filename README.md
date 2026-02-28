# LockIn Timer

A focused study timer with custom schedules, multiple profiles, and inactivity detection.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Features

- **Multiple profiles** — each saved to its own JSON file with color, defaults, and session history
- **Custom schedule builder** — add any combination of work and break blocks before starting
- **Live countdown** — large clock display with progress bar, block type indicator, and queue view
- **Pause / Skip / Stop** — full control during a session
- **Inactivity detection** — alerts you after 60 seconds of no mouse/keyboard input (requires `pynput`)
- **Session history** — every completed block is saved to your profile automatically

## Project Structure

```
lockin-timer/
├── main.py                  # Entry point
├── config.py                # Constants, colors, fonts
├── requirements.txt
├── data/profiles/           # JSON profile files (auto-created)
├── models/
│   ├── profile.py
│   ├── schedule.py
│   └── session.py
├── services/
│   ├── storage_service.py
│   ├── timer_service.py
│   ├── schedule_service.py
│   └── activity_service.py
└── ui/
    ├── main_window.py
    ├── profile_screen.py
    ├── schedule_builder.py
    ├── timer_screen.py
    └── alert_dialog.py
```

## Customization

Edit `config.py` to change:
- `INACTIVITY_TIMEOUT` — seconds before the inactivity alert fires (default: 60)
- `DEFAULT_WORK_DURATION` / `DEFAULT_BREAK_DURATION` — per-profile defaults
- `COLORS` — full dark theme color palette
