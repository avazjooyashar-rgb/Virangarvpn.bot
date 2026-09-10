# =========================
# MENU ACTION DISPATCHER
# =========================

from menu_action_router import (
    route_menu_action,
    ACTION_CALLBACK,
    ACTION_URL,
    ACTION_SUBMENU,
)

from menu_registry import get_menu_action_handler
from menu_service import get_menu_item_safe


def dispatch_menu_action(item_id):
    """
    مسیر اجرای یک آیتم منو را مشخص می‌کند.
    """

    action = route_menu_action(item_id)

    if not action or not action.get("success"):
        return {
            "success": False,
            "type": "error",
            "message": "❌ عملیات منو پیدا نشد.",
            "value": "",
            "item": None,
        }

    action_type = action.get("type")
    value = action.get("value", "")

    if action_type == ACTION_CALLBACK:
        return dispatch_callback_action(item_id, value)

    if action_type == ACTION_URL:
        return dispatch_url_action(item_id, value)

    if action_type == ACTION_SUBMENU:
        return dispatch_submenu_action(item_id, value)

    return {
        "success": False,
        "type": "error",
        "message": "❌ نوع عملیات نامعتبر است.",
        "value": "",
        "item": action.get("item"),
    }


def dispatch_callback_action(item_id, callback_value=None):
    """
    اجرای callback داخلی ثبت‌شده برای آیتم.
    """

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "success": False,
            "type": ACTION_CALLBACK,
            "message": "❌ آیتم منو پیدا نشد.",
        }

    if not int(item.get("is_active", 0)):
        return {
            "success": False,
            "type": ACTION_CALLBACK,
            "message": "⚠️ این گزینه در حال حاضر غیرفعال است.",
        }

    value = (
        callback_value
        if callback_value is not None
        else item.get("action_value") or ""
    )

    handler = get_menu_action_handler(item_id)

    if handler is None:
        return {
            "success": False,
            "type": ACTION_CALLBACK,
            "message": "⚠️ برای این دکمه هنوز عملیاتی ثبت نشده است.",
            "value": value,
            "item": item,
        }

    return {
        "success": True,
        "type": ACTION_CALLBACK,
        "message": "✅ عملیات آماده اجراست.",
        "value": value,
        "handler": handler,
        "item": item,
    }


def dispatch_url_action(item_id, url=None):
    """
    آماده‌سازی لینک برای ارسال به کاربر.
    """

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "success": False,
            "type": ACTION_URL,
            "message": "❌ آیتم منو پیدا نشد.",
        }

    if not int(item.get("is_active", 0)):
        return {
            "success": False,
            "type": ACTION_URL,
            "message": "⚠️ این گزینه در حال حاضر غیرفعال است.",
        }

    value = url or item.get("action_value") or ""

    if not value:
        return {
            "success": False,
            "type": ACTION_URL,
            "message": "❌ لینک این گزینه تنظیم نشده است.",
            "item": item,
        }

    return {
        "success": True,
        "type": ACTION_URL,
        "message": "✅ لینک آماده است.",
        "value": value,
        "item": item,
    }


def dispatch_submenu_action(item_id, value=None):
    """
    آماده‌سازی زیرمنوی یک آیتم.
    """

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "success": False,
            "type": ACTION_SUBMENU,
            "message": "❌ آیتم منو پیدا نشد.",
        }

    if not int(item.get("is_active", 0)):
        return {
            "success": False,
            "type": ACTION_SUBMENU,
            "message": "⚠️ این گزینه در حال حاضر غیرفعال است.",
        }

    return {
        "success": True,
        "type": ACTION_SUBMENU,
        "message": "✅ زیرمنو آماده نمایش است.",
        "value": value or "",
        "parent_id": item_id,
        "item": item,
    }


def is_dispatchable_action(item_id):
    result = dispatch_menu_action(item_id)
    return bool(result.get("success"))


def get_dispatch_result(item_id):
    result = dispatch_menu_action(item_id)

    return {
        "success": result.get("success", False),
        "type": result.get("type", "error"),
        "message": result.get("message", ""),
        "value": result.get("value", ""),
    }
