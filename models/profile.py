from dataclasses import dataclass, field
from datetime import datetime
from config import DEFAULT_WORK_DURATION, DEFAULT_BREAK_DURATION


@dataclass
class Profile:
    name: str
    avatar_color: str = "#7c6af7"
    default_work: int = DEFAULT_WORK_DURATION
    default_break: int = DEFAULT_BREAK_DURATION
    sessions: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def total_work_seconds(self) -> int:
        return sum(
            s.get("actual_duration", 0)
            for s in self.sessions
            if s.get("block_type") == "work" and s.get("completed")
        )

    def total_sessions(self) -> int:
        return sum(1 for s in self.sessions if s.get("completed"))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "avatar_color": self.avatar_color,
            "default_work": self.default_work,
            "default_break": self.default_break,
            "sessions": self.sessions,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            avatar_color=data.get("avatar_color", "#7c6af7"),
            default_work=data.get("default_work", DEFAULT_WORK_DURATION),
            default_break=data.get("default_break", DEFAULT_BREAK_DURATION),
            sessions=data.get("sessions", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
