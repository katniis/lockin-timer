import customtkinter as ctk
from config import COLORS, FONTS, APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from models.profile import Profile
from services.storage_service import StorageService
from ui.profile_screen import ProfileScreen
from ui.mode_select_screen import ModeSelectScreen
from ui.timer_screen import TimerScreen
from ui.free_mode_screen import FreeModeScreen
from ui.stats_screen import StatsScreen
from ui.general_stats_screen import GeneralStatsScreen
from ui.mini_window import MiniWindow


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._storage = StorageService()
        self._profile = None
        self._nav_bar = None
        self._mini_window = None
        self._mini_btn = None

        # Session frames — kept alive while switching tabs
        self._timer_frame = None
        self._free_frame = None
        self._active_tab = None      # "timer" | "free" | "stats"

        # Non-session overlay (profiles, mode-select, stats, rewards)
        self._overlay = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(800, 560)
        self.configure(fg_color=COLORS["bg"])

        # Icon
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "..", "icon", "logo_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self._content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._content.pack(fill="both", expand=True)

        self._show_profiles()

    # ── Overlay management ────────────────────────────────────────────────────

    def _set_overlay(self, frame):
        """Destroy old overlay, hide session frames, show new overlay."""
        if self._overlay:
            self._overlay.destroy()
        self._overlay = frame
        # Hide all content children then show overlay
        for child in self._content.winfo_children():
            child.pack_forget()
        frame.pack(fill="both", expand=True)

    def _clear_overlay(self):
        """Remove overlay and reveal whatever session tab is active."""
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        self._show_active_session()

    def _show_active_session(self):
        """Pack-show only the active session frame."""
        for child in self._content.winfo_children():
            child.pack_forget()
        if self._active_tab == "timer" and self._timer_frame:
            self._timer_frame.pack(fill="both", expand=True)
        elif self._active_tab == "free" and self._free_frame:
            self._free_frame.pack(fill="both", expand=True)

    # ── Top-level screens ─────────────────────────────────────────────────────

    def _show_profiles(self):
        self._hide_nav()
        self._destroy_sessions()
        self._set_overlay(ProfileScreen(
            self._content,
            storage=self._storage,
            on_select_profile=self._on_profile_selected,
            on_general_stats=self._show_general_stats,
            on_rewards=self._show_rewards,
        ))

    def _on_profile_selected(self, profile: Profile):
        self._profile = profile
        self._show_mode_select()

    def _show_mode_select(self):
        self._hide_nav()
        self._destroy_sessions()
        self._set_overlay(ModeSelectScreen(
            self._content,
            profile=self._profile,
            on_scheduled=self._enter_timer,
            on_free=self._enter_free,
            on_back=self._show_profiles,
        ))

    def _show_general_stats(self):
        self._hide_nav()
        self._destroy_sessions()
        profiles = self._load_all_profiles()
        self._set_overlay(GeneralStatsScreen(
            self._content,
            profiles=profiles,
            storage=self._storage,
            on_back=self._show_profiles,
        ))

    def _show_rewards(self):
        from ui.rewards_screen import RewardsScreen
        self._hide_nav()
        self._destroy_sessions()
        profiles = self._load_all_profiles()
        self._set_overlay(RewardsScreen(
            self._content,
            profiles=profiles,
            storage=self._storage,
            on_back=self._show_profiles,
        ))

    def _load_all_profiles(self):
        profiles = []
        for name in self._storage.list_profiles():
            try:
                profiles.append(self._storage.load_profile(name))
            except Exception:
                pass
        return profiles

    # ── Session entry — create frames on demand ───────────────────────────────

    def _enter_timer(self):
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        # Destroy free frame — can't run both simultaneously
        if self._free_frame:
            self._free_frame.destroy()
            self._free_frame = None
        if self._timer_frame is None:
            self._timer_frame = TimerScreen(
                self._content,
                profile=self._profile,
                storage=self._storage,
                on_back=self._show_mode_select,
                on_complete=self._on_session_complete,
            )
        self._build_nav_bar("timer")
        self._switch_tab("timer")

    def _enter_free(self):
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        # Destroy timer frame — can't run both simultaneously
        if self._timer_frame:
            self._timer_frame.destroy()
            self._timer_frame = None
        if self._free_frame is None:
            self._free_frame = FreeModeScreen(
                self._content,
                profile=self._profile,
                storage=self._storage,
                on_back=self._show_mode_select,
                on_complete=self._on_session_complete,
            )
        self._build_nav_bar("free")
        self._switch_tab("free")

    def _destroy_sessions(self):
        if self._timer_frame:
            self._timer_frame.destroy()
            self._timer_frame = None
        if self._free_frame:
            self._free_frame.destroy()
            self._free_frame = None
        self._active_tab = None

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, tab: str):
        prev_tab = self._active_tab
        self._active_tab = tab
        self._update_nav_highlight()

        if tab == "stats":
            stats = StatsScreen(
                self._content,
                profile=self._profile,
                storage=self._storage,
                on_back=self._on_stats_back,
            )
            self._set_overlay(stats)
            return

        # For timer/free tabs: destroy opposite frame, create this one on demand
        if tab == "timer":
            if self._free_frame:
                self._free_frame.destroy()
                self._free_frame = None
            if self._timer_frame is None:
                self._timer_frame = TimerScreen(
                    self._content,
                    profile=self._profile,
                    storage=self._storage,
                    on_back=self._show_mode_select,
                    on_complete=self._on_session_complete,
                )
        elif tab == "free":
            if self._timer_frame:
                self._timer_frame.destroy()
                self._timer_frame = None
            if self._free_frame is None:
                self._free_frame = FreeModeScreen(
                    self._content,
                    profile=self._profile,
                    storage=self._storage,
                    on_back=self._show_mode_select,
                    on_complete=self._on_session_complete,
                )

        self._clear_overlay()

    def _on_stats_back(self):
        """Return from stats to whichever session tab was active before."""
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        # If active tab is still "stats" (set before going to stats), revert to last session
        if self._timer_frame:
            self._active_tab = "timer"
        elif self._free_frame:
            self._active_tab = "free"
        self._update_nav_highlight()
        self._show_active_session()

    # ── Completion pulse ──────────────────────────────────────────────────────

    def _on_session_complete(self):
        if self._mini_window:
            self._mini_window.pulse_complete(on_done=self._close_mini)

    # ── Nav bar ───────────────────────────────────────────────────────────────

    def _build_nav_bar(self, active: str):
        if self._nav_bar:
            self._nav_bar.destroy()

        self._nav_bar = ctk.CTkFrame(self, fg_color=COLORS["surface"],
                                      corner_radius=0, height=58,
                                      border_width=1, border_color=COLORS["border"])
        self._nav_bar.pack(side="bottom", fill="x")
        self._nav_bar.pack_propagate(False)

        left = ctk.CTkFrame(self._nav_bar, fg_color="transparent")
        left.pack(side="left", fill="y")

        self._nav_btns = {}
        for tab_id, icon, label in [("timer", "⏱", "Timer"),
                                     ("free",  "🆓", "Free Mode"),
                                     ("stats", "📊", "My Stats")]:
            is_active = tab_id == active
            btn = ctk.CTkButton(
                left,
                text=f"{icon}  {label}",
                command=lambda t=tab_id: self._switch_tab(t),
                fg_color=COLORS["accent_dim"] if is_active else "transparent",
                hover_color=COLORS["surface2"],
                text_color=COLORS["accent2"] if is_active else COLORS["text_dim"],
                corner_radius=10, height=40, width=128, font=FONTS["body"],
            )
            btn.pack(side="left", padx=8, pady=9)
            self._nav_btns[tab_id] = btn

        right = ctk.CTkFrame(self._nav_bar, fg_color="transparent")
        right.pack(side="right", padx=16)

        self._mini_btn = ctk.CTkButton(
            right, text="□  Mini", command=self._toggle_mini,
            fg_color=COLORS["surface2"], hover_color=COLORS["border"],
            text_color=COLORS["text_dim"], corner_radius=8,
            height=32, width=84, font=FONTS["small"],
        )
        self._mini_btn.pack(side="left", padx=4)
        self._active_tab = active

    def _update_nav_highlight(self):
        if not hasattr(self, "_nav_btns"):
            return
        for tab_id, btn in self._nav_btns.items():
            if tab_id == self._active_tab:
                btn.configure(fg_color=COLORS["accent_dim"], text_color=COLORS["accent2"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_dim"])

    def _hide_nav(self):
        if self._nav_bar:
            self._nav_bar.destroy()
            self._nav_bar = None
        self._close_mini()

    # ── Mini window ───────────────────────────────────────────────────────────

    def _toggle_mini(self):
        if self._mini_window:
            self._close_mini()
        else:
            self._mini_window = MiniWindow(
                self,
                get_state=self._get_timer_state,
                on_pause_toggle=self._mini_pause,
                on_break_toggle=self._mini_break,
                on_close=self._on_mini_closed,
            )
            if self._mini_btn:
                self._mini_btn.configure(text="■  Mini", fg_color=COLORS["accent_dim"],
                                          text_color=COLORS["accent2"])

    def _close_mini(self):
        if self._mini_window:
            try:
                self._mini_window.destroy()
            except Exception:
                pass
            self._mini_window = None
        if self._mini_btn:
            try:
                self._mini_btn.configure(text="□  Mini", fg_color=COLORS["surface2"],
                                          text_color=COLORS["text_dim"])
            except Exception:
                pass

    def _on_mini_closed(self):
        self._mini_window = None
        if self._mini_btn:
            try:
                self._mini_btn.configure(text="□  Mini", fg_color=COLORS["surface2"],
                                          text_color=COLORS["text_dim"])
            except Exception:
                pass

    def _get_timer_state(self):
        if self._timer_frame and self._timer_frame._session_running:
            f = self._timer_frame
            return {
                "time": f._timer.remaining if f._timer else 0,
                "block_type": f._current_block.type if f._current_block else "work",
                "on_break": False, "break_elapsed": 0,
                "paused": f._paused, "running": True, "is_free": False,
                "inactive_alert": getattr(f, "_inactive_alerted", False),
            }
        if self._free_frame and self._free_frame._running:
            f = self._free_frame
            return {
                "time": f._elapsed,
                "block_type": "break" if f._on_break else "work",
                "on_break": f._on_break, "break_elapsed": f._break_elapsed,
                "paused": f._paused, "running": True, "is_free": True,
                "inactive_alert": getattr(f, "_inactive_alerted", False),
            }
        return {"time": 0, "block_type": "ready", "paused": False,
                "running": False, "is_free": False, "inactive_alert": False,
                "on_break": False, "break_elapsed": 0}

    def _mini_pause(self):
        if self._timer_frame and self._timer_frame._session_running:
            self._timer_frame._toggle_pause()
        elif self._free_frame and self._free_frame._running and not self._free_frame._on_break:
            self._free_frame._toggle_pause()

    def _mini_break(self):
        if self._free_frame:
            if self._free_frame._on_break:
                self._free_frame._end_break()
            elif self._free_frame._running:
                self._free_frame._start_break()
