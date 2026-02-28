from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    profile_name: str
    block_type: str
    planned_duration: int
    actual_duration: int
    date: str
    completed: bool

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "block_type": self.block_type,
            "planned_duration": self.planned_duration,
            "actual_duration": self.actual_duration,
            "date": self.date,
            "completed": self.completed,
        }

    @classmethod
    def create(cls, profile_name: str, block_type: str, planned: int, actual: int, completed: bool) -> "Session":
        return cls(
            profile_name=profile_name,
            block_type=block_type,
            planned_duration=planned,
            actual_duration=actual,
            date=datetime.now().isoformat(),
            completed=completed,
        )
