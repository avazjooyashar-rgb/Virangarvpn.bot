# =========================
# MENU ACTION RATE LIMITER
# =========================

import time
from threading import Lock


DEFAULT_COOLDOWN = 0.8
MAX_TRACKED_USERS = 10000


class MenuActionRateLimiter:
    def __init__(self, cooldown=DEFAULT_COOLDOWN):
        self.cooldown = float(cooldown)
        self._last_action = {}
        self._lock = Lock()

    def is_allowed(self, user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return False

        now = time.monotonic()

        with self._lock:
            last_time = self._last_action.get(user_id)

            if last_time is not None:
                if now - last_time < self.cooldown:
                    return False

            self._last_action[user_id] = now

            if len(self._last_action) > MAX_TRACKED_USERS:
                self._cleanup(now)

            return True

    def remaining(self, user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return self.cooldown

        now = time.monotonic()

        with self._lock:
            last_time = self._last_action.get(user_id)

        if last_time is None:
            return 0.0

        remaining = self.cooldown - (now - last_time)

        return round(max(0.0, remaining), 3)

    def reset(self, user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return False

        with self._lock:
            self._last_action.pop(user_id, None)

        return True

    def clear(self):
        with self._lock:
            self._last_action.clear()

    def _cleanup(self, now):
        expired = [
            user_id
            for user_id, last_time in self._last_action.items()
            if now - last_time >= self.cooldown
        ]

        for user_id in expired:
            self._last_action.pop(user_id, None)

        if len(self._last_action) > MAX_TRACKED_USERS:
            oldest = sorted(
                self._last_action.items(),
                key=lambda item: item[1],
            )

            remove_count = len(self._last_action) - MAX_TRACKED_USERS

            for user_id, _ in oldest[:remove_count]:
                self._last_action.pop(user_id, None)


menu_action_rate_limiter = MenuActionRateLimiter()


def is_action_allowed(user_id):
    return menu_action_rate_limiter.is_allowed(user_id)


def get_remaining_cooldown(user_id):
    return menu_action_rate_limiter.remaining(user_id)


def reset_user_limit(user_id):
    return menu_action_rate_limiter.reset(user_id)


def reset_all_limits():
    menu_action_rate_limiter.clear()


def get_rate_limiter_status():
    return {
        "module": "menu_action_rate_limiter",
        "status": "ready",
        "cooldown": DEFAULT_COOLDOWN,
        "thread_safe": True,
        "max_tracked_users": MAX_TRACKED_USERS,
    }
