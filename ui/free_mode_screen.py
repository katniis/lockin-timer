import customtkinter as ctk
from datetime import datetime
from config import COLORS, FONTS, TICK_INTERVAL, INACTIVITY_TIMEOUT
from models.profile import Profile
from services.activity_service import ActivityService
from services.sound_service import SoundService
from ui.alert_dialog import AlertDialog


def fmt_stopwatch(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


MILESTONE_INTERVAL = 25 * 60


class FreeModeScreen(ctk.CTkFrame):
    def __init__(self, parent, profile: Profile, storage, on_back, on_complete=None):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profile = profile
        self._storage = storage
        self._on_back = on_back
        self._on_complete_cb = on_complete

        self._elapsed = 0
        self._break_elapsed = 0
        self._running = False
        self._on_break = False
        self._paused = False
        self._inactive_alerted = False
        self._was_paused_by_alert = False
        self._session_start = None
        self._tick_job = None
        self._next_milestone = MILESTONE_INTERVAL
        self._activity = None
        self._sound = SoundService()

        self._build()

    def _build(self):
        nav = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(nav, text="← Back", command=self._back,
                      fg_color="transparent", hover_color=COLORS["surface2"],
                      text_color=COLORS["text_dim"], corner_radius=8,
                      height=36, width=80, font=FONTS["small"]).pack(side="left", padx=12, pady=10)

        badge = ctk.CTkFrame(nav, fg_color=COLORS["accent_dim"], corner_radius=10)
        badge.pack(side="left", padx=8, pady=14)
        ctk.CTkLabel(badge, text="FREE MODE", font=("Helvetica Neue", 10, "bold"),
                     text_color=COLORS["accent2"], fg_color="transparent").pack(padx=12, pady=4)

        avatar_frame = ctk.CTkFrame(nav, fg_color=self._profile.avatar_color,
                                     width=32, height=32, corner_radius=16)
        avatar_frame.pack(side="right", padx=(0, 12), pady=12)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text=self._profile.name[0].upper(),
                     font=("Georgia", 13, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(nav, text=self._profile.name, font=FONTS["body_bold"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="right", padx=4)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._left = ctk.CTkFrame(content, fg_color=COLORS["surface"], corner_radius=20)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self._right = ctk.CTkFrame(content, fg_color=COLORS["surface"], corner_radius=20)
        self._right.grid(row=0, column=1, sticky="nsew")

        self._build_main_panel()
        self._build_side_panel()

    def _build_main_panel(self):
        for w in self._left.winfo_children():
            w.destroy()

        center = ctk.CTkFrame(self._left, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        if self._on_break:
            badge_text, badge_color, badge_bg = "ON BREAK", COLORS["break"], COLORS["break_dim"]
        elif self._running:
            badge_text, badge_color, badge_bg = "STUDYING", COLORS["work"], COLORS["accent_dim"]
        else:
            badge_text, badge_color, badge_bg = "READY", COLORS["text_dim"], COLORS["surface2"]

        badge_frame = ctk.CTkFrame(center, fg_color=badge_bg, corner_radius=12)
        badge_frame.pack(pady=(0, 20))
        badge_inner = ctk.CTkFrame(badge_frame, fg_color="transparent")
        badge_inner.pack(padx=16, pady=6)
        ctk.CTkFrame(badge_inner, fg_color=badge_color, width=8, height=8,
                     corner_radius=4).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(badge_inner, text=badge_text, font=("Helvetica Neue", 11, "bold"),
                     text_color=badge_color, fg_color="transparent").pack(side="left")

        self._clock_label = ctk.CTkLabel(
            center, text=fmt_stopwatch(self._elapsed),
            font=("Courier New", 72, "bold"),
            text_color=COLORS["text"], fg_color="transparent")
        self._clock_label.pack()

        self._milestone_label = ctk.CTkLabel(
            center, text=self._milestone_text(),
            font=FONTS["small"], text_color=COLORS["text_dim"], fg_color="transparent")
        self._milestone_label.pack(pady=(8, 28))

        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack()

        if not self._running and not self._on_break:
            ctk.CTkButton(btn_row, text="▶ Start", command=self._start,
                          fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                          corner_radius=12, height=44, width=130,
                          font=FONTS["body_bold"]).pack(side="left", padx=6)

        elif self._running and not self._on_break:
            self._pause_btn = ctk.CTkButton(
                btn_row, text="⏸ Pause" if not self._paused else "▶ Resume",
                command=self._toggle_pause,
                fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
                corner_radius=12, height=44, width=130, font=FONTS["body_bold"])
            self._pause_btn.pack(side="left", padx=6)

            ctk.CTkButton(btn_row, text="☕ Break", command=self._start_break,
                          fg_color=COLORS["break_dim"], hover_color=COLORS["break"],
                          text_color=COLORS["text"], corner_radius=12, height=44, width=100,
                          font=FONTS["body_bold"]).pack(side="left", padx=6)

            ctk.CTkButton(btn_row, text="■ End", command=self._end_session,
                          fg_color="transparent", hover_color=COLORS["danger_dim"],
                          text_color=COLORS["danger"], border_color=COLORS["danger"],
                          border_width=1, corner_radius=12, height=44, width=80,
                          font=FONTS["body_bold"]).pack(side="left", padx=6)

        elif self._on_break:
            ctk.CTkButton(btn_row, text="▶ Resume Study", command=self._end_break,
                          fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                          corner_radius=12, height=44, width=160,
                          font=FONTS["body_bold"]).pack(side="left", padx=6)
            ctk.CTkButton(btn_row, text="■ End Session", command=self._end_session,
                          fg_color="transparent", hover_color=COLORS["danger_dim"],
                          text_color=COLORS["danger"], border_color=COLORS["danger"],
                          border_width=1, corner_radius=12, height=44, width=120,
                          font=FONTS["body_bold"]).pack(side="left", padx=6)

    def _build_side_panel(self):
        for w in self._right.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._right, text="Break Timer", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(anchor="w", padx=20, pady=(24, 0))
        ctk.CTkFrame(self._right, fg_color=COLORS["border"], height=1).pack(fill="x", padx=20, pady=(12, 16))

        break_center = ctk.CTkFrame(self._right, fg_color="transparent")
        break_center.pack(fill="x", padx=20)

        if self._on_break:
            self._break_label = ctk.CTkLabel(break_center,
                                              text=fmt_stopwatch(self._break_elapsed),
                                              font=("Courier New", 40, "bold"),
                                              text_color=COLORS["break"], fg_color="transparent")
            self._break_label.pack()
            ctk.CTkLabel(break_center, text="You're on a break — recharge!",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(pady=(6, 0))
        else:
            self._break_label = None
            ctk.CTkLabel(break_center, text="--:--",
                         font=("Courier New", 40, "bold"),
                         text_color=COLORS["text_dim"], fg_color="transparent").pack()
            ctk.CTkLabel(break_center, text="No active break",
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(pady=(6, 0))

        ctk.CTkFrame(self._right, fg_color=COLORS["border"], height=1).pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(self._right, text="This Session", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(anchor="w", padx=20)

        stats_grid = ctk.CTkFrame(self._right, fg_color=COLORS["surface2"], corner_radius=12)
        stats_grid.pack(fill="x", padx=20, pady=(12, 0))
        inner = ctk.CTkFrame(stats_grid, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        h = self._elapsed // 3600
        m = (self._elapsed % 3600) // 60
        time_str = f"{h}h {m}m" if h else f"{m}m"

        for label, val in [
            ("Study time", time_str if self._running or self._on_break else "—"),
            ("Milestones", f"Every 25 min"),
            ("Status", "On break" if self._on_break else ("Studying" if self._running else "Not started")),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONTS["small"],
                         text_color=COLORS["text"], fg_color="transparent").pack(side="right")

    def _milestone_text(self) -> str:
        if not self._running:
            return "Start to begin tracking"
        remaining = self._next_milestone - self._elapsed
        if remaining <= 0:
            return "Milestone reached! 🎉"
        m, s = divmod(remaining, 60)
        return f"Next milestone in {m:02d}:{s:02d}"

    def _start(self):
        self._elapsed = 0
        self._running = True
        self._paused = False
        self._session_start = datetime.now().isoformat()
        self._next_milestone = MILESTONE_INTERVAL
        self._sound.play_session_start()

        timeout = getattr(self._profile, "inactivity_timeout", INACTIVITY_TIMEOUT)
        self._activity = ActivityService(timeout=timeout, on_inactive=self._on_inactive)
        self._activity.start()

        self._build_main_panel()
        self._build_side_panel()
        self._tick()

    def _start_break(self):
        self._on_break = True
        self._break_elapsed = 0
        self._sound.play_break_start()
        self._build_main_panel()
        self._build_side_panel()

    def _end_break(self):
        self._on_break = False
        self._sound.play_session_start()
        self._build_main_panel()
        self._build_side_panel()

    def _toggle_pause(self):
        self._paused = not self._paused
        try:
            self._pause_btn.configure(text="▶ Resume" if self._paused else "⏸ Pause")
        except Exception:
            pass

    def _end_session(self):
        self._running = False
        self._on_break = False
        self._paused = False
        self._inactive_alerted = False
        self._was_paused_by_alert = False

        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        if self._activity:
            self._activity.stop()

        if self._elapsed > 0:
            record = {"duration": self._elapsed,
                      "date": self._session_start or datetime.now().isoformat()}
            self._profile.free_sessions.append(record)
            self._storage.save_profile(self._profile)

        self._sound.play_completion()
        self._show_summary()
        if self._on_complete_cb:
            self._on_complete_cb()

    def _show_summary(self):
        for w in self._left.winfo_children():
            w.destroy()
        for w in self._right.winfo_children():
            w.destroy()

        center = ctk.CTkFrame(self._left, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="✓", font=("Georgia", 52),
                     text_color=COLORS["success"], fg_color="transparent").pack()
        ctk.CTkLabel(center, text="Session Complete!", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(pady=(8, 4))

        h, rem = divmod(self._elapsed, 3600)
        m = rem // 60
        time_str = f"{h}h {m}m" if h else f"{m}m"
        ctk.CTkLabel(center, text=f"You studied for {time_str}",
                     font=FONTS["body"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack()

        ctk.CTkButton(center, text="New Session", command=self._reset,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                      corner_radius=12, height=44, font=FONTS["body_bold"]).pack(pady=(24, 0))

        tip = ctk.CTkFrame(self._right, fg_color="transparent")
        tip.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(tip, text="Great work!", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack()
        ctk.CTkLabel(tip, text="Check Stats to see\nyour progress over time.",
                     font=FONTS["body"], text_color=COLORS["text_dim"],
                     fg_color="transparent", justify="center").pack(pady=(8, 0))

    def _reset(self):
        self._elapsed = 0
        self._break_elapsed = 0
        self._running = False
        self._on_break = False
        self._paused = False
        self._inactive_alerted = False
        self._was_paused_by_alert = False
        self._session_start = None
        self._next_milestone = MILESTONE_INTERVAL
        self._build_main_panel()
        self._build_side_panel()

    def _tick(self):
        if not self._running:
            return
        if not self._paused:
            if self._on_break:
                self._break_elapsed += 1
                if self._break_label:
                    try:
                        self._break_label.configure(text=fmt_stopwatch(self._break_elapsed))
                    except Exception:
                        pass
                if self._break_elapsed == 20 * 60:
                    self.after(0, self._show_break_nudge)
            else:
                self._elapsed += 1
                try:
                    self._clock_label.configure(text=fmt_stopwatch(self._elapsed))
                    self._milestone_label.configure(text=self._milestone_text())
                except Exception:
                    pass
                if self._elapsed >= self._next_milestone:
                    self._next_milestone += MILESTONE_INTERVAL
                    self._sound.play_session_start()

        self._tick_job = self.after(TICK_INTERVAL, self._tick)

    def _show_break_nudge(self):
        class NudgeDialog(ctk.CTkToplevel):
            def __init__(self, parent, on_resume, on_end):
                super().__init__(parent)
                self.title("")
                self.geometry("360x200")
                self.resizable(False, False)
                self.configure(fg_color=COLORS["surface"])
                self.attributes("-topmost", True)
                px = parent.winfo_x() + parent.winfo_width() // 2 - 180
                py = parent.winfo_y() + parent.winfo_height() // 2 - 100
                self.geometry(f"+{px}+{py}")

                ctk.CTkLabel(self, text="☕  Long break!", font=FONTS["heading"],
                             text_color=COLORS["warning"], fg_color="transparent").pack(pady=(28, 4))
                ctk.CTkLabel(self, text="You've been on break for 20 minutes.\nReady to get back?",
                             font=FONTS["small"], text_color=COLORS["text_dim"],
                             fg_color="transparent", justify="center").pack()

                row = ctk.CTkFrame(self, fg_color="transparent")
                row.pack(pady=20)
                ctk.CTkButton(row, text="▶ Resume",
                              command=lambda: (on_resume(), self.destroy()),
                              fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                              corner_radius=8, height=36, font=FONTS["body_bold"]).pack(side="left", padx=8)
                ctk.CTkButton(row, text="End Session",
                              command=lambda: (on_end(), self.destroy()),
                              fg_color="transparent", hover_color=COLORS["danger_dim"],
                              text_color=COLORS["danger"], border_color=COLORS["danger"],
                              border_width=1, corner_radius=8, height=36).pack(side="left", padx=8)
                self.grab_set()

        NudgeDialog(self.winfo_toplevel(), on_resume=self._end_break, on_end=self._end_session)

    def _on_inactive(self):
        self.after(0, self._show_alert)

    def _show_alert(self):
        if not self._activity or not self._running:
            return
        self._inactive_alerted = True
        # Auto-pause while alert is shown (only if not on break and not already paused)
        self._was_paused_by_alert = False
        if not self._on_break and not self._paused:
            self._paused = True
            self._was_paused_by_alert = True
            try:
                self._pause_btn.configure(text="▶ Resume")
            except Exception:
                pass
        self._sound.play_inactivity()
        AlertDialog(self.winfo_toplevel(), on_dismiss=self._on_alert_dismissed)

    def _on_alert_dismissed(self):
        self._inactive_alerted = False
        if self._was_paused_by_alert and self._running and not self._on_break:
            self._paused = False
            self._was_paused_by_alert = False
            try:
                self._pause_btn.configure(text="⏸ Pause")
            except Exception:
                pass
        if self._activity:
            self._activity.reset()

    def _back(self):
        if self._running:
            self._end_session()
        else:
            if self._tick_job:
                self.after_cancel(self._tick_job)
            if self._activity:
                self._activity.stop()
        self._on_back()

    def destroy(self):
        self._running = False
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
        if self._activity:
            self._activity.stop()
        super().destroy()
