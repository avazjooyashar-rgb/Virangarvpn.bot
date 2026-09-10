# =========================
# MENU ACTION HISTORY
# =========================

from menu_action_logger import (
    get_menu_action_logs,
    count_menu_action_logs,
)


DEFAULT_LIMIT = 50
MAX_LIMIT = 500


def _safe_limit(limit):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT

    return max(1, min(limit, MAX_LIMIT))


def get_user_history(user_id, limit=DEFAULT_LIMIT):
    return get_menu_action_logs(
        limit=_safe_limit(limit),
        user_id=user_id,
    )


def get_item_history(item_id, limit=DEFAULT_LIMIT):
    return get_menu_action_logs(
        limit=_safe_limit(limit),
        item_id=item_id,
    )


def get_user_action_count(user_id):
    return count_menu_action_logs(user_id=user_id)


def get_item_action_count(item_id):
    return count_menu_action_logs(item_id=item_id)


def format_history_item(item):
    status = "✅ موفق" if int(item.get("success", 0)) == 1 else "❌ ناموفق"

    return (
        f"🆔 #{item.get('id', '—')}\n"
        f"👤 کاربر: {item.get('user_id', '—')}\n"
        f"📦 آیتم: {item.get('item_id', '—')}\n"
        f"⚙️ عملیات: {item.get('action_type', '—')}\n"
        f"📌 وضعیت: {status}\n"
        f"🕐 زمان: {item.get('created_at', '—')}"
    )


def format_history(items):
    if not items:
        return "📭 هنوز سابقه‌ای ثبت نشده است."

    return "\n\n".join(
        format_history_item(item)
        for item in items
    )


def get_user_history_text(user_id, limit=DEFAULT_LIMIT):
    items = get_user_history(user_id, limit)
    return format_history(items)


def get_item_history_text(item_id, limit=DEFAULT_LIMIT):
    items = get_item_history(item_id, limit)
    return format_history(items)


def get_history_status():
    return {
        "module": "menu_action_history",
        "status": "ready",
        "user_history": True,
        "item_history": True,
        "formatting": True,
    }
