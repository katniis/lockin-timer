APP_NAME = "LockIn"
VERSION = "1.0.0"
DATA_DIR = "data/profiles"

# Timer defaults (in seconds)
DEFAULT_WORK_DURATION = 25 * 60
DEFAULT_BREAK_DURATION = 5 * 60
INACTIVITY_TIMEOUT = 300
TICK_INTERVAL = 1000  # ms

# UI
WINDOW_WIDTH = 920
WINDOW_HEIGHT = 620
CORNER_RADIUS = 16

# Theme colors
COLORS = {
    "bg": "#0f0f13",
    "surface": "#17171f",
    "surface2": "#1e1e2a",
    "border": "#2a2a3a",
    "accent": "#7c6af7",
    "accent2": "#a78bfa",
    "accent_dim": "#3d3575",
    "work": "#7c6af7",
    "break": "#34d399",
    "break_dim": "#0f4a38",
    "text": "#e8e8f0",
    "text_dim": "#7070a0",
    "danger": "#f87171",
    "danger_dim": "#3d1f1f",
    "warning": "#fbbf24",
    "warning_dim": "#3d3010",
    "success": "#34d399",
    "accent_highlight": "#2a2550",
}

FONTS = {
    "display": ("Georgia", 48, "bold"),
    "title": ("Georgia", 22, "bold"),
    "heading": ("Georgia", 16, "bold"),
    "body": ("Helvetica Neue", 13),
    "body_bold": ("Helvetica Neue", 13, "bold"),
    "small": ("Helvetica Neue", 11),
    "mono": ("Courier New", 32, "bold"),
}
