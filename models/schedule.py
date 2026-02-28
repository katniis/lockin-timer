from dataclasses import dataclass, field


@dataclass
class Block:
    type: str       # "work" or "break"
    duration: int   # seconds
    label: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type, "duration": self.duration, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        return cls(type=data["type"], duration=data["duration"], label=data.get("label", ""))


@dataclass
class Schedule:
    blocks: list = field(default_factory=list)
    current_index: int = 0

    def current_block(self) -> Block | None:
        if self.current_index < len(self.blocks):
            return self.blocks[self.current_index]
        return None

    def advance(self) -> bool:
        """Move to next block. Returns True if there is a next block."""
        self.current_index += 1
        return self.current_index < len(self.blocks)

    def is_done(self) -> bool:
        return self.current_index >= len(self.blocks)

    def reset(self):
        self.current_index = 0

    def total_duration(self) -> int:
        return sum(b.duration for b in self.blocks)

    def total_work(self) -> int:
        return sum(b.duration for b in self.blocks if b.type == "work")

    def total_break(self) -> int:
        return sum(b.duration for b in self.blocks if b.type == "break")
