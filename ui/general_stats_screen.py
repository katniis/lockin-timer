import tkinter as tk
import customtkinter as ctk
from datetime import date, timedelta
from config import COLORS, FONTS


def fmt_hours(seconds: int) -> str:
    h = seconds / 3600
    return f"{h:.1f}h" if h >= 1 else f"{seconds // 60}m"


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


class GeneralStatsScreen(ctk.CTkFrame):
    def __init__(self, parent, profiles: list, storage, on_back):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profiles = profiles
        self._storage = storage
        self._on_back = on_back
        self._chart_range = "7"
        self._build()

    def _build(self):
        nav = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(nav, text="← Back", command=self._on_back,
                      fg_color="transparent", hover_color=COLORS["surface2"],
                      text_color=COLORS["text_dim"], corner_radius=8,
                      height=36, width=80, font=FONTS["small"]).pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(nav, text="General Stats", font=FONTS["title"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="left", padx=8)

        ctk.CTkLabel(nav, text=f"{len(self._profiles)} profile{'s' if len(self._profiles) != 1 else ''}",
                     font=FONTS["small"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack(side="right", padx=20)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                               scrollbar_button_color=COLORS["border"])
        self._scroll.pack(fill="both", expand=True, padx=24, pady=20)
        self._render()

    def _render(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._render_combined_overview()
        self._render_goals_summary()
        self._render_chart()
        self._render_per_profile()

    # ── Combined totals ───────────────────────────────────────────────────────

    def _render_combined_overview(self):
        section = self._section("All Time — Combined")

        total_work  = sum(p.total_work_seconds() for p in self._profiles)
        total_free  = sum(p.total_free_seconds() for p in self._profiles)
        total_all   = total_work + total_free
        total_sessions = sum(p.total_sessions() for p in self._profiles)
        best_streak = max((p.streak_days() for p in self._profiles), default=0)
        today = date.today()
        today_secs  = sum(p.work_seconds_on(today) + p.free_seconds_on(today) for p in self._profiles)
        wstart = week_start(today)
        week_secs   = sum(p.work_seconds_in_week(wstart) + p.free_seconds_in_week(wstart) for p in self._profiles)

        cards = [
            ("⏱ Total Study",  fmt_hours(total_all),     "Scheduled + Free"),
            ("📚 Scheduled",    fmt_hours(total_work),    "Scheduled sessions"),
            ("🆓 Free Mode",    fmt_hours(total_free),    "Free mode time"),
            ("⚡ Sessions",     str(total_sessions),      "Completed blocks"),
            ("🔥 Best Streak",  f"{best_streak}d",        "Any single profile"),
            ("📅 This Week",    fmt_hours(week_secs),     "All profiles"),
        ]

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        for i, (title, val, sub) in enumerate(cards):
            r, c = divmod(i, 3)
            card = ctk.CTkFrame(grid, fg_color=COLORS["surface"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
            card.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=14, pady=12)
            ctk.CTkLabel(inner, text=val, font=FONTS["title"],
                         text_color=COLORS["text"], fg_color="transparent").pack()
            ctk.CTkLabel(inner, text=title, font=FONTS["small"],
                         text_color=COLORS["accent2"], fg_color="transparent").pack()
            ctk.CTkLabel(inner, text=sub, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack()

    # ── Goals summary (read-only combined view) ───────────────────────────────

    def _render_goals_summary(self):
        section = self._section("Today's Goals — All Profiles")

        today = date.today()
        for p in self._profiles:
            done = p.work_seconds_on(today) + p.free_seconds_on(today)
            goal = p.daily_goal
            progress = min(done / goal, 1.0) if goal > 0 else 0.0

            row = ctk.CTkFrame(section, fg_color=COLORS["surface"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
            row.pack(fill="x", pady=3)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)

            # Avatar
            av = ctk.CTkFrame(inner, fg_color=p.avatar_color, width=28, height=28, corner_radius=14)
            av.pack(side="left", padx=(0, 10))
            av.pack_propagate(False)
            ctk.CTkLabel(av, text=p.name[0].upper(), font=("Georgia", 11, "bold"),
                         text_color="white", fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info, text=p.name, font=FONTS["body_bold"],
                         text_color=COLORS["text"], fg_color="transparent").pack(anchor="w")
            bar = ctk.CTkProgressBar(info, height=5, fg_color=COLORS["surface2"],
                                      progress_color=p.avatar_color, corner_radius=3)
            bar.pack(fill="x", pady=(4, 0))
            bar.set(progress)

            pct = int(progress * 100)
            status = "✓" if progress >= 1.0 else f"{pct}%"
            status_color = COLORS["success"] if progress >= 1.0 else COLORS["text_dim"]
            ctk.CTkLabel(inner, text=f"{fmt_hours(done)} / {fmt_hours(goal)}\n{status}",
                         font=FONTS["small"], text_color=status_color,
                         fg_color="transparent", justify="right").pack(side="right")

    # ── Combined bar chart ────────────────────────────────────────────────────

    def _render_chart(self):
        section = self._section("Daily Hours — All Profiles Combined")

        toggle_row = ctk.CTkFrame(section, fg_color="transparent")
        toggle_row.pack(anchor="e", pady=(0, 12))
        for label, val in [("7 days", "7"), ("30 days", "30")]:
            is_active = self._chart_range == val
            ctk.CTkButton(toggle_row, text=label, width=72, height=28,
                          fg_color=COLORS["accent"] if is_active else COLORS["surface2"],
                          hover_color=COLORS["accent2"],
                          text_color=COLORS["text"] if is_active else COLORS["text_dim"],
                          corner_radius=8, font=FONTS["small"],
                          command=lambda v=val: self._set_range(v)).pack(side="left", padx=3)

        days = int(self._chart_range)
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
        values = [sum(p.work_seconds_on(d) + p.free_seconds_on(d)
                      for p in self._profiles) / 3600 for d in dates]
        self._draw_chart(section, dates, values)

    def _draw_chart(self, parent, dates, values):
        container = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12)
        container.pack(fill="x")
        canvas = tk.Canvas(container, height=180, bg=COLORS["surface"],
                           highlightthickness=0, bd=0)
        canvas.pack(fill="x", padx=16, pady=16)

        def draw(event=None):
            canvas.delete("all")
            w = canvas.winfo_width() or 600
            h = 180
            if not values:
                return
            max_val = max(values) if max(values) > 0 else 1.0
            bar_area_h = h - 40
            spacing = (w - 40) / len(values)
            bar_w = max(4, spacing - 4)
            today = date.today()

            for i in range(4):
                y = 10 + bar_area_h * (1 - i / 3)
                canvas.create_line(20, y, w - 20, y, fill=COLORS["border"], width=1, dash=(4, 4))
                canvas.create_text(14, y, text=f"{max_val * i / 3:.1f}",
                                   fill=COLORS["text_dim"], font=("Helvetica Neue", 8), anchor="e")

            for i, (d, v) in enumerate(zip(dates, values)):
                xc = 20 + spacing * i + spacing / 2
                bh = (v / max_val) * bar_area_h
                color = COLORS["accent"] if d == today else COLORS["accent_dim"]
                if bh > 2:
                    canvas.create_rectangle(xc - bar_w / 2, h - 28 - bh,
                                            xc + bar_w / 2, h - 28, fill=color, outline="")
                if len(dates) <= 14 or i % 5 == 0:
                    canvas.create_text(xc, h - 14,
                                       text=d.strftime("%d" if len(dates) > 7 else "%a"),
                                       fill=COLORS["text_dim"], font=("Helvetica Neue", 8))

        canvas.bind("<Configure>", draw)
        canvas.after(50, draw)

    # ── Per-profile breakdown ─────────────────────────────────────────────────

    def _render_per_profile(self):
        if len(self._profiles) < 2:
            return
        section = self._section("Per Profile Breakdown")

        for p in self._profiles:
            card = ctk.CTkFrame(section, fg_color=COLORS["surface"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            av = ctk.CTkFrame(inner, fg_color=p.avatar_color, width=36, height=36, corner_radius=18)
            av.pack(side="left", padx=(0, 12))
            av.pack_propagate(False)
            ctk.CTkLabel(av, text=p.name[0].upper(), font=("Georgia", 14, "bold"),
                         text_color="white", fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info, text=p.name, font=FONTS["body_bold"],
                         text_color=COLORS["text"], fg_color="transparent").pack(anchor="w")

            total = p.total_work_seconds() + p.total_free_seconds()
            streak = p.streak_days()
            ctk.CTkLabel(info,
                         text=f"{fmt_hours(total)} total · {p.total_sessions()} sessions · {streak}d streak",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(anchor="w")

            today = date.today()
            today_secs = p.work_seconds_on(today) + p.free_seconds_on(today)
            goal = p.daily_goal
            progress = min(today_secs / goal, 1.0) if goal > 0 else 0.0
            bar = ctk.CTkProgressBar(inner, width=110, height=6,
                                      fg_color=COLORS["surface2"],
                                      progress_color=p.avatar_color, corner_radius=3)
            bar.pack(side="right")
            bar.set(progress)
            ctk.CTkLabel(inner, text="today", font=FONTS["small"],
                         text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(side="right", padx=(0, 8))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section(self, title):
        ctk.CTkLabel(self._scroll, text=title, font=FONTS["heading"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(20, 6))
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 8))
        return frame

    def _set_range(self, val):
        self._chart_range = val
        self._render()
