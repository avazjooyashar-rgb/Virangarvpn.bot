# =========================
# MENU ACTION CACHE
# =========================

import time
from threading import Lock


DEFAULT_TTL = 60
MAX_CACHE_SIZE = 10000


class MenuActionCache:
    def __init__(self, ttl=DEFAULT_TTL):
        self.ttl = int(ttl)
        self._cache = {}
        self._lock = Lock()

    def _key(self, item_id):
        try:
            return int(item_id)
        except (TypeError, ValueError):
            return None

    def set(self, item_id, value):
        key = self._key(item_id)

        if key is None:
            return False

        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": time.monotonic() + self.ttl,
            }

            self._cleanup()

        return True

    def get(self, item_id):
        key = self._key(item_id)

        if key is None:
            return None

        with self._lock:
            entry = self._cache.get(key)

            if not entry:
                return None

            if time.monotonic() >= entry["expires_at"]:
                self._cache.pop(key, None)
                return None

            return entry["value"]

    def delete(self, item_id):
        key = self._key(item_id)

        if key is None:
            return False

        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self):
        with self._lock:
            self._cache.clear()

    def has(self, item_id):
        return self.get(item_id) is not None

    def size(self):
        with self._lock:
            self._cleanup()
            return len(self._cache)

    def _cleanup(self):
        now = time.monotonic()

        expired = [
            key
            for key, entry in self._cache.items()
            if now >= entry["expires_at"]
        ]

        for key in expired:
            self._cache.pop(key, None)

        if len(self._cache) > MAX_CACHE_SIZE:
            oldest = sorted(
                self._cache.items(),
                key=lambda item: item[1]["expires_at"],
            )

            remove_count = len(self._cache) - MAX_CACHE_SIZE

            for key, _ in oldest[:remove_count]:
                self._cache.pop(key, None)


menu_action_cache = MenuActionCache()


def cache_set(item_id, value):
    return menu_action_cache.set(item_id, value)


def cache_get(item_id):
    return menu_action_cache.get(item_id)


def cache_delete(item_id):
    return menu_action_cache.delete(item_id)


def cache_clear():
    menu_action_cache.clear()


def cache_has(item_id):
    return menu_action_cache.has(item_id)


def get_cache_size():
    return menu_action_cache.size()


def get_cache_status():
    return {
        "module": "menu_action_cache",
        "status": "ready",
        "ttl": DEFAULT_TTL,
        "thread_safe": True,
        "max_cache_size": MAX_CACHE_SIZE,
    }
