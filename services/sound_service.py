"""
SoundService — procedural lo-fi warm sounds, no external audio files.
Sounds are ~5 seconds long, loud enough to cut through background music,
with rich harmonics and overdrive for presence.
"""

import threading
import numpy as np

try:
    import sounddevice as sd
    _AVAILABLE = True
except Exception:
    _AVAILABLE = False

SAMPLE_RATE = 44100
MASTER_VOLUME = 0.3  # loud enough to punch through music


# ---------------------------------------------------------------------------
# DSP helpers
# ---------------------------------------------------------------------------

def _sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _triangle(freq, duration, sr=SAMPLE_RATE):
    """Triangle wave — more harmonics than sine, cuts through better."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1


def _envelope(wave, attack=0.01, decay=0.08, sustain=0.75, release=0.4):
    n = len(wave)
    a = int(SAMPLE_RATE * attack)
    d = int(SAMPLE_RATE * decay)
    r = int(SAMPLE_RATE * release)
    s = max(0, n - a - d - r)
    env = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sustain, d),
        np.full(s, sustain),
        np.linspace(sustain, 0, r),
    ])
    return wave * env[:n]


def _low_pass(wave, cutoff=1400, sr=SAMPLE_RATE):
    """Single-pole IIR low-pass — lo-fi warmth without killing presence."""
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / sr
    alpha = dt / (rc + dt)
    out = np.zeros_like(wave)
    prev = 0.0
    for i, x in enumerate(wave):
        prev += alpha * (x - prev)
        out[i] = prev
    return out


def _overdrive(wave, amount=0.45):
    """Soft-clip overdrive — adds odd harmonics, makes sound punchier."""
    return np.tanh(wave * (1 + amount * 4)) / np.tanh(1 + amount * 4)


def _add_harmonics(freq, duration, weights):
    """Build a rich tone from multiple harmonics."""
    wave = np.zeros(int(SAMPLE_RATE * duration))
    for harmonic, weight in enumerate(weights, start=1):
        wave += weight * _sine(freq * harmonic, duration)
    return wave


def _reverb(wave, decay=0.35, delay_ms=38):
    """Simple comb-filter reverb for warmth and space."""
    delay_samples = int(SAMPLE_RATE * delay_ms / 1000)
    out = wave.copy()
    for i in range(delay_samples, len(out)):
        out[i] += out[i - delay_samples] * decay
    return out


def _normalize(wave, target=MASTER_VOLUME):
    peak = np.max(np.abs(wave))
    if peak > 0:
        wave = wave / peak * target
    return wave.astype(np.float32)


def _place(total_samples, wave, offset_sec):
    """Place a wave into a buffer at a given time offset."""
    buf = np.zeros(total_samples)
    start = int(SAMPLE_RATE * offset_sec)
    end = min(start + len(wave), total_samples)
    buf[start:end] = wave[:end - start]
    return buf


def _play(wave):
    if not _AVAILABLE:
        return
    wave = _normalize(wave)
    stereo = np.column_stack([wave, wave])
    try:
        sd.play(stereo, samplerate=SAMPLE_RATE, blocking=False)
    except Exception:
        pass


def _play_async(wave):
    threading.Thread(target=_play, args=(wave,), daemon=True).start()


# ---------------------------------------------------------------------------
# Sound generators — all ~5 seconds
# ---------------------------------------------------------------------------

def _make_session_start():
    """
    'Focus mode' — three ascending notes, rich harmonics, bold attack.
    E4 → B4 → E5, each held with a warm sustained tail.
    Total ~5s.
    """
    total = int(SAMPLE_RATE * 5.0)
    wave = np.zeros(total)

    notes = [
        (329.6, 0.0,  1.8),   # E4
        (493.9, 0.9,  1.8),   # B4
        (659.3, 1.8,  3.0),   # E5 — held longest
    ]

    for freq, offset, dur in notes:
        # Rich harmonic stack: fundamental + octave + fifth
        tone = _add_harmonics(freq, dur, [1.0, 0.35, 0.2, 0.08])
        tone = _envelope(tone, attack=0.02, decay=0.1, sustain=0.72, release=0.55)
        # Detune layer for lo-fi
        tone_d = _add_harmonics(freq * 0.997, dur, [0.5, 0.18, 0.1])
        tone_d = _envelope(tone_d, attack=0.025, decay=0.12, sustain=0.65, release=0.55)
        combined = tone + tone_d
        combined = _overdrive(combined, 0.3)
        wave += _place(total, combined, offset)

    wave = _reverb(wave, decay=0.3, delay_ms=40)
    wave = _low_pass(wave, cutoff=1600)
    return wave


def _make_break_start():
    """
    'Exhale' — descending soft chord, warm and wide.
    G4 → D4 → G3, slower and more spaced out. Total ~5s.
    """
    total = int(SAMPLE_RATE * 5.0)
    wave = np.zeros(total)

    notes = [
        (392.0, 0.0,  1.6),   # G4
        (293.7, 0.85, 1.6),   # D4
        (196.0, 1.8,  3.0),   # G3 — deep, held long
    ]

    for freq, offset, dur in notes:
        tone = _add_harmonics(freq, dur, [1.0, 0.4, 0.15, 0.05])
        tone = _envelope(tone, attack=0.04, decay=0.15, sustain=0.68, release=0.7)
        tone_d = _add_harmonics(freq * 1.003, dur, [0.45, 0.2])
        tone_d = _envelope(tone_d, attack=0.05, decay=0.15, sustain=0.6, release=0.7)
        combined = tone + tone_d
        combined = _overdrive(combined, 0.2)
        wave += _place(total, combined, offset)

    wave = _reverb(wave, decay=0.4, delay_ms=52)
    wave = _low_pass(wave, cutoff=1200)
    return wave


def _make_completion():
    """
    'Victory' — full C major arpeggio that blooms into a held chord.
    C4 → E4 → G4 → C5, then all ring together. ~5s total.
    """
    total = int(SAMPLE_RATE * 5.2)
    wave = np.zeros(total)

    # Arpeggio up
    arp = [
        (261.6, 0.0,  1.0),   # C4
        (329.6, 0.3,  1.2),   # E4
        (392.0, 0.6,  1.4),   # G4
        (523.3, 0.95, 3.8),   # C5 — long ring-out
    ]
    for freq, offset, dur in arp:
        tone = _add_harmonics(freq, dur, [1.0, 0.45, 0.22, 0.1, 0.04])
        tone = _envelope(tone, attack=0.015, decay=0.1, sustain=0.78, release=0.65)
        tone_d = _add_harmonics(freq * 0.998, dur, [0.5, 0.2, 0.1])
        tone_d = _envelope(tone_d, attack=0.02, decay=0.1, sustain=0.7, release=0.65)
        combined = _overdrive(tone + tone_d, 0.35)
        wave += _place(total, combined, offset)

    # Swell chord at the end — all notes together
    chord_freqs = [261.6, 329.6, 392.0, 523.3]
    for freq in chord_freqs:
        swell = _add_harmonics(freq, 2.2, [0.6, 0.25, 0.1])
        swell = _envelope(swell, attack=0.25, decay=0.2, sustain=0.6, release=0.9)
        wave += _place(total, swell, 2.8)

    wave = _reverb(wave, decay=0.45, delay_ms=35)
    wave = _low_pass(wave, cutoff=1800)
    return wave


def _make_inactivity():
    """
    'Hey!' — three urgent descending pings, enough to pierce through music.
    Bright and sharp with overdrive. ~4s total.
    """
    total = int(SAMPLE_RATE * 4.0)
    wave = np.zeros(total)

    pings = [
        (880, 0.0,  0.7),
        (740, 0.55, 0.7),
        (880, 1.1,  1.5),   # repeat high note — extra attention-grab
    ]

    for freq, offset, dur in pings:
        tone = _add_harmonics(freq, dur, [1.0, 0.5, 0.3, 0.12])
        tone = _envelope(tone, attack=0.005, decay=0.06, sustain=0.6, release=0.35)
        tone = _overdrive(tone, 0.5)
        wave += _place(total, tone, offset)

    wave = _reverb(wave, decay=0.25, delay_ms=28)
    wave = _low_pass(wave, cutoff=2200)
    return wave


# ---------------------------------------------------------------------------
# Public service class
# ---------------------------------------------------------------------------

class SoundService:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and _AVAILABLE
        if self.enabled:
            self._sounds = {
                "session_start": _make_session_start(),
                "break_start":   _make_break_start(),
                "completion":    _make_completion(),
                "inactivity":    _make_inactivity(),
            }
        else:
            self._sounds = {}

    def play_session_start(self):
        self._play("session_start")

    def play_break_start(self):
        self._play("break_start")

    def play_completion(self):
        self._play("completion")

    def play_inactivity(self):
        self._play("inactivity")

    def _play(self, name: str):
        if not self.enabled:
            return
        wave = self._sounds.get(name)
        if wave is not None:
            _play_async(wave)

    @property
    def available(self) -> bool:
        return _AVAILABLE