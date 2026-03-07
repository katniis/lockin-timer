# LockIn Timer — v1.1.2 Patch Notes

> Released: 2026 · Follows v1.1.1

---

## Bug Fixes

### 🏆 Goals & Rewards — XP not awarding on challenge completion
Daily challenge bonus XP was not being added to the total XP. Completed challenges now correctly persist their bonus XP to `data/_app_data.json` and are counted in the XP total and level calculation. The challenge card also now shows a green **"✓ +XP claimed"** badge once the reward has been awarded — idempotent, so it will never double-award the same day's challenge.

### 🪟 Mini Window — Completion state dismissed too quickly
The green "DONE" state on the mini window was closing after ~1.5 seconds. It now pulses green three times then holds the solid green border and clock for **5 seconds** before auto-closing.

---

## Adjustments

### 🔊 Master Volume reduced to 0.3
Procedural lo-fi sounds (session start, break, completion, inactivity alert) have been dialed back from 0.82 to **0.3** — less intrusive when working with background music or in quiet environments.

---

## How to Build

```bash
pip install customtkinter pynput numpy sounddevice Pillow pyinstaller
cd lockin-timer
build.bat
# Output: dist/LockIn-v1.1.2.exe
```

---

## Upgrade Notes

Fully compatible with v1.1.1 profiles and app data. A new `data/_app_data.json` file is created automatically on first launch to track challenge XP — no manual migration needed.
