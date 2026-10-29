"""In-memory TTL store. No DB: everything is lost on restart/spin-down."""
import threading, time

class TTLStore:
    def __init__(self, ttl=6 * 3600):
        self.ttl, self._d, self._lock = ttl, {}, threading.Lock()

    def set(self, k, v):
        with self._lock:
            self._d[k] = (time.time() + self.ttl, v)
            now = time.time()
            for key in [x for x, (e, _) in self._d.items() if e < now]:
                del self._d[key]

    def get(self, k):
        with self._lock:
            item = self._d.get(k)
            return item[1] if item and item[0] > time.time() else None

store = TTLStore()
suppressed = set()  # unsubscribed emails (also in-memory; see README)
