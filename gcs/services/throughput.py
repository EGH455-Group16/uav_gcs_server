# gcs/services/throughput.py
from collections import deque
from threading import RLock
from time import time

class ThroughputMeter:
    """Rolling average throughput calculator in kb/s."""
    def __init__(self, window_sec: float = 4.0):
        self.window = window_sec
        self._lock = RLock()
        self._streams = {"AQSA": deque(), "TAIP": deque()}  # (ts, bytes)

    def add(self, stream: str, nbytes: int):
        if stream not in self._streams or nbytes is None:
            return
        now = time()
        with self._lock:
            q = self._streams[stream]
            q.append((now, nbytes))
            cutoff = now - self.window
            while q and q[0][0] < cutoff:
                q.popleft()

    def kbps(self, stream: str) -> float:
        now = time()
        with self._lock:
            q = self._streams[stream]
            cutoff = now - self.window
            total_bytes = sum(b for t, b in q if t >= cutoff)
        return round((total_bytes / self.window) * 8 / 1000, 2)  # kb/s

    def snapshot(self) -> dict:
        return {
            "window_sec": self.window,
            "aqsa_kbps": self.kbps("AQSA"),
            "taip_kbps": self.kbps("TAIP"),
            "ts": time(),
        }
