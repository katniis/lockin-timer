import customtkinter as ctk
from config import COLORS, FONTS


def fmt_time(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class MiniWindow(ctk.CTkToplevel):
    """
    Compact always-on-top floating timer. Draggable. No title bar.
    - Scheduled mode: shows pause button only (no break button)
    - Free mode: shows pause + break/resume button; clock turns green on break
    - Inactivity: border + clock pulse orange
    - Completion: pulse green 3x then auto-close
    """

    def __init__(self, parent, get_state, on_pause_toggle, on_break_toggle, on_close):
        super().__init__(parent)
        self._get_state = get_state
        self._on_pause_toggle = on_pause_toggle
        self._on_break_toggle = on_break_toggle
        self._on_close = on_close

        self._drag_x = 0
        self._drag_y = 0
        self._update_job = None
        self._pulse_job = None
        self._pulse_state = False
        self._pulse_count = 0
        self._pulsing_inactive = False
        self._pulsing_complete = False
        self._complete_done_cb = None

        # Cache last state to avoid unnecessary widget reconfigures
        self._last_state = {}

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        # Match outer frame color exactly to eliminate any gap
        self.configure(fg_color=COLORS["surface2"])
        self.geometry("230x100")
        self.resizable(False, False)

        sw = self.winfo_screenwidth()
        self.geometry(f"+{sw - 250}+20")

        self._build()
        self._schedule_update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Outer frame fills window exactly — no padding gap
        self._outer = ctk.CTkFrame(self, fg_color=COLORS["surface2"], corner_radius=14,
                                    border_width=1, border_color=COLORS["border"])
        self._outer.pack(fill="both", expand=True)
        self._bind_drag(self._outer)

        # Top row
        top = ctk.CTkFrame(self._outer, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 0))
        self._bind_drag(top)

        self._badge = ctk.CTkLabel(top, text="●  READY",
                                    font=("Helvetica Neue", 10, "bold"),
                                    text_color=COLORS["text_dim"], fg_color="transparent")
        self._badge.pack(side="left")
        self._bind_drag(self._badge)

        ctk.CTkButton(top, text="✕", width=20, height=20,
                      fg_color="transparent", hover_color=COLORS["border"],
                      text_color=COLORS["text_dim"], corner_radius=4,
                      font=("Helvetica Neue", 11), command=self._close).pack(side="right")

        # Main row
        main = ctk.CTkFrame(self._outer, fg_color="transparent")
        main.pack(fill="x", padx=10, pady=(4, 8))
        self._bind_drag(main)

        self._clock = ctk.CTkLabel(main, text="00:00",
                                    font=("Courier New", 26, "bold"),
                                    text_color=COLORS["text"], fg_color="transparent")
        self._clock.pack(side="left")
        self._bind_drag(self._clock)

        self._btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        self._btn_frame.pack(side="right")

        self._pause_btn = ctk.CTkButton(
            self._btn_frame, text="⏸", width=30, height=30,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            text_color=COLORS["text"], corner_radius=8,
            font=("Helvetica Neue", 13), command=self._on_pause_toggle)
        self._pause_btn.pack(side="left", padx=(0, 4))

        # Break button — starts hidden, shown only for free mode
        self._break_btn = ctk.CTkButton(
            self._btn_frame, text="☕", width=30, height=30,
            fg_color=COLORS["break_dim"], hover_color=COLORS["break"],
            text_color=COLORS["text"], corner_radius=8,
            font=("Helvetica Neue", 13), command=self._on_break_toggle)
        self._break_shown = False  # track whether it's packed

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _bind_drag(self, widget):
        widget.bind("<ButtonPress-1>", self._drag_start)
        widget.bind("<B1-Motion>", self._drag_motion)

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.winfo_x()
        self._drag_y = e.y_root - self.winfo_y()

    def _drag_motion(self, e):
        self.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── Update loop (diff-based to stop flicker) ──────────────────────────────

    def _schedule_update(self):
        self._do_update()

    def _do_update(self):
        try:
            state = self._get_state()
            if state:
                self._apply_state(state)
        except Exception:
            pass
        self._update_job = self.after(500, self._do_update)

    def _apply_state(self, s):
        is_free    = s.get("is_free", False)
        on_break   = s.get("on_break", False)
        running    = s.get("running", False)
        paused     = s.get("paused", False)
        inactive   = s.get("inactive_alert", False)
        block_type = s.get("block_type", "ready")

        # ── Clock ─────────────────────────────────────────────────────────────
        if is_free and on_break:
            clock_text  = fmt_time(s.get("break_elapsed", 0))
            clock_color = COLORS["break"]
        else:
            clock_text  = fmt_time(s.get("time", 0))
            clock_color = COLORS["text"]

        if not self._pulsing_inactive and not self._pulsing_complete:
            if self._last_state.get("clock_text") != clock_text:
                self._clock.configure(text=clock_text)
            if self._last_state.get("clock_color") != clock_color:
                self._clock.configure(text_color=clock_color)

        # ── Badge ─────────────────────────────────────────────────────────────
        if is_free and on_break:
            badge_text, badge_color = "●  BREAK", COLORS["break"]
        elif is_free and running:
            badge_text, badge_color = "●  STUDYING", COLORS["accent2"]
        elif not is_free and block_type == "work":
            badge_text, badge_color = "●  WORK", COLORS["work"]
        elif not is_free and block_type == "break":
            badge_text, badge_color = "●  BREAK", COLORS["break"]
        elif running:
            badge_text, badge_color = "●  RUNNING", COLORS["accent2"]
        else:
            badge_text, badge_color = "●  READY", COLORS["text_dim"]

        if self._last_state.get("badge_text") != badge_text:
            self._badge.configure(text=badge_text, text_color=badge_color)

        # ── Pause button ──────────────────────────────────────────────────────
        pause_text = "▶" if paused else "⏸"
        pause_disabled = is_free and on_break
        if self._last_state.get("pause_text") != pause_text:
            self._pause_btn.configure(text=pause_text)
        if self._last_state.get("pause_disabled") != pause_disabled:
            self._pause_btn.configure(
                fg_color=COLORS["surface2"] if pause_disabled else COLORS["accent_dim"],
                text_color=COLORS["text_dim"] if pause_disabled else COLORS["text"],
                state="disabled" if pause_disabled else "normal")

        # ── Break button (free mode only) ────────────────────────────────────
        want_break_shown = is_free and running
        if want_break_shown != self._break_shown:
            if want_break_shown:
                self._break_btn.pack(side="left")
            else:
                self._break_btn.pack_forget()
            self._break_shown = want_break_shown

        if want_break_shown:
            if on_break:
                brk_text, brk_fg, brk_hover, brk_tc = "▶", COLORS["accent_dim"], COLORS["accent"], COLORS["accent2"]
            else:
                brk_text, brk_fg, brk_hover, brk_tc = "☕", COLORS["break_dim"], COLORS["break"], COLORS["text"]
            if self._last_state.get("brk_text") != brk_text:
                self._break_btn.configure(text=brk_text, fg_color=brk_fg,
                                           hover_color=brk_hover, text_color=brk_tc)

        # ── Inactivity pulse ──────────────────────────────────────────────────
        if inactive and not self._pulsing_inactive and not self._pulsing_complete:
            self._pulsing_inactive = True
            self._pulse_inactive()
        elif not inactive and self._pulsing_inactive:
            self._stop_pulse()
            self._clock.configure(text_color=clock_color)
            self._outer.configure(border_color=COLORS["border"])

        # Cache state
        self._last_state = {
            "clock_text": clock_text, "clock_color": clock_color,
            "badge_text": badge_text,
            "pause_text": pause_text, "pause_disabled": pause_disabled,
            "brk_text": (brk_text if want_break_shown else None),
        }

    # ── Pulse: inactivity (orange) ────────────────────────────────────────────

    def _pulse_inactive(self):
        if not self._pulsing_inactive:
            return
        self._pulse_state = not self._pulse_state
        color = COLORS["warning"] if self._pulse_state else COLORS["border"]
        clock_c = COLORS["warning"] if self._pulse_state else COLORS["text"]
        try:
            self._outer.configure(border_color=color)
            self._clock.configure(text_color=clock_c)
        except Exception:
            return
        self._pulse_job = self.after(600, self._pulse_inactive)

    # ── Pulse: completion (green) — called by main_window ────────────────────

    def pulse_complete(self, on_done=None):
        self._complete_done_cb = on_done
        self._pulsing_complete = True
        self._pulsing_inactive = False
        self._pulse_count = 0
        self._stop_pulse()
        self._pulse_green()

    def _pulse_green(self):
        if not self._pulsing_complete:
            return
        self._pulse_state = not self._pulse_state
        color = COLORS["success"] if self._pulse_state else COLORS["border"]
        clock_c = COLORS["success"] if self._pulse_state else COLORS["text"]
        try:
            self._outer.configure(border_color=color)
            self._clock.configure(text_color=clock_c)
            self._badge.configure(text="●  DONE", text_color=COLORS["success"])
        except Exception:
            return

        if self._pulse_state:
            self._pulse_count += 1

        if self._pulse_count >= 3:
            # Pulses done — hold the green "DONE" state for 5 seconds then close
            try:
                self._outer.configure(border_color=COLORS["success"])
                self._clock.configure(text_color=COLORS["success"])
            except Exception:
                pass
            self.after(5000, self._finish_complete)
        else:
            self._pulse_job = self.after(500, self._pulse_green)

    def _finish_complete(self):
        self._pulsing_complete = False
        cb = self._complete_done_cb
        self._complete_done_cb = None
        if cb:
            cb()

    # ── Pulse utils ────────────────────────────────────────────────────────────

    def _stop_pulse(self):
        if self._pulse_job:
            try:
                self.after_cancel(self._pulse_job)
            except Exception:
                pass
            self._pulse_job = None
        self._pulsing_inactive = False
        self._pulse_state = False

    # ── Close ─────────────────────────────────────────────────────────────────

    def _close(self):
        self._cleanup()
        self._on_close()
        self.destroy()

    def _cleanup(self):
        self._stop_pulse()
        if self._update_job:
            try:
                self.after_cancel(self._update_job)
            except Exception:
                pass
            self._update_job = None

    def destroy(self):
        self._cleanup()
        super().destroy()
