import time
import threading
from typing import Callable


class ActivityService:
    """Monitors mouse/keyboard activity and fires on_inactive when idle too long."""

    def __init__(self, timeout: int, on_inactive: Callable):
        self._timeout = timeout
        self._on_inactive = on_inactive
        self._last_active = time.time()
        self._alerted = False
        self._running = False
        self._thread = None
        self._listeners = []

    def start(self):
        self._running = True
        self._last_active = time.time()
        self._alerted = False
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        self._start_listeners()

    def stop(self):
        self._running = False
        self._stop_listeners()

    def reset(self):
        """Call when user dismisses the alert or resumes."""
        self._last_active = time.time()
        self._alerted = False

    def _reset_from_input(self, *args, **kwargs):
        self._last_active = time.time()
        if self._alerted:
            self._alerted = False

    def _check_loop(self):
        while self._running:
            idle = time.time() - self._last_active
            if idle >= self._timeout and not self._alerted:
                self._alerted = True
                self._on_inactive()
            time.sleep(5)

    def _start_listeners(self):
        try:
            from pynput import mouse, keyboard

            m_listener = mouse.Listener(
                on_move=self._reset_from_input,
                on_click=self._reset_from_input,
                on_scroll=self._reset_from_input,
            )
            k_listener = keyboard.Listener(on_press=self._reset_from_input)
            m_listener.start()
            k_listener.start()
            self._listeners = [m_listener, k_listener]
        except ImportError:
            # pynput not available — degrade gracefully
            pass

    def _stop_listeners(self):
        for listener in self._listeners:
            try:
                listener.stop()
            except Exception:
                pass
        self._listeners = []
