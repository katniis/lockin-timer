from typing import Callable


class TimerService:
    """Pure logic timer — no UI dependencies. Driven by external tick() calls."""

    def __init__(self, on_tick: Callable[[int], None], on_finish: Callable):
        self._on_tick = on_tick
        self._on_finish = on_finish
        self._remaining = 0
        self._planned = 0
        self._running = False
        self._elapsed = 0

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def planned(self) -> int:
        return self._planned

    @property
    def elapsed(self) -> int:
        return self._elapsed

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, duration: int):
        self._planned = duration
        self._remaining = duration
        self._elapsed = 0
        self._running = True

    def pause(self):
        self._running = False

    def resume(self):
        self._running = True

    def stop(self):
        self._running = False
        self._remaining = 0

    def tick(self):
        """Called every second by the UI's after() loop."""
        if not self._running or self._remaining <= 0:
            return
        self._remaining -= 1
        self._elapsed += 1
        self._on_tick(self._remaining)
        if self._remaining <= 0:
            self._running = False
            self._on_finish()

    def progress(self) -> float:
        """Returns 0.0 → 1.0"""
        if self._planned == 0:
            return 0.0
        return 1.0 - (self._remaining / self._planned)
