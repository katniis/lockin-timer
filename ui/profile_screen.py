import customtkinter as ctk
from config import COLORS, FONTS
from models.profile import Profile


AVATAR_COLORS = [
    "#7c6af7", "#f87171", "#34d399", "#fbbf24",
    "#60a5fa", "#f472b6", "#a78bfa", "#2dd4bf",
]


class ProfileScreen(ctk.CTkFrame):
    def __init__(self, parent, storage, on_select_profile, on_general_stats=None):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._storage = storage
        self._on_select = on_select_profile
        self._on_general_stats = on_general_stats
        self._creating = False
        self._editing = None
        self._build()
        self._load_profiles()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 0))

        ctk.CTkLabel(header, text="LockIn", font=("Georgia", 36, "bold"),
                     text_color=COLORS["accent2"], fg_color="transparent").pack(side="left")
        ctk.CTkLabel(header, text="Select or create a profile to begin",
                     font=FONTS["body"], text_color=COLORS["text_dim"],
                     fg_color="transparent").pack(side="left", padx=(16, 0), pady=(8, 0))

        if self._on_general_stats:
            ctk.CTkButton(
                header, text="📊  General Stats",
                command=self._on_general_stats,
                fg_color=COLORS["surface"], hover_color=COLORS["surface2"],
                text_color=COLORS["text_dim"], border_color=COLORS["border"],
                border_width=1, corner_radius=10,
                height=36, font=FONTS["small"],
            ).pack(side="right")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).pack(fill="x", padx=40, pady=(16, 0))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                               scrollbar_button_color=COLORS["border"],
                                               scrollbar_button_hover_color=COLORS["accent_dim"])
        self._scroll.pack(fill="both", expand=True, padx=40, pady=20)

        self._grid_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._grid_container.pack(fill="both", expand=True)

        self._form_frame = ctk.CTkFrame(self._scroll, fg_color=COLORS["surface"], corner_radius=16)
        self._form_frame.pack(fill="x", pady=(8, 16))
        self._build_form()

    # ── Form ────────────────────────────────────────────────────────────────

    def _build_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

        if not self._creating and not self._editing:
            ctk.CTkButton(self._form_frame, text="+ New Profile",
                          command=self._show_create_form,
                          fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
                          corner_radius=12, font=FONTS["body_bold"], height=44,
                          ).pack(fill="x", padx=20, pady=16)
            return

        is_edit = self._editing is not None
        title = "Edit Profile" if is_edit else "New Profile"

        inner = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(inner, text=title, font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(anchor="w")

        ctk.CTkLabel(inner, text="Name", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(12, 2))
        self._name_entry = ctk.CTkEntry(inner, placeholder_text="e.g. Alice",
                                         fg_color=COLORS["surface2"], border_color=COLORS["border"],
                                         text_color=COLORS["text"], corner_radius=8, height=38)
        self._name_entry.pack(fill="x")
        if is_edit:
            self._name_entry.insert(0, self._editing.name)

        ctk.CTkLabel(inner, text="Pick a color", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(12, 6))

        color_row = ctk.CTkFrame(inner, fg_color="transparent")
        color_row.pack(anchor="w")
        self._selected_color = ctk.StringVar(value=self._editing.avatar_color if is_edit else AVATAR_COLORS[0])

        for color in AVATAR_COLORS:
            ctk.CTkButton(color_row, text="", width=30, height=30, corner_radius=15,
                          fg_color=color, hover_color=color,
                          command=lambda c=color: self._pick_color(c),
                          ).pack(side="left", padx=3)

        defaults_row = ctk.CTkFrame(inner, fg_color="transparent")
        defaults_row.pack(fill="x", pady=(12, 0))

        defaults = [
            ("Default work (min)", "_work_var", (self._editing.default_work // 60) if is_edit else 25),
            ("Default break (min)", "_break_var", (self._editing.default_break // 60) if is_edit else 5),
            ("Inactivity alert (sec)", "_idle_var", getattr(self._editing, "inactivity_timeout", 60) if is_edit else 60),
        ]
        for label, attr, default in defaults:
            col = ctk.CTkFrame(defaults_row, fg_color="transparent")
            col.pack(side="left", expand=True, fill="x", padx=(0, 8))
            ctk.CTkLabel(col, text=label, font=FONTS["small"],
                         text_color=COLORS["text_dim"], fg_color="transparent").pack(anchor="w", pady=(0, 4))
            var = ctk.StringVar(value=str(default))
            setattr(self, attr, var)
            ctk.CTkEntry(col, textvariable=var, fg_color=COLORS["surface2"],
                         border_color=COLORS["border"], text_color=COLORS["text"],
                         corner_radius=8, height=36).pack(fill="x")

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(16, 0))

        ctk.CTkButton(btn_row, text="Cancel", command=self._cancel_form,
                      fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                      text_color=COLORS["text_dim"], corner_radius=8, height=38,
                      ).pack(side="left", padx=(0, 8))

        save_text = "Save Changes" if is_edit else "Create Profile"
        ctk.CTkButton(btn_row, text=save_text,
                      command=self._save_profile,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                      corner_radius=8, height=38, font=FONTS["body_bold"],
                      ).pack(side="left")

        self._error_label = ctk.CTkLabel(inner, text="", font=FONTS["small"],
                                          text_color=COLORS["danger"], fg_color="transparent")
        self._error_label.pack(anchor="w", pady=(6, 0))

    def _pick_color(self, color):
        self._selected_color.set(color)

    def _show_create_form(self):
        self._creating = True
        self._editing = None
        self._build_form()

    def _show_edit_form(self, profile):
        self._editing = profile
        self._creating = False
        self._build_form()

    def _cancel_form(self):
        self._creating = False
        self._editing = None
        self._build_form()

    def _save_profile(self):
        name = self._name_entry.get().strip()
        if not name:
            self._error_label.configure(text="Please enter a name.")
            return

        is_edit = self._editing is not None
        if not is_edit and self._storage.profile_exists(name):
            self._error_label.configure(text=f"'{name}' already exists.")
            return
        if is_edit and name != self._editing.name and self._storage.profile_exists(name):
            self._error_label.configure(text=f"'{name}' already exists.")
            return

        try:
            work = int(self._work_var.get()) * 60
            brk = int(self._break_var.get()) * 60
            idle = int(self._idle_var.get())
        except ValueError:
            self._error_label.configure(text="All fields must be numbers.")
            return

        if is_edit:
            old_name = self._editing.name
            self._editing.avatar_color = self._selected_color.get()
            self._editing.default_work = work
            self._editing.default_break = brk
            self._editing.inactivity_timeout = idle
            if name != old_name:
                self._storage.delete_profile(old_name)
                self._editing.name = name
            self._storage.save_profile(self._editing)
        else:
            profile = Profile(name=name, avatar_color=self._selected_color.get(),
                              default_work=work, default_break=brk,
                              inactivity_timeout=idle)
            self._storage.save_profile(profile)

        self._creating = False
        self._editing = None
        self._build_form()
        self._load_profiles()

    # ── Profile grid ────────────────────────────────────────────────────────

    def _load_profiles(self):
        for w in self._grid_container.winfo_children():
            w.destroy()

        names = self._storage.list_profiles()
        if not names:
            ctk.CTkLabel(self._grid_container, text="No profiles yet. Create one below.",
                         font=FONTS["body"], text_color=COLORS["text_dim"],
                         fg_color="transparent").pack(pady=40)
            return

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

    def _make_card(self, parent, profile, index):
        row, col = divmod(index, 2)
        card = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=16,
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=20, pady=20)

        avatar = ctk.CTkFrame(inner, fg_color=profile.avatar_color,
                               width=52, height=52, corner_radius=26)
        avatar.pack(side="left", padx=(0, 16))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=profile.name[0].upper(),
                     font=("Georgia", 22, "bold"), text_color="white",
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(info, text=profile.name, font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent", anchor="w").pack(anchor="w")

        # Smart subtitle
        hours = profile.total_work_seconds() // 3600
        free_hours = profile.total_free_seconds() // 3600
        sessions = profile.total_sessions()
        if sessions == 0 and free_hours == 0:
            subtitle = "Ready to start"
            sub_color = COLORS["accent2"]
        else:
            subtitle = f"{hours + free_hours}h studied · {sessions} sessions"
            sub_color = COLORS["text_dim"]

        ctk.CTkLabel(info, text=subtitle, font=FONTS["small"],
                     text_color=sub_color, fg_color="transparent", anchor="w").pack(anchor="w", pady=(2, 0))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(btn_row, text="Select",
                      command=lambda p=profile: self._on_select(p),
                      fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                      corner_radius=8, height=28, width=70, font=FONTS["small"],
                      ).pack(pady=(0, 4))

        ctk.CTkButton(btn_row, text="Edit",
                      command=lambda p=profile: self._show_edit_form(p),
                      fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                      text_color=COLORS["text_dim"],
                      corner_radius=8, height=28, width=70, font=FONTS["small"],
                      ).pack(pady=(0, 4))

        ctk.CTkButton(btn_row, text="Delete",
                      command=lambda p=profile: self._confirm_delete(p),
                      fg_color="transparent", hover_color=COLORS["danger_dim"],
                      text_color=COLORS["danger"], border_color=COLORS["danger"],
                      border_width=1, corner_radius=8, height=28, width=70,
                      font=FONTS["small"]).pack()

    # ── Delete confirmation ──────────────────────────────────────────────────

    def _confirm_delete(self, profile):
        dlg = ctk.CTkToplevel(self)
        dlg.title("")
        dlg.geometry("340x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color=COLORS["surface"])
        dlg.attributes("-topmost", True)
        px = self.winfo_toplevel().winfo_x() + self.winfo_toplevel().winfo_width() // 2 - 170
        py = self.winfo_toplevel().winfo_y() + self.winfo_toplevel().winfo_height() // 2 - 90
        dlg.geometry(f"+{px}+{py}")

        ctk.CTkLabel(dlg, text="Delete profile?", font=FONTS["heading"],
                     text_color=COLORS["danger"], fg_color="transparent").pack(pady=(24, 6))
        ctk.CTkLabel(dlg,
                     text=f"'{profile.name}' and all its history\nwill be permanently deleted.",
                     font=FONTS["small"], text_color=COLORS["text_dim"],
                     fg_color="transparent", justify="center").pack()

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(pady=20)

        ctk.CTkButton(row, text="Cancel", command=dlg.destroy,
                      fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                      text_color=COLORS["text_dim"], corner_radius=8,
                      height=36, width=90).pack(side="left", padx=8)

        ctk.CTkButton(row, text="Delete",
                      command=lambda: (self._storage.delete_profile(profile.name),
                                       self._load_profiles(), dlg.destroy()),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_dim"],
                      corner_radius=8, height=36, width=90,
                      font=FONTS["body_bold"]).pack(side="left", padx=8)
        dlg.grab_set()
