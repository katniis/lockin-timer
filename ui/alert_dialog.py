import customtkinter as ctk
from config import COLORS, FONTS


class AlertDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_dismiss=None):
        super().__init__(parent)
        self._on_dismiss = on_dismiss

        self.title("")
        self.geometry("380x220")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["surface"])
        self.attributes("-topmost", True)

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2 - 190
        py = parent.winfo_y() + parent.winfo_height() // 2 - 110
        self.geometry(f"+{px}+{py}")

        self._build()
        self.grab_set()

    def _build(self):
        # Warning icon area
        icon_frame = ctk.CTkFrame(self, fg_color=COLORS["warning_dim"], corner_radius=40,
                                   width=64, height=64)
        icon_frame.place(relx=0.5, rely=0.22, anchor="center")
        icon_frame.pack_propagate(False)

        icon = ctk.CTkLabel(icon_frame, text="⚠", font=("Georgia", 28),
                             text_color=COLORS["warning"], fg_color="transparent")
        icon.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(self, text="Are you still there?",
                              font=FONTS["heading"], text_color=COLORS["text"],
                              fg_color="transparent")
        title.place(relx=0.5, rely=0.52, anchor="center")

        sub = ctk.CTkLabel(self, text="You've been inactive for a while.\nYour timer is still running.",
                            font=FONTS["small"], text_color=COLORS["text_dim"],
                            fg_color="transparent", justify="center")
        sub.place(relx=0.5, rely=0.67, anchor="center")

        btn = ctk.CTkButton(
            self, text="I'm here — resume",
            command=self._dismiss,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent2"],
            corner_radius=10,
            font=FONTS["body_bold"],
            width=200, height=38,
        )
        btn.place(relx=0.5, rely=0.87, anchor="center")

    def _dismiss(self):
        if self._on_dismiss:
            self._on_dismiss()
        self.destroy()
