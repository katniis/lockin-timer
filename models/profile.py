from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from config import DEFAULT_WORK_DURATION, DEFAULT_BREAK_DURATION


@dataclass
class Profile:
    name: str
    avatar_color: str = "#7c6af7"
    default_work: int = DEFAULT_WORK_DURATION
    default_break: int = DEFAULT_BREAK_DURATION
    sessions: list = field(default_factory=list)
    free_sessions: list = field(default_factory=list)
    daily_goal: int = 2 * 3600       # seconds (default 2h)
    weekly_goal: int = 10 * 3600     # seconds (default 10h)
    inactivity_timeout: int = 60     # seconds before idle alert
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── Scheduled mode helpers ──────────────────────────────────────────────

    def total_work_seconds(self) -> int:
        return sum(
            s.get("actual_duration", 0)
            for s in self.sessions
            if s.get("block_type") == "work" and s.get("completed")
        )

    def total_sessions(self) -> int:
        return sum(1 for s in self.sessions if s.get("completed") and s.get("block_type") == "work")

    def work_seconds_on(self, day: date) -> int:
        total = 0
        for s in self.sessions:
            if not s.get("completed") or s.get("block_type") != "work":
                continue
            try:
                d = datetime.fromisoformat(s["date"]).date()
                if d == day:
                    total += s.get("actual_duration", 0)
            except Exception:
                pass
        return total

    def work_seconds_in_week(self, week_start: date) -> int:
        total = 0
        for i in range(7):
            total += self.work_seconds_on(week_start + timedelta(days=i))
        return total

    # ── Free mode helpers ───────────────────────────────────────────────────

    def total_free_seconds(self) -> int:
        return sum(s.get("duration", 0) for s in self.free_sessions)

    def free_seconds_on(self, day: date) -> int:
        total = 0
        for s in self.free_sessions:
            try:
                d = datetime.fromisoformat(s["date"]).date()
                if d == day:
                    total += s.get("duration", 0)
            except Exception:
                pass
        return total

    def free_seconds_in_week(self, week_start: date) -> int:
        return sum(self.free_seconds_on(week_start + timedelta(days=i)) for i in range(7))

    # ── Combined helpers ────────────────────────────────────────────────────

    def streak_days(self) -> int:
        """Consecutive days with at least 1 completed work/free session ending today."""
        today = date.today()
        streak = 0
        for i in range(365):
            day = today - timedelta(days=i)
            if self.work_seconds_on(day) > 0 or self.free_seconds_on(day) > 0:
                streak += 1
            else:
                break
        return streak

    # ── Serialization ───────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "avatar_color": self.avatar_color,
            "default_work": self.default_work,
            "default_break": self.default_break,
            "sessions": self.sessions,
            "free_sessions": self.free_sessions,
            "daily_goal": self.daily_goal,
            "weekly_goal": self.weekly_goal,
            "inactivity_timeout": self.inactivity_timeout,
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
            free_sessions=data.get("free_sessions", []),
            daily_goal=data.get("daily_goal", 2 * 3600),
            weekly_goal=data.get("weekly_goal", 10 * 3600),
            inactivity_timeout=data.get("inactivity_timeout", 60),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
