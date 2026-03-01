import customtkinter as ctk
from config import COLORS, FONTS
from models.schedule import Block, Schedule


class ScheduleBuilder(ctk.CTkFrame):
    """Widget that lets users build a list of work/break blocks before starting."""

    def __init__(self, parent, default_work: int, default_break: int, on_start):
        super().__init__(parent, fg_color=COLORS["surface"], corner_radius=16)
        self._default_work = default_work // 60
        self._default_break = default_break // 60
        self._on_start = on_start
        self._blocks = []
        self._build()
        self._add_block("work")
        self._add_block("break")
        self._add_block("work")

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(header, text="Build your session", font=FONTS["heading"],
                     text_color=COLORS["text"], fg_color="transparent").pack(side="left")

        add_row = ctk.CTkFrame(header, fg_color="transparent")
        add_row.pack(side="right")

        ctk.CTkButton(add_row, text="+ Work", width=70, height=26,
                      fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
                      corner_radius=8, font=FONTS["small"],
                      command=lambda: self._add_block("work"),
                      ).pack(side="left", padx=3)

        ctk.CTkButton(add_row, text="+ Break", width=70, height=26,
                      fg_color=COLORS["break_dim"], hover_color=COLORS["break"],
                      text_color=COLORS["text"], corner_radius=8, font=FONTS["small"],
                      command=lambda: self._add_block("break"),
                      ).pack(side="left")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).pack(fill="x", padx=14)

        # Scrollable list — does NOT expand, rows pack to top naturally
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dim"],
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=4)

        footer = ctk.CTkFrame(self, fg_color=COLORS["surface2"], corner_radius=10)
        footer.pack(fill="x", padx=14, pady=(2, 12))

        inner = ctk.CTkFrame(footer, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        self._summary_label = ctk.CTkLabel(inner, text="", font=FONTS["small"],
                                            text_color=COLORS["text_dim"], fg_color="transparent")
        self._summary_label.pack(side="left")

        self._start_btn = ctk.CTkButton(inner, text="Start Session →",
                                         command=self._start,
                                         fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                                         corner_radius=8, height=34, font=FONTS["body_bold"])
        self._start_btn.pack(side="right")
        self._update_summary()

    def _add_block(self, block_type: str):
        default_dur = self._default_work if block_type == "work" else self._default_break
        color = COLORS["work"] if block_type == "work" else COLORS["break"]

        row = ctk.CTkFrame(self._list_frame, fg_color=COLORS["surface2"], corner_radius=8)
        row.pack(fill="x", padx=2, pady=2, anchor="n")

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=5)

        ctk.CTkFrame(inner, fg_color=color, width=3, corner_radius=2).pack(
            side="left", fill="y", padx=(0, 8))

        type_var = ctk.StringVar(value=block_type)
        ctk.CTkLabel(inner, text="WORK" if block_type == "work" else "BREAK",
                     font=("Helvetica Neue", 10, "bold"), text_color=color,
                     fg_color="transparent", width=42).pack(side="left")

        dur_var = ctk.StringVar(value=str(default_dur))
        ctk.CTkEntry(inner, textvariable=dur_var, width=52, height=28,
                     fg_color=COLORS["surface"], border_color=COLORS["border"],
                     text_color=COLORS["text"], corner_radius=6).pack(side="left", padx=6)
        dur_var.trace_add("write", lambda *_: self._update_summary())

        ctk.CTkLabel(inner, text="min", font=FONTS["small"],
                     text_color=COLORS["text_dim"], fg_color="transparent").pack(side="left")

        ctk.CTkButton(inner, text="✕", width=24, height=24,
                      fg_color="transparent", hover_color=COLORS["danger_dim"],
                      text_color=COLORS["text_dim"], corner_radius=6,
                      command=lambda r=row: self._remove_block(r),
                      ).pack(side="right")

        self._blocks.append((type_var, dur_var, row, color))
        self._update_summary()

    def _remove_block(self, frame):
        self._blocks = [b for b in self._blocks if b[2] is not frame]
        frame.destroy()
        self._update_summary()

    def _update_summary(self):
        work_mins = break_mins = 0
        for type_var, dur_var, _, _ in self._blocks:
            try:
                val = int(dur_var.get())
            except ValueError:
                val = 0
            if type_var.get() == "work":
                work_mins += val
            else:
                break_mins += val
        total = work_mins + break_mins
        self._summary_label.configure(
            text=f"{len(self._blocks)} blocks · {work_mins}m work · {break_mins}m break · {total}m total")

    def _start(self):
        blocks = []
        for type_var, dur_var, _, _ in self._blocks:
            try:
                mins = int(dur_var.get())
                if mins <= 0:
                    continue
            except ValueError:
                continue
            blocks.append(Block(type=type_var.get(), duration=mins * 60))
        if not blocks:
            return
        self._on_start(Schedule(blocks=blocks))
