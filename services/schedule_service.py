from typing import Callable
from models.schedule import Schedule, Block
from models.session import Session
from services.timer_service import TimerService


class ScheduleService:
    def __init__(
        self,
        schedule: Schedule,
        timer: TimerService,
        profile_name: str,
        on_block_change: Callable[[Block], None],
        on_complete: Callable[[list], None],
        on_session_done: Callable[[dict], None],
    ):
        self._schedule = schedule
        self._timer = timer
        self._profile_name = profile_name
        self._on_block_change = on_block_change
        self._on_complete = on_complete
        self._on_session_done = on_session_done
        self._completed_sessions = []

        # Wire timer's on_finish to our handler
        self._timer._on_finish = self._handle_block_finish

    def start(self):
        self._schedule.reset()
        self._completed_sessions = []
        block = self._schedule.current_block()
        if block:
            self._timer.start(block.duration)
            self._on_block_change(block)

    def skip_current(self):
        """Skip the current block without saving it as completed."""
        block = self._schedule.current_block()
        if block:
            self._save_session(block, completed=False)
        self._advance()

    def _handle_block_finish(self):
        block = self._schedule.current_block()
        if block:
            self._save_session(block, completed=True)
        self._advance()

    def _save_session(self, block: Block, completed: bool):
        session = Session.create(
            profile_name=self._profile_name,
            block_type=block.type,
            planned=block.duration,
            actual=self._timer.elapsed,
            completed=completed,
        )
        d = session.to_dict()
        self._completed_sessions.append(d)
        self._on_session_done(d)

    def _advance(self):
        has_next = self._schedule.advance()
        if has_next:
            block = self._schedule.current_block()
            self._timer.start(block.duration)
            self._on_block_change(block)
        else:
            self._on_complete(self._completed_sessions)

    @property
    def schedule(self) -> Schedule:
        return self._schedule
