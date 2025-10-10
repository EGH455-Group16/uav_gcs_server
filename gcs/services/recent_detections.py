from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from time import time
from collections import deque

@dataclass
class DetectionItem:
    ts: float          # epoch seconds (server)
    type: str
    details: dict
    image_url: str     # /static/targets/archive/...
    thumb_url: str     # same for now (can be real thumb later)

class RecentDetections:
    def __init__(self, window_sec: int = 3600, max_items: int = 200, min_conf: float = 0.75, refresh_sec: float = 4.0):
        self.window_sec = window_sec
        self.max_items = max_items
        self.min_conf = min_conf
        self.refresh_sec = refresh_sec
        self.items: deque[DetectionItem] = deque()
        self._last: Optional[DetectionItem] = None
        self._last_emit_ts: float = 0.0

    def _same_object(self, a: dict, b: dict, t: str) -> bool:
        try:
            if t == "valve":
                return a.get("state") == b.get("state")
            if t == "gauge":
                ra, rb = float(a.get("reading_bar", -1)), float(b.get("reading_bar", -2))
                return abs(ra - rb) <= 0.1
            if t == "aruco":
                return int(a.get("id", -1)) == int(b.get("id", -2))
        except Exception:
            pass
        return False

    def consider(self, t: str, details: dict, image_url: str, server_ts: float) -> Optional[DetectionItem]:
        # Filter out "livedata" type (not a real detection)
        if t == "livedata":
            return None
        
        conf = float(details.get("confidence", 0.0))
        if conf < self.min_conf:
            return None

        item = DetectionItem(ts=server_ts, type=t, details=details, image_url=image_url, thumb_url=image_url)
        now = server_ts

        # Evict old
        cutoff = now - self.window_sec
        while self.items and self.items[0].ts < cutoff:
            self.items.popleft()

        # Decide whether to append or refresh last
        if self._last and self._same_object(self._last.details, details, t) and (now - self._last_emit_ts) < self.refresh_sec:
            # Same object and refresh window not elapsed => keep showing previous
            return None

        # New object OR refresh window elapsed -> append
        self.items.append(item)
        while len(self.items) > self.max_items:
            self.items.popleft()

        self._last = item
        self._last_emit_ts = now
        return item

    def list(self, limit: int = 40) -> list[dict]:
        return [
            {
                "ts": it.ts,
                "type": it.type,
                "details": it.details,
                "image_url": it.image_url,
                "thumb_url": it.thumb_url
            } for it in list(self.items)[:limit]
        ]

    def clear(self):
        """Clear all stored detections"""
        self.items.clear()
        self._last = None
        self._last_emit_ts = 0.0
