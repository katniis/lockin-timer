import customtkinter as ctk
from config import COLORS, FONTS, TICK_INTERVAL, INACTIVITY_TIMEOUT
from models.profile import Profile
from models.schedule import Schedule, Block
from services.timer_service import TimerService
from services.schedule_service import ScheduleService
from services.activity_service import ActivityService
from services.sound_service import SoundService
from ui.schedule_builder import ScheduleBuilder
from ui.alert_dialog import AlertDialog


def fmt_time(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_duration(seconds: int) -> str:
    m = seconds // 60
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


class TimerScreen(ctk.CTkFrame):
    def __init__(self, parent, profile: Profile, storage, on_back):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profile = profile
        self._storage = storage
        self._on_back = on_back

        self._timer = None
        self._schedule_svc = None
        self._activity = None
        self._tick_job = None
        self._current_block = None
        self._session_running = False
        self._paused = False
        self._sound = SoundService()

        self._build()

    def _build(self):
        # Top nav bar
        nav = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(
            nav, text="← Back",
            command=self._back,
            fg_color="transparent", hover_color=COLORS["surface2"],
            text_color=COLORS["text_dim"], corner_radius=8,
            height=36, width=80, font=FONTS["small"],
        ).pack(side="left", padx=12, pady=10)

        # Avatar + name
        avatar_frame = ctk.CTkFrame(nav, fg_color=self._profile.avatar_color,
                                     width=32, height=32, corner_radius=16)
        avatar_frame.pack(side="right", padx=(0, 12), pady=12)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text=self._profile.name[0].upper(),
                     font=("Georgia", 13, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(nav, text=self._profile.name, font=FONTS["body_bold"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="right", padx=4, pady=12)

        # Main content: left = timer display, right = schedule builder / stats
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # LEFT PANEL — timer
        self._left = ctk.CTkFrame(content, fg_color=COLORS["surface"], corner_radius=20)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._build_timer_panel()

        # RIGHT PANEL — schedule builder (before session) / block queue (during)
        self._right = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._show_schedule_builder()

    def _build_timer_panel(self):
        for w in self._left.winfo_children():
            w.destroy()

        center = ctk.CTkFrame(self._left, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Block type badge
        block_type = self._current_block.type if self._current_block else "ready"
        badge_color = COLORS["work"] if block_type == "work" else (
            COLORS["break"] if block_type == "break" else COLORS["text_dim"]
        )
        badge_text = block_type.upper() if self._current_block else "READY"

        badge_bg = COLORS["accent_dim"] if block_type == "work" else COLORS["break_dim"]
        badge_frame = ctk.CTkFrame(center, fg_color=badge_bg,
                                    corner_radius=12, height=30)
        badge_frame.pack(pady=(0, 20))

        badge_inner = ctk.CTkFrame(badge_frame, fg_color="transparent")
        badge_inner.pack(padx=16, pady=6)

        dot = ctk.CTkFrame(badge_inner, fg_color=badge_color, width=8, height=8, corner_radius=4)
        dot.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(badge_inner, text=badge_text,
                     font=("Helvetica Neue", 11, "bold"),
                     text_color=badge_color, fg_color="transparent").pack(side="left")

        # Big countdown clock
        self._clock_label = ctk.CTkLabel(
            center,
            text="00:00",
            font=("Courier New", 72, "bold"),
            text_color=COLORS["text"],
            fg_color="transparent",
        )
        self._clock_label.pack()

        # Progress bar
        bar_frame = ctk.CTkFrame(center, fg_color="transparent")
        bar_frame.pack(pady=(12, 24), fill="x")

        self._progress_bar = ctk.CTkProgressBar(
            bar_frame, width=280, height=6,
            fg_color=COLORS["surface2"],
            progress_color=badge_color,
            corner_radius=3,
        )
        self._progress_bar.pack()
        self._progress_bar.set(0)

        # Sub info
        self._sub_label = ctk.CTkLabel(
            center, text="Build your schedule and press Start",
            font=FONTS["small"], text_color=COLORS["text_dim"], fg_color="transparent"
        )
        self._sub_label.pack(pady=(0, 28))

        # Controls
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack()

        if self._session_running:
            self._pause_btn = ctk.CTkButton(
                btn_row,
                text="⏸ Pause" if not self._paused else "▶ Resume",
                command=self._toggle_pause,
                fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
                corner_radius=12, height=44, width=130, font=FONTS["body_bold"],
            )
            self._pause_btn.pack(side="left", padx=6)

            ctk.CTkButton(
                btn_row, text="⏭ Skip",
                command=self._skip,
                fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                text_color=COLORS["text_dim"], corner_radius=12, height=44, width=90,
                font=FONTS["body_bold"],
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                btn_row, text="■ Stop",
                command=self._stop_session,
                fg_color="transparent",
                hover_color=COLORS["danger_dim"],
                text_color=COLORS["danger"],
                border_color=COLORS["danger"], border_width=1,
                corner_radius=12, height=44, width=80,
                font=FONTS["body_bold"],
            ).pack(side="left", padx=6)

    def _show_schedule_builder(self):
        for w in self._right.winfo_children():
            w.destroy()

        builder = ScheduleBuilder(
            self._right,
            self._profile.default_work,
            self._profile.default_break,
            on_start=self._start_session,
        )
        builder.pack(fill="both", expand=True)

    def _show_block_queue(self):
        for w in self._right.winfo_children():
            w.destroy()

        panel = ctk.CTkFrame(self._right, fg_color=COLORS["surface"], corner_radius=16)
        panel.pack(fill="both", expand=True)

        ctk.CTkLabel(panel, text="Session Queue", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(
            anchor="w", padx=20, pady=(20, 8)
        )
        ctk.CTkFrame(panel, fg_color=COLORS["border"], height=1).pack(fill="x", padx=20)

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                         scrollbar_button_color=COLORS["border"])
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        schedule = self._schedule_svc.schedule
        for i, block in enumerate(schedule.blocks):
            is_current = i == schedule.current_index
            is_done = i < schedule.current_index

            row = ctk.CTkFrame(scroll,
                                fg_color=COLORS["accent_highlight"] if is_current else "transparent",
                                corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            color = COLORS["work"] if block.type == "work" else COLORS["break"]
            bar = ctk.CTkFrame(inner, fg_color=color if not is_done else COLORS["text_dim"],
                                width=3, corner_radius=2)
            bar.pack(side="left", fill="y", padx=(0, 10))

            text_color = COLORS["text"] if not is_done else COLORS["text_dim"]
            ctk.CTkLabel(inner,
                         text=f"{'✓ ' if is_done else ''}{block.type.capitalize()}",
                         font=FONTS["body_bold" if is_current else "body"],
                         text_color=text_color, fg_color="transparent").pack(side="left")

            ctk.CTkLabel(inner, text=fmt_duration(block.duration),
                         font=FONTS["small"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(side="right")

        # Stats footer
        stats_frame = ctk.CTkFrame(panel, fg_color=COLORS["surface2"], corner_radius=12)
        stats_frame.pack(fill="x", padx=16, pady=(0, 16))

        s = self._schedule_svc.schedule
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=16, pady=12)

        for label, val in [
            ("Work", fmt_duration(s.total_work())),
            ("Break", fmt_duration(s.total_break())),
            ("Total", fmt_duration(s.total_duration())),
        ]:
            col = ctk.CTkFrame(stats_inner, fg_color="transparent")
            col.pack(side="left", expand=True)
            ctk.CTkLabel(col, text=val, font=FONTS["body_bold"],
                         text_color=COLORS["text"], fg_color="transparent").pack()
            ctk.CTkLabel(col, text=label, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack()

    def _start_session(self, schedule: Schedule):
        self._session_running = True
        self._paused = False

        # Set up timer (callbacks filled in by schedule service)
        self._timer = TimerService(
            on_tick=self._on_tick,
            on_finish=lambda: None,  # overridden by schedule service
        )

        self._schedule_svc = ScheduleService(
            schedule=schedule,
            timer=self._timer,
            profile_name=self._profile.name,
            on_block_change=self._on_block_change,
            on_complete=self._on_complete,
            on_session_done=self._on_session_done,
        )

        # Activity monitoring
        self._activity = ActivityService(
            timeout=INACTIVITY_TIMEOUT,
            on_inactive=self._on_inactive,
        )
        self._activity.start()

        self._schedule_svc.start()
        self._sound.play_session_start()
        self._start_tick_loop()

    def _start_tick_loop(self):
        if self._tick_job:
            self.after_cancel(self._tick_job)
        self._tick()

    def _tick(self):
        if self._session_running and self._timer and not self._paused:
            self._timer.tick()
        self._tick_job = self.after(TICK_INTERVAL, self._tick)

    def _on_tick(self, remaining: int):
        self._clock_label.configure(text=fmt_time(remaining))
        if self._timer:
            self._progress_bar.set(self._timer.progress())

    def _on_block_change(self, block: Block):
        self._current_block = block
        self._clock_label.configure(text=fmt_time(block.duration))
        self._progress_bar.set(0)
        color = COLORS["work"] if block.type == "work" else COLORS["break"]
        self._progress_bar.configure(progress_color=color)
        self._sub_label.configure(
            text=f"Block {self._schedule_svc.schedule.current_index + 1} of {len(self._schedule_svc.schedule.blocks)}"
        )
        # Play the right sound for this block type
        if block.type == "break":
            self._sound.play_break_start()
        else:
            self._sound.play_session_start()
        self._build_timer_panel()
        self._show_block_queue()

    def _on_session_done(self, session_dict: dict):
        self._storage.append_session(self._profile, session_dict)

    def _on_complete(self, sessions: list):
        self._session_running = False
        self._paused = False
        self._current_block = None
        if self._activity:
            self._activity.stop()
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        self._sound.play_completion()
        self._build_timer_panel()
        self._show_completion_panel(sessions)

    def _show_completion_panel(self, sessions: list):
        for w in self._right.winfo_children():
            w.destroy()

        panel = ctk.CTkFrame(self._right, fg_color=COLORS["surface"], corner_radius=16)
        panel.pack(fill="both", expand=True)

        center = ctk.CTkFrame(panel, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center, text="✓", font=("Georgia", 52),
                     text_color=COLORS["success"], fg_color="transparent").pack()

        ctk.CTkLabel(center, text="Session Complete!", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(pady=(8, 4))

        completed = [s for s in sessions if s.get("completed")]
        work_done = sum(s["actual_duration"] for s in completed if s["block_type"] == "work")
        ctk.CTkLabel(
            center,
            text=f"You studied for {fmt_duration(work_done)}",
            font=FONTS["body"], text_color=COLORS["text_dim"], fg_color="transparent"
        ).pack()

        ctk.CTkButton(
            center, text="Start New Session",
            command=self._reset,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            corner_radius=12, height=44, font=FONTS["body_bold"],
        ).pack(pady=(24, 0))

    def _toggle_pause(self):
        if not self._timer:
            return
        self._paused = not self._paused
        if self._paused:
            self._timer.pause()
            self._pause_btn.configure(text="▶ Resume")
        else:
            self._timer.resume()
            self._pause_btn.configure(text="⏸ Pause")

    def _skip(self):
        if self._schedule_svc:
            self._schedule_svc.skip_current()

    def _stop_session(self):
        self._session_running = False
        self._paused = False
        self._current_block = None
        if self._timer:
            self._timer.stop()
        if self._activity:
            self._activity.stop()
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        self._build_timer_panel()
        self._show_schedule_builder()

    def _reset(self):
        self._stop_session()

    def _on_inactive(self):
        """Called from background thread — hop to main thread."""
        self.after(0, self._show_alert)

    def _show_alert(self):
        if self._activity:
            self._sound.play_inactivity()
            AlertDialog(
                self.winfo_toplevel(),
                on_dismiss=self._activity.reset,
            )

    def _back(self):
        self._stop_session()
        self._on_back()

    def destroy(self):
        self._stop_session()
        super().destroy()
