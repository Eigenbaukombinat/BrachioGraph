"""ESPpio: a tiny pigpio-compatible shim that forwards servo commands over
USB-CDC to an ESP32-S3 running the firmware in ``esppio-fw/``.

It implements only the subset of the ``pigpio`` API that BrachioGraph
actually uses:

* ``esppio.pi()`` -> a connection object
* ``pi.set_servo_pulsewidth(pin, us)``
* ``pi.set_PWM_frequency(pin, hz)``  (accepted, fixed at 50 Hz on device)
* ``pi.get_servo_pulsewidth(pin)``
* ``pi.stop()``
* module-level ``exceptions`` flag (accepted, ignored)

Usage in BrachioGraph forks:

    import esppio as pigpio          # drop-in replacement
    rpi = pigpio.pi()
    rpi.set_servo_pulsewidth(14, 1500)

Port selection (in order of precedence):

1. ``ESPPIO_PORT`` environment variable (e.g. ``/dev/cu.usbmodem14101``).
2. Auto-detection by USB VID/PID (Espressif: 0x303A).
3. First port whose description contains "USB JTAG" or "USB Serial".

If no device can be opened, ``pi()`` still returns an object, but its
methods raise ``AttributeError`` -- matching the behaviour the existing
BrachioGraph code expects when ``pigpiod`` is unavailable, so it falls
back to virtual mode automatically.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "esppio requires pyserial. Install it with: pip install pyserial"
    ) from exc


# Module-level flag accepted for pigpio compatibility. Ignored.
exceptions = True

# Espressif USB VID; covers ESP32-S2/S3/C3 native USB-CDC devices.
_ESPRESSIF_VID = 0x303A

_BAUDRATE = 921600  # ignored over native USB-CDC, used only for UART bridges
_READ_TIMEOUT = 0.2


def _autodetect_port() -> Optional[str]:
    candidates = list(list_ports.comports())

    # 1. exact VID match (Espressif native USB)
    for p in candidates:
        if p.vid == _ESPRESSIF_VID:
            return p.device

    # 2. heuristic: description hints at a USB-serial bridge
    for p in candidates:
        desc = (p.description or "").lower()
        if "usb jtag" in desc or "JTAG" in desc or "usb serial" in desc or "usbmodem" in desc:
            return p.device

    return None


class _Pi:
    """Connection to an ESPpio-equipped ESP32. Mirrors the parts of
    ``pigpio.pi`` that BrachioGraph uses."""

    def __init__(self, port: Optional[str] = None):
        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self.connected = False

        port = port or os.environ.get("ESPPIO_PORT") or _autodetect_port()
        if not port:
            return

        try:
            ser = serial.Serial()
            ser.port = port
            ser.baudrate = _BAUDRATE
            ser.timeout = _READ_TIMEOUT
            # Avoid resetting the ESP32 when opening the port.
            ser.dtr = False
            ser.rts = False
            ser.open()
        except (serial.SerialException, OSError):
            return

        self._serial = ser
        self._port = port
        self.connected = True

        # Drain any boot-time chatter (ROM bootloader banner) so that the
        # first G query doesn't get a stale line back. We don't wait for it
        # actively (would add ~1s latency); instead we just flush whatever
        # is buffered now plus a short follow-up read.
        try:
            import time as _time
            _time.sleep(0.05)
            while ser.in_waiting:
                ser.read(ser.in_waiting)
                _time.sleep(0.05)
            # Probe: send V; if reply is not "ESPPIO ...", keep draining.
            for _ in range(20):  # up to ~2s
                ser.reset_input_buffer()
                ser.write(b"V\n")
                line = ser.readline().decode("ascii", errors="replace").strip()
                if line.startswith("ESPPIO"):
                    break
                _time.sleep(0.1)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # internal I/O
    # ------------------------------------------------------------------

    def _write(self, line: str) -> None:
        # AttributeError on missing serial mirrors pigpio's behaviour when
        # the daemon is unreachable, which BrachioGraph already handles by
        # falling back to virtual mode.
        with self._lock:
            self._serial.write(line.encode("ascii"))  # type: ignore[union-attr]

    def _query(self, line: str) -> str:
        with self._lock:
            self._serial.reset_input_buffer()  # type: ignore[union-attr]
            self._serial.write(line.encode("ascii"))  # type: ignore[union-attr]
            reply = self._serial.readline()  # type: ignore[union-attr]
        return reply.decode("ascii", errors="replace").strip()

    # ------------------------------------------------------------------
    # pigpio-compatible API
    # ------------------------------------------------------------------

    def set_servo_pulsewidth(self, pin: int, pulsewidth: float) -> None:
        self._write(f"S {int(pin)} {int(pulsewidth)}\n")

    def set_PWM_frequency(self, pin: int, frequency: int) -> int:
        # Firmware fixes the frequency at 50 Hz; accept and acknowledge.
        self._write(f"F {int(pin)} {int(frequency)}\n")
        return int(frequency)

    def get_servo_pulsewidth(self, pin: int) -> int:
        reply = self._query(f"G {int(pin)}\n")
        try:
            return int(reply)
        except ValueError:
            return 0

    def stop(self) -> None:
        if self._serial is not None:
            try:
                # Detach all known servos defensively before closing.
                for pin in (14, 15, 18):
                    self._write(f"S {pin} 0\n")
            except Exception:
                pass
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
            self.connected = False
        # Drop from connection cache so a fresh pi() reopens cleanly.
        try:
            with _connections_lock:
                port = getattr(self, "_port", None)
                if port and _connections.get(port) is self:
                    del _connections[port]
        except Exception:
            pass


# Cache of open connections keyed by resolved port path, so multiple
# pigpio.pi() calls from different subsystems (Plotter, Pen, ...) share
# one underlying serial connection and lock.
_connections: dict = {}
_connections_lock = threading.Lock()


def pi(port: Optional[str] = None) -> _Pi:
    """Return a connection object. Mirrors ``pigpio.pi``.

    Connections are cached per resolved port; repeated calls return the
    same ``_Pi`` instance so callers safely share the serial port.
    """
    resolved = port or os.environ.get("ESPPIO_PORT") or _autodetect_port()
    with _connections_lock:
        cached = _connections.get(resolved)
        if cached is not None and cached.connected:
            return cached
        instance = _Pi(port=resolved)
        if instance.connected and resolved is not None:
            _connections[resolved] = instance
        return instance
