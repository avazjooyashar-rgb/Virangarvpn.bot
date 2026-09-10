# =========================
# MENU ACTION SECURITY
# =========================

from urllib.parse import urlparse

from menu_action_types import (
    ACTION_CALLBACK,
    ACTION_URL,
    ACTION_SUBMENU,
    normalize_action_type,
)

from menu_service import get_menu_item_safe


MAX_CALLBACK_LENGTH = 200
MAX_URL_LENGTH = 500


def is_safe_user_id(user_id):
    try:
        return int(user_id) > 0
    except (TypeError, ValueError):
        return False


def is_safe_item_id(item_id):
    try:
        return int(item_id) > 0
    except (TypeError, ValueError):
        return False


def is_safe_callback(value):
    if not value:
        return False

    value = str(value).strip()

    if len(value) > MAX_CALLBACK_LENGTH:
        return False

    if "\n" in value or "\r" in value:
        return False

    return True


def is_safe_url(value):
    if not value:
        return False

    value = str(value).strip()

    if len(value) > MAX_URL_LENGTH:
        return False

    try:
        parsed = urlparse(value)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    return True


def validate_action_security(action_type, value):
    action_type = normalize_action_type(action_type)

    if action_type == ACTION_CALLBACK:
        valid = is_safe_callback(value)

    elif action_type == ACTION_URL:
        valid = is_safe_url(value)

    elif action_type == ACTION_SUBMENU:
        valid = True

    else:
        valid = False

    return {
        "safe": valid,
        "type": action_type,
        "value": value or "",
    }


def can_execute_menu_item(user_id, item_id):
    if not is_safe_user_id(user_id):
        return False

    if not is_safe_item_id(item_id):
        return False

    item = get_menu_item_safe(item_id)

    if not item:
        return False

    if int(item.get("is_active", 0)) != 1:
        return False

    result = validate_action_security(
        item.get("action_type"),
        item.get("action_value"),
    )

    return result["safe"]


def get_security_report(item_id):
    if not is_safe_item_id(item_id):
        return {
            "safe": False,
            "message": "❌ شناسه آیتم نامعتبر است.",
        }

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "safe": False,
            "message": "❌ آیتم منو پیدا نشد.",
        }

    result = validate_action_security(
        item.get("action_type"),
        item.get("action_value"),
    )

    return {
        "safe": result["safe"],
        "item_id": item_id,
        "action_type": result["type"],
        "message": (
            "🟢 عملیات امن است."
            if result["safe"]
            else "🔴 عملیات نیاز به بررسی دارد."
        ),
    }


def get_security_status():
    return {
        "module": "menu_action_security",
        "status": "ready",
        "callback_validation": True,
        "url_validation": True,
        "submenu_validation": True,
    }
