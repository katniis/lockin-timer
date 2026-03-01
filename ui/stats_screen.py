import tkinter as tk
import customtkinter as ctk
from datetime import date, timedelta
from config import COLORS, FONTS
from models.profile import Profile


def fmt_hours(seconds: int) -> str:
    h = seconds / 3600
    return f"{h:.1f}h" if h >= 1 else f"{seconds // 60}m"


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


class StatsScreen(ctk.CTkFrame):
    def __init__(self, parent, profile: Profile, storage, on_back):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profile = profile
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

        ctk.CTkLabel(nav, text=f"{self._profile.name}'s Stats", font=FONTS["title"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="left", padx=8)

        avatar_frame = ctk.CTkFrame(nav, fg_color=self._profile.avatar_color,
                                     width=32, height=32, corner_radius=16)
        avatar_frame.pack(side="right", padx=(0, 12), pady=12)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text=self._profile.name[0].upper(),
                     font=("Georgia", 13, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                               scrollbar_button_color=COLORS["border"])
        self._scroll.pack(fill="both", expand=True, padx=24, pady=20)
        self._render()

    def _render(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._render_overview()
        self._render_chart()
        if self._profile.free_sessions:
            self._render_free_stats()

    def _render_overview(self):
        section = self._section("Overview")
        p = self._profile
        streak = p.streak_days()
        total_sessions = p.total_sessions()
        avg_sec = (p.total_work_seconds() / total_sessions) if total_sessions else 0

        cards = [
            ("🔥 Streak",      f"{streak}d",                    "Current streak"),
            ("📚 Study Time",  fmt_hours(p.total_work_seconds()), "Scheduled sessions"),
            ("🆓 Free Mode",   fmt_hours(p.total_free_seconds()), "Free mode time"),
            ("⚡ Sessions",    str(total_sessions),              "Completed blocks"),
            ("⏱ Avg Session", fmt_hours(int(avg_sec)),           "Per work block"),
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

    def _render_chart(self):
        section = self._section("Study Hours")

        toggle_row = ctk.CTkFrame(section, fg_color="transparent")
        toggle_row.pack(anchor="e", pady=(0, 12))
        for label, val in [("7 days", "7"), ("30 days", "30")]:
            is_active = self._chart_range == val
            ctk.CTkButton(toggle_row, text=label, width=72, height=28,
                          fg_color=COLORS["accent"] if is_active else COLORS["surface2"],
                          hover_color=COLORS["accent2"],
                          text_color=COLORS["text"] if is_active else COLORS["text_dim"],
                          corner_radius=8, font=FONTS["small"],
                          command=lambda v=val: self._set_chart(v),
                          ).pack(side="left", padx=3)

        days = int(self._chart_range)
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
        values = [(self._profile.work_seconds_on(d) + self._profile.free_seconds_on(d)) / 3600
                  for d in dates]
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
            n = len(values)
            if not n:
                return
            max_val = max(values) if max(values) > 0 else 1.0
            bar_area_h = h - 40
            spacing = (w - 40) / n
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
                                            xc + bar_w / 2, h - 28,
                                            fill=color, outline="")
                if len(dates) <= 14 or i % 5 == 0:
                    label = d.strftime("%d" if len(dates) > 7 else "%a")
                    canvas.create_text(xc, h - 14, text=label,
                                       fill=COLORS["text_dim"], font=("Helvetica Neue", 8))

        canvas.bind("<Configure>", draw)
        canvas.after(50, draw)

    def _render_free_stats(self):
        section = self._section("Free Mode")
        p = self._profile
        total_h = p.total_free_seconds() / 3600
        count = len(p.free_sessions)
        avg = p.total_free_seconds() / count if count else 0

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        for i, (title, val) in enumerate([
            ("Total Time", f"{total_h:.1f}h"),
            ("Sessions", str(count)),
            ("Avg Session", fmt_hours(int(avg))),
        ]):
            card = ctk.CTkFrame(grid, fg_color=COLORS["surface"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
            card.grid(row=0, column=i, padx=4, pady=4, sticky="ew")
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=14, pady=12)
            ctk.CTkLabel(inner, text=val, font=FONTS["title"],
                         text_color=COLORS["break"], fg_color="transparent").pack()
            ctk.CTkLabel(inner, text=title, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack()

    def _section(self, title):
        ctk.CTkLabel(self._scroll, text=title, font=FONTS["heading"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(20, 6))
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 8))
        return frame

    def _set_chart(self, val):
        self._chart_range = val
        self._render()
