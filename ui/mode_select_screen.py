import customtkinter as ctk
from config import COLORS, FONTS
from models.profile import Profile


class ModeSelectScreen(ctk.CTkFrame):
    def __init__(self, parent, profile: Profile, on_scheduled, on_free, on_back):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._profile = profile
        self._on_scheduled = on_scheduled
        self._on_free = on_free
        self._on_back = on_back
        self._build()

    def _build(self):
        # Nav
        nav = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(nav, text="← Profiles", command=self._on_back,
                      fg_color="transparent", hover_color=COLORS["surface2"],
                      text_color=COLORS["text_dim"], corner_radius=8,
                      height=36, width=100, font=FONTS["small"]).pack(side="left", padx=12, pady=10)

        avatar_frame = ctk.CTkFrame(nav, fg_color=self._profile.avatar_color,
                                     width=32, height=32, corner_radius=16)
        avatar_frame.pack(side="right", padx=(0, 12), pady=12)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text=self._profile.name[0].upper(),
                     font=("Georgia", 13, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(nav, text=self._profile.name, font=FONTS["body_bold"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="right", padx=4)

        # Center content
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="How do you want to study?",
                     font=("Georgia", 26, "bold"), text_color=COLORS["text"],
                     fg_color="transparent").pack(pady=(0, 8))
        ctk.CTkLabel(center, text="Choose a mode for this session",
                     font=FONTS["body"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack(pady=(0, 40))

        cards_row = ctk.CTkFrame(center, fg_color="transparent")
        cards_row.pack()

        self._make_mode_card(
            cards_row,
            icon="⏱",
            title="Scheduled",
            description="Build a custom session with\nwork and break blocks.\nPerfect for structured focus.",
            color=COLORS["accent"],
            color_dim=COLORS["accent_dim"],
            command=self._on_scheduled,
        )

        # Divider
        ctk.CTkFrame(cards_row, fg_color=COLORS["border"], width=1).pack(
            side="left", fill="y", padx=24, pady=20)

        self._make_mode_card(
            cards_row,
            icon="🆓",
            title="Free Mode",
            description="Start a stopwatch and study\nat your own pace. Take breaks\nwhenever you need.",
            color=COLORS["break"],
            color_dim=COLORS["break_dim"],
            command=self._on_free,
        )

    def _make_mode_card(self, parent, icon, title, description, color, color_dim, command):
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=20,
                             border_width=1, border_color=COLORS["border"],
                             width=260, height=280)
        card.pack(side="left")
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")

        # Icon circle
        icon_frame = ctk.CTkFrame(inner, fg_color=color_dim, width=72, height=72, corner_radius=36)
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Georgia", 30),
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=title, font=("Georgia", 20, "bold"),
                     text_color=COLORS["text"], fg_color="transparent").pack(pady=(0, 10))

        ctk.CTkLabel(inner, text=description, font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent",
                     justify="center").pack(pady=(0, 24))

        ctk.CTkButton(inner, text=f"Start {title}",
                      command=command,
                      fg_color=color, hover_color=color,
                      corner_radius=12, height=42, width=180,
                      font=FONTS["body_bold"]).pack()
