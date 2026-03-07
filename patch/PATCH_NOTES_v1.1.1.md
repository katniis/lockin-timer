# LockIn Timer — v1.1.1 Patch Notes

> Released: 2026 · Follows v1.0.0

---

## What's New

### 🏆 Goals & Rewards
A new top-level screen accessible from the profile page. Study time now earns XP and levels you up — 100 XP per hour, six levels from 🌱 Beginner to 👑 Legend. Includes:
- **XP & Level system** with a visual progress bar and full level ladder
- **15 unlockable badges** — First Step, Night Owl, Early Bird, Marathon, Week Warrior, Legend, and more
- **Daily Challenge** — a new challenge every day with a progress bar and bonus XP reward
- **Streak tracker** — per-profile flame levels (❄️ → 🔥 → 🔥🔥 → 🔥🔥🔥) with a 7-day dot history

### 📊 General Stats
New top-level screen showing combined data across every profile:
- All-time totals: total study time, scheduled vs free mode breakdown, sessions, best streak, this week
- Combined daily bar chart (7-day / 30-day toggle)
- Per-profile breakdown with today's progress bars

### 🆕 Mode Selection Screen
After picking a profile you now choose your mode — **Scheduled** or **Free Mode** — before entering a session. Each mode has its own card with a description. Cleaner flow, no confusion.

### 🆓 Free Mode
New stopwatch-based session mode:
- Count-up timer, manual break toggle with its own break timer
- Milestone pings every 25 minutes
- 20-minute break nudge dialog
- Sessions saved to profile history and counted in all stats

### ✏️ Profile Editing
Profiles can now be edited without deleting — rename, recolor, change default work/break durations, and set a per-profile inactivity alert timeout.

### 🗑️ Delete Confirmation
Deleting a profile now shows a confirmation dialog before permanently removing it and all its history.

---

## Improvements

### Timer Behavior
- **Inactivity alert now auto-pauses the timer** while the alert dialog is open, then auto-resumes when dismissed (respects manual pause — won't override if you paused yourself)
- Per-profile configurable inactivity timeout (was hardcoded at 60s for all profiles)

### Tab Switching
- Switching tabs (Timer / Free Mode / My Stats) no longer destroys the active session — the timer keeps running in the background
- Switching between Timer and Free Mode tabs correctly prevents both from running simultaneously
- My Stats shows as an overlay above the session, Back returns to the active session

### Mini Window
- **Break button hidden in scheduled mode** — only appears in Free Mode where it's relevant
- **Break timer displayed in green** when on break in Free Mode (previously showed the study timer)
- **Completion pulse** — when a session ends the mini window border and clock pulse green three times then close automatically
- **Inactivity pulse** — border and clock pulse orange when an inactivity alert fires
- **Flicker fix** — update loop now diffs state before reconfiguring widgets, eliminating button flickering
- Background gap behind rounded corners eliminated

### Profile Screen
- New profiles show **"Ready to start"** instead of "0h studied · 0 sessions"
- Total hours shown combines scheduled + free mode time

### Completion Screen
- Shows work time, break time, and blocks completed
- Compares today's study time to yesterday (▲ more / ▼ less)

### Schedule Builder
- Tightened row padding — blocks no longer float in oversized rows
- Rows anchor to top of list correctly

### Navigation
- **Pin button removed** — the always-on-top mini window handles that use case more elegantly
- Bottom nav reduced to three focused tabs: Timer, Free Mode, My Stats
- Goals & Rewards and General Stats accessible from the profile screen as top-level destinations

---

## Bug Fixes

- Fixed blank window when switching to a tab whose session frame hadn't been created yet
- Fixed blank window when pressing Back from My Stats
- Fixed timer continuing to tick while inactivity alert was visible
- Fixed mini window break button appearing in scheduled mode
- Fixed mini window showing study timer instead of break timer during a free mode break
- Fixed profile deletion happening immediately without confirmation
- Fixed icon not displaying — switched to `.ico` + `iconbitmap()` for reliable Windows support


---

## Upgrade Notes

Profiles from v1.0.0 are fully compatible. New fields (`inactivity_timeout`, `free_sessions`, `daily_goal`, `weekly_goal`) are added automatically with sensible defaults when a v1.0.0 profile is loaded.
