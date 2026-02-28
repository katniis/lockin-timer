import customtkinter as ctk
from config import COLORS, FONTS
from models.profile import Profile


AVATAR_COLORS = [
    "#7c6af7", "#f87171", "#34d399", "#fbbf24",
    "#60a5fa", "#f472b6", "#a78bfa", "#2dd4bf",
]


class ProfileScreen(ctk.CTkFrame):
    def __init__(self, parent, storage, on_select_profile):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._storage = storage
        self._on_select = on_select_profile
        self._creating = False
        self._build()
        self._load_profiles()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 0))

        ctk.CTkLabel(
            header, text="LockIn", font=("Georgia", 36, "bold"),
            text_color=COLORS["accent2"], fg_color="transparent"
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Select or create a profile to begin",
            font=FONTS["body"], text_color=COLORS["text_dim"], fg_color="transparent"
        ).pack(side="left", padx=(16, 0), pady=(8, 0))

        # Divider
        div = ctk.CTkFrame(self, fg_color=COLORS["border"], height=1, corner_radius=0)
        div.pack(fill="x", padx=40, pady=(16, 0))

        # Single scrollable area that holds both profiles and the form
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dim"]
        )
        self._scroll.pack(fill="both", expand=True, padx=40, pady=20)

        # Profile grid container (inside scroll)
        self._grid_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._grid_container.pack(fill="both", expand=True)

        # New profile form container (inside scroll, below grid)
        self._form_frame = ctk.CTkFrame(self._scroll, fg_color=COLORS["surface"], corner_radius=16)
        self._form_frame.pack(fill="x", pady=(8, 16))
        self._build_form()

    def _build_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

        if not self._creating:
            btn = ctk.CTkButton(
                self._form_frame,
                text="+ New Profile",
                command=self._show_create_form,
                fg_color=COLORS["accent_dim"],
                hover_color=COLORS["accent"],
                corner_radius=12,
                font=FONTS["body_bold"],
                height=44,
            )
            btn.pack(fill="x", padx=20, pady=16)
            return

        # Form fields
        inner = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(inner, text="New Profile", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(anchor="w")

        ctk.CTkLabel(inner, text="Name", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(12, 2))
        self._name_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g. Alice",
            fg_color=COLORS["surface2"], border_color=COLORS["border"],
            text_color=COLORS["text"], corner_radius=8, height=38,
        )
        self._name_entry.pack(fill="x")

        ctk.CTkLabel(inner, text="Pick a color", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(12, 6))

        color_row = ctk.CTkFrame(inner, fg_color="transparent")
        color_row.pack(anchor="w")
        self._selected_color = ctk.StringVar(value=AVATAR_COLORS[0])

        self._color_btns = []
        for color in AVATAR_COLORS:
            btn = ctk.CTkButton(
                color_row, text="", width=30, height=30, corner_radius=15,
                fg_color=color, hover_color=color,
                command=lambda c=color: self._pick_color(c),
            )
            btn.pack(side="left", padx=3)
            self._color_btns.append((color, btn))

        # Work/Break defaults
        defaults_row = ctk.CTkFrame(inner, fg_color="transparent")
        defaults_row.pack(fill="x", pady=(12, 0))

        for label, attr, default in [
            ("Default work (min)", "_work_var", 25),
            ("Default break (min)", "_break_var", 5),
        ]:
            col = ctk.CTkFrame(defaults_row, fg_color="transparent")
            col.pack(side="left", expand=True, fill="x", padx=(0, 8))
            ctk.CTkLabel(col, text=label, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(0, 4))
            var = ctk.StringVar(value=str(default))
            setattr(self, attr, var)
            ctk.CTkEntry(col, textvariable=var, fg_color=COLORS["surface2"],
                         border_color=COLORS["border"], text_color=COLORS["text"],
                         corner_radius=8, height=36).pack(fill="x")

        # Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(16, 0))

        ctk.CTkButton(
            btn_row, text="Cancel",
            command=self._cancel_create,
            fg_color=COLORS["surface2"], hover_color=COLORS["border"],
            text_color=COLORS["text_dim"], corner_radius=8, height=38,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Create Profile",
            command=self._create_profile,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            corner_radius=8, height=38, font=FONTS["body_bold"],
        ).pack(side="left")

        self._error_label = ctk.CTkLabel(
            inner, text="", font=FONTS["small"],
            text_color=COLORS["danger"], fg_color="transparent"
        )
        self._error_label.pack(anchor="w", pady=(6, 0))

    def _pick_color(self, color: str):
        self._selected_color.set(color)

    def _show_create_form(self):
        self._creating = True
        self._build_form()

    def _cancel_create(self):
        self._creating = False
        self._build_form()

    def _create_profile(self):
        name = self._name_entry.get().strip()
        if not name:
            self._error_label.configure(text="Please enter a name.")
            return
        if self._storage.profile_exists(name):
            self._error_label.configure(text=f"'{name}' already exists.")
            return

        try:
            work = int(self._work_var.get()) * 60
            brk = int(self._break_var.get()) * 60
        except ValueError:
            self._error_label.configure(text="Durations must be numbers.")
            return

        profile = Profile(
            name=name,
            avatar_color=self._selected_color.get(),
            default_work=work,
            default_break=brk,
        )
        self._storage.save_profile(profile)
        self._creating = False
        self._build_form()
        self._load_profiles()

    def _load_profiles(self):
        for w in self._grid_container.winfo_children():
            w.destroy()

        names = self._storage.list_profiles()
        if not names:
            ctk.CTkLabel(
                self._grid_container, text="No profiles yet. Create one below.",
                font=FONTS["body"], text_color=COLORS["text_dim"], fg_color="transparent"
            ).pack(pady=40)
            return

        # Grid: 2 columns
        grid = ctk.CTkFrame(self._grid_container, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, name in enumerate(names):
            try:
                profile = self._storage.load_profile(name)
                self._make_card(grid, profile, i)
            except Exception:
                pass

    def _make_card(self, parent, profile: Profile, index: int):
        row, col = divmod(index, 2)
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=16,
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=20, pady=20)

        # Avatar circle
        avatar = ctk.CTkFrame(inner, fg_color=profile.avatar_color,
                               width=52, height=52, corner_radius=26)
        avatar.pack(side="left", padx=(0, 16))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=profile.name[0].upper(),
                     font=("Georgia", 22, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(info, text=profile.name, font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent", anchor="w").pack(anchor="w")

        hours = profile.total_work_seconds() // 3600
        sessions = profile.total_sessions()
        ctk.CTkLabel(
            info,
            text=f"{hours}h studied · {sessions} sessions",
            font=FONTS["small"], text_color=COLORS["text_dim"],
            fg_color="transparent", anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Buttons row
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row, text="Select",
            command=lambda p=profile: self._on_select(p),
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            corner_radius=8, height=32, width=80, font=FONTS["small"],
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            btn_row, text="Delete",
            command=lambda p=profile: self._delete(p),
            fg_color="transparent", hover_color=COLORS["danger_dim"],
            text_color=COLORS["danger"], border_color=COLORS["danger"],
            border_width=1, corner_radius=8, height=32, width=80, font=FONTS["small"],
        ).pack()

    def _delete(self, profile: Profile):
        self._storage.delete_profile(profile.name)
        self._load_profiles()
