import customtkinter as ctk
from config import COLORS, APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from models.profile import Profile
from services.storage_service import StorageService
from ui.profile_screen import ProfileScreen
from ui.timer_screen import TimerScreen


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._storage = StorageService()
        self._current_frame = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(800, 540)
        self.configure(fg_color=COLORS["bg"])

        self._show_profiles()

    def _show_profiles(self):
        self._swap(ProfileScreen(
            self,
            storage=self._storage,
            on_select_profile=self._show_timer,
        ))

    def _show_timer(self, profile: Profile):
        self._swap(TimerScreen(
            self,
            profile=profile,
            storage=self._storage,
            on_back=self._show_profiles,
        ))

    def _swap(self, frame: ctk.CTkFrame):
        if self._current_frame:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True)
