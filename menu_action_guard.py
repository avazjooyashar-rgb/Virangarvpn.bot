# =========================
# MENU ACTION GUARD
# =========================

from menu_action_security import can_execute_menu_item
from menu_action_rate_limiter import is_action_allowed
from menu_service import get_menu_item_safe


def guard_action(user_id, item_id):
    try:
        user_id = int(user_id)
        item_id = int(item_id)
    except (TypeError, ValueError):
        return {
            "allowed": False,
            "message": "❌ شناسه نامعتبر است.",
        }

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "allowed": False,
            "message": "❌ آیتم منو پیدا نشد.",
        }

    if int(item.get("is_active", 0)) != 1:
        return {
            "allowed": False,
            "message": "⛔ این گزینه در حال حاضر غیرفعال است.",
        }

    if not can_execute_menu_item(user_id, item_id):
        return {
            "allowed": False,
            "message": "⛔ اجرای این عملیات مجاز نیست.",
        }

    if not is_action_allowed(user_id):
        return {
            "allowed": False,
            "message": "⏳ لطفاً کمی صبر کنید و دوباره تلاش کنید.",
        }

    return {
        "allowed": True,
        "message": "✅ اجازه اجرا دارد.",
        "item": item,
    }


def is_action_allowed_by_guard(user_id, item_id):
    return guard_action(user_id, item_id).get("allowed", False)


def get_guard_status():
    return {
        "module": "menu_action_guard",
        "status": "ready",
        "security": True,
        "rate_limit": True,
        "active_check": True,
        "item_check": True,
    }
