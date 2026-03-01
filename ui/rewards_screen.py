import tkinter as tk
import customtkinter as ctk
import hashlib
from datetime import date, timedelta, datetime
from config import COLORS, FONTS


# ── XP & Level system ────────────────────────────────────────────────────────

LEVELS = [
    (0,     "Beginner",     "🌱"),
    (500,   "Focused",      "🎯"),
    (1500,  "Deep Worker",  "🔥"),
    (3500,  "Flow State",   "⚡"),
    (7000,  "Grinder",      "💎"),
    (12000, "Legend",       "👑"),
]

def calc_xp(profiles: list) -> int:
    """1 XP per 36 seconds of study (= 100 XP/hour)."""
    total = sum(p.total_work_seconds() + p.total_free_seconds() for p in profiles)
    return total // 36

def get_level(xp: int) -> tuple:
    """Returns (level_name, icon, xp_start, xp_next)."""
    current = LEVELS[0]
    for threshold, name, icon in LEVELS:
        if xp >= threshold:
            current = (threshold, name, icon)
        else:
            prev_thresh, prev_name, prev_icon = current
            return prev_name, prev_icon, prev_thresh, threshold
    # Max level
    thresh, name, icon = LEVELS[-1]
    return name, icon, thresh, thresh + 5000


# ── Badge definitions ─────────────────────────────────────────────────────────

def get_all_badges(profiles: list) -> list:
    """Returns list of (icon, title, description, unlocked: bool)."""
    total_secs = sum(p.total_work_seconds() + p.total_free_seconds() for p in profiles)
    total_sessions = sum(p.total_sessions() for p in profiles)
    total_free = sum(len(p.free_sessions) for p in profiles)
    best_streak = max((p.streak_days() for p in profiles), default=0)
    xp = calc_xp(profiles)

    # Night owl: any session started after 22:00
    night_owl = False
    for p in profiles:
        for s in p.sessions + p.free_sessions:
            try:
                dt = datetime.fromisoformat(s.get("date", ""))
                if dt.hour >= 22:
                    night_owl = True
                    break
            except Exception:
                pass

    # Early bird: any session started before 07:00
    early_bird = False
    for p in profiles:
        for s in p.sessions + p.free_sessions:
            try:
                dt = datetime.fromisoformat(s.get("date", ""))
                if dt.hour < 7:
                    early_bird = True
                    break
            except Exception:
                pass

    # Marathon: any single free session > 2 hours
    marathon = any(
        s.get("duration", 0) >= 7200
        for p in profiles for s in p.free_sessions
    )

    badges = [
        ("🎉", "First Step",      "Complete your first session",              total_sessions >= 1),
        ("⚡", "Getting Started", "Reach 500 XP",                             xp >= 500),
        ("🔥", "On Fire",         "Achieve a 3-day streak",                   best_streak >= 3),
        ("📚", "Bookworm",        "Study for 10 hours total",                 total_secs >= 36000),
        ("💎", "Diamond Mind",    "Study for 50 hours total",                 total_secs >= 180000),
        ("👑", "Legend",          "Reach Legend level (12,000 XP)",           xp >= 12000),
        ("🌙", "Night Owl",       "Start a session after 10 PM",              night_owl),
        ("🌅", "Early Bird",      "Start a session before 7 AM",              early_bird),
        ("🏃", "Marathon",        "Study 2+ hours in a single free session",  marathon),
        ("🎯", "Focused",         "Complete 10 scheduled sessions",           total_sessions >= 10),
        ("🆓", "Free Spirit",     "Complete 5 free mode sessions",            total_free >= 5),
        ("🔗", "Week Warrior",    "Achieve a 7-day streak",                   best_streak >= 7),
        ("🧠", "Flow State",      "Reach Flow State level (3,500 XP)",        xp >= 3500),
        ("🏆", "Champion",        "Achieve a 30-day streak",                  best_streak >= 30),
        ("✨", "Century",         "Complete 100 sessions",                    total_sessions >= 100),
    ]
    return badges


# ── Daily challenge ───────────────────────────────────────────────────────────

CHALLENGES = [
    ("Study for 30 minutes",       30 * 60,  "scheduled", 50),
    ("Study for 1 hour",           3600,     "both",      100),
    ("Study for 90 minutes",       90 * 60,  "both",      150),
    ("Complete 2 work blocks",     2,        "blocks",    80),
    ("Complete 4 work blocks",     4,        "blocks",    160),
    ("Do a free mode session",     1,        "free",      75),
    ("Study for 2 hours",          7200,     "both",      200),
    ("Study for 45 minutes",       45 * 60,  "both",      75),
]

def get_daily_challenge(profiles: list) -> tuple:
    """Deterministic daily challenge based on date seed. Returns (text, xp_reward, progress, target, done)."""
    seed = int(date.today().strftime("%Y%m%d"))
    idx = seed % len(CHALLENGES)
    text, target, kind, xp_reward = CHALLENGES[idx]

    today = date.today()
    if kind == "blocks":
        progress = sum(
            sum(1 for s in p.sessions
                if s.get("completed") and s.get("block_type") == "work"
                and _is_today(s.get("date", "")))
            for p in profiles
        )
    elif kind == "free":
        progress = sum(
            sum(1 for s in p.free_sessions if _is_today(s.get("date", "")))
            for p in profiles
        )
    else:
        progress = sum(
            p.work_seconds_on(today) + p.free_seconds_on(today)
            for p in profiles
        )

    done = progress >= target
    return text, xp_reward, progress, target, done

def _is_today(date_str: str) -> bool:
    try:
        return datetime.fromisoformat(date_str).date() == date.today()
    except Exception:
        return False


# ── Rewards Screen ────────────────────────────────────────────────────────────

class RewardsScreen(ctk.CTkFrame):
    def __init__(self, parent, profiles: list, storage, on_back):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profiles = profiles
        self._storage = storage
        self._on_back = on_back
        self._build()

    def _build(self):
        nav = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(nav, text="← Back", command=self._on_back,
                      fg_color="transparent", hover_color=COLORS["surface2"],
                      text_color=COLORS["text_dim"], corner_radius=8,
                      height=36, width=80, font=FONTS["small"]).pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(nav, text="Goals & Rewards", font=FONTS["title"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="left", padx=8)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                               scrollbar_button_color=COLORS["border"])
        self._scroll.pack(fill="both", expand=True, padx=24, pady=20)

        self._render_level()
        self._render_daily_challenge()
        self._render_streak()
        self._render_badges()

    # ── Level & XP ────────────────────────────────────────────────────────────

    def _render_level(self):
        xp = calc_xp(self._profiles)
        level_name, level_icon, xp_start, xp_next = get_level(xp)
        progress = (xp - xp_start) / (xp_next - xp_start) if xp_next > xp_start else 1.0
        progress = min(progress, 1.0)

        section = self._section("Your Level")

        card = ctk.CTkFrame(section, fg_color=COLORS["surface"], corner_radius=16,
                             border_width=1, border_color=COLORS["border"])
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        # Left: icon + level name
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        icon_frame = ctk.CTkFrame(left, fg_color=COLORS["accent_dim"],
                                   width=72, height=72, corner_radius=36)
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=level_icon, font=("Georgia", 32),
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(left, text=level_name, font=FONTS["heading"],
                     text_color=COLORS["accent2"], fg_color="transparent").pack(pady=(8, 0))

        # Right: XP bar + info
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(24, 0))

        xp_row = ctk.CTkFrame(right, fg_color="transparent")
        xp_row.pack(fill="x")
        ctk.CTkLabel(xp_row, text=f"{xp:,} XP", font=FONTS["title"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="left")
        ctk.CTkLabel(xp_row, text=f"Next: {xp_next:,} XP", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(side="right")

        bar = ctk.CTkProgressBar(right, height=12, fg_color=COLORS["surface2"],
                                  progress_color=COLORS["accent"], corner_radius=6)
        bar.pack(fill="x", pady=(10, 6))
        bar.set(progress)

        ctk.CTkLabel(right,
                     text=f"{int(progress * 100)}% to next level  •  1 XP = 36 seconds of study",
                     font=FONTS["small"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack(anchor="w")

        # Level ladder
        ladder = ctk.CTkFrame(right, fg_color="transparent")
        ladder.pack(fill="x", pady=(14, 0))
        for i, (thresh, name, icon) in enumerate(LEVELS):
            unlocked = xp >= thresh
            col = ctk.CTkFrame(ladder, fg_color="transparent")
            col.pack(side="left", expand=True)
            ctk.CTkLabel(col, text=icon,
                         font=("Georgia", 16 if unlocked else 14),
                         fg_color="transparent",
                         text_color=COLORS["text"] if unlocked else COLORS["text_dim"]).pack()
            ctk.CTkLabel(col, text=name, font=FONTS["small"],
                         fg_color="transparent",
                         text_color=COLORS["accent2"] if unlocked else COLORS["text_dim"]).pack()

    # ── Daily challenge ───────────────────────────────────────────────────────

    def _render_daily_challenge(self):
        text, xp_reward, progress, target, done = get_daily_challenge(self._profiles)
        section = self._section("Daily Challenge")

        card = ctk.CTkFrame(section, fg_color=COLORS["surface"], corner_radius=16,
                             border_width=1,
                             border_color=COLORS["success"] if done else COLORS["border"])
        card.pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        # Header row
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(header, text="✓ " + text if done else text,
                     font=FONTS["heading"],
                     text_color=COLORS["success"] if done else COLORS["text"],
                     fg_color="transparent").pack(side="left")

        xp_badge = ctk.CTkFrame(header, fg_color=COLORS["accent_dim"], corner_radius=8)
        xp_badge.pack(side="right")
        ctk.CTkLabel(xp_badge, text=f"+{xp_reward} XP",
                     font=("Helvetica Neue", 11, "bold"),
                     text_color=COLORS["accent2"], fg_color="transparent").pack(padx=12, pady=4)

        ctk.CTkLabel(inner, text="Resets at midnight  •  Bonus XP on completion",
                     font=FONTS["small"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack(anchor="w", pady=(4, 10))

        # Progress bar
        if isinstance(target, int) and target > 60:
            # Time-based
            ratio = min(progress / target, 1.0)
            bar = ctk.CTkProgressBar(inner, height=10, fg_color=COLORS["surface2"],
                                      progress_color=COLORS["success"] if done else COLORS["accent"],
                                      corner_radius=5)
            bar.pack(fill="x")
            bar.set(ratio)

            mins_done = progress // 60
            mins_target = target // 60
            ctk.CTkLabel(inner, text=f"{mins_done}m / {mins_target}m",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(anchor="w", pady=(6, 0))
        else:
            # Count-based
            ratio = min(progress / target, 1.0) if target > 0 else 1.0
            bar = ctk.CTkProgressBar(inner, height=10, fg_color=COLORS["surface2"],
                                      progress_color=COLORS["success"] if done else COLORS["accent"],
                                      corner_radius=5)
            bar.pack(fill="x")
            bar.set(ratio)
            ctk.CTkLabel(inner, text=f"{progress} / {target}",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(anchor="w", pady=(6, 0))

    # ── Streak display ────────────────────────────────────────────────────────

    def _render_streak(self):
        section = self._section("Streaks")

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for col_i, p in enumerate(self._profiles[:2]):
            streak = p.streak_days()
            # Determine flame level
            if streak >= 30:
                flame = "🔥🔥🔥"
                flame_color = COLORS["warning"]
            elif streak >= 14:
                flame = "🔥🔥"
                flame_color = COLORS["warning"]
            elif streak >= 7:
                flame = "🔥"
                flame_color = COLORS["warning"]
            elif streak >= 3:
                flame = "🔥"
                flame_color = COLORS["accent2"]
            else:
                flame = "❄️"
                flame_color = COLORS["text_dim"]

            card = ctk.CTkFrame(grid, fg_color=COLORS["surface"], corner_radius=14,
                                 border_width=1, border_color=COLORS["border"])
            card.grid(row=0, column=col_i, padx=(0, 6) if col_i == 0 else (6, 0), sticky="ew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=16, pady=14)

            # Avatar row
            av_row = ctk.CTkFrame(inner, fg_color="transparent")
            av_row.pack()
            av = ctk.CTkFrame(av_row, fg_color=p.avatar_color, width=32, height=32, corner_radius=16)
            av.pack(side="left", padx=(0, 8))
            av.pack_propagate(False)
            ctk.CTkLabel(av, text=p.name[0].upper(), font=("Georgia", 13, "bold"),
                         text_color="white", fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(av_row, text=p.name, font=FONTS["body_bold"],
                         text_color=COLORS["text"], fg_color="transparent").pack(side="left")

            ctk.CTkLabel(inner, text=flame, font=("Georgia", 36),
                         fg_color="transparent").pack(pady=(8, 0))
            ctk.CTkLabel(inner, text=f"{streak} day{'s' if streak != 1 else ''}",
                         font=FONTS["title"], text_color=flame_color,
                         fg_color="transparent").pack()
            ctk.CTkLabel(inner, text="Keep it going!" if streak > 0 else "Start today!",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack()

            # Last 7 days dots
            dots = ctk.CTkFrame(inner, fg_color="transparent")
            dots.pack(pady=(10, 0))
            today = date.today()
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                studied = p.work_seconds_on(day) > 0 or p.free_seconds_on(day) > 0
                dot = ctk.CTkFrame(dots,
                                    fg_color=COLORS["accent"] if studied else COLORS["surface2"],
                                    width=12, height=12, corner_radius=6)
                dot.pack(side="left", padx=2)

        # If more than 2 profiles, show the rest as simple rows
        for p in self._profiles[2:]:
            streak = p.streak_days()
            row = ctk.CTkFrame(section, fg_color=COLORS["surface"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
            row.pack(fill="x", pady=(6, 0))
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)
            av = ctk.CTkFrame(inner, fg_color=p.avatar_color, width=28, height=28, corner_radius=14)
            av.pack(side="left", padx=(0, 10))
            av.pack_propagate(False)
            ctk.CTkLabel(av, text=p.name[0].upper(), font=("Georgia", 11, "bold"),
                         text_color="white", fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(inner, text=p.name, font=FONTS["body_bold"],
                         text_color=COLORS["text"], fg_color="transparent").pack(side="left")
            ctk.CTkLabel(inner, text=f"🔥 {streak}d streak",
                         font=FONTS["body"], text_color=COLORS["warning"],
                         fg_color="transparent").pack(side="right")

    # ── Badge shelf ───────────────────────────────────────────────────────────

    def _render_badges(self):
        section = self._section("Badges")

        badges = get_all_badges(self._profiles)
        unlocked = [b for b in badges if b[3]]
        locked = [b for b in badges if not b[3]]

        if unlocked:
            ctk.CTkLabel(section, text=f"Unlocked — {len(unlocked)}/{len(badges)}",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(anchor="w", pady=(0, 8))

            shelf = ctk.CTkFrame(section, fg_color="transparent")
            shelf.pack(fill="x")

            cols = 5
            for i in range(cols):
                shelf.columnconfigure(i, weight=1)

            for i, (icon, title, desc, _) in enumerate(unlocked):
                r, c = divmod(i, cols)
                self._badge_card(shelf, icon, title, desc, unlocked=True, row=r, col=c)

        if locked:
            ctk.CTkLabel(section, text="Locked",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(anchor="w", pady=(16, 8))

            shelf2 = ctk.CTkFrame(section, fg_color="transparent")
            shelf2.pack(fill="x")
            cols = 5
            for i in range(cols):
                shelf2.columnconfigure(i, weight=1)

            for i, (icon, title, desc, _) in enumerate(locked):
                r, c = divmod(i, cols)
                self._badge_card(shelf2, icon, title, desc, unlocked=False, row=r, col=c)

    def _badge_card(self, parent, icon, title, desc, unlocked, row, col):
        card = ctk.CTkFrame(parent,
                             fg_color=COLORS["surface"] if unlocked else COLORS["bg"],
                             corner_radius=12,
                             border_width=1,
                             border_color=COLORS["accent"] if unlocked else COLORS["border"])
        card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=10, pady=10)

        ctk.CTkLabel(inner, text=icon if unlocked else "🔒",
                     font=("Georgia", 26 if unlocked else 20),
                     fg_color="transparent",
                     text_color=COLORS["text"] if unlocked else COLORS["text_dim"]).pack()

        ctk.CTkLabel(inner, text=title, font=FONTS["small"],
                     text_color=COLORS["accent2"] if unlocked else COLORS["text_dim"],
                     fg_color="transparent", wraplength=90, justify="center").pack(pady=(4, 0))

        ctk.CTkLabel(inner, text=desc, font=("Helvetica Neue", 9),
                     text_color=COLORS["text_dim"],
                     fg_color="transparent", wraplength=90, justify="center").pack(pady=(2, 0))

    # ── Helper ────────────────────────────────────────────────────────────────

    def _section(self, title):
        ctk.CTkLabel(self._scroll, text=title, font=FONTS["heading"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(20, 8))
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 8))
        return frame
