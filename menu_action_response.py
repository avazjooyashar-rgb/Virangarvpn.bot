# =========================
# MENU ACTION RESPONSE
# =========================

from menu_action_types import (
    ACTION_CALLBACK,
    ACTION_URL,
    ACTION_SUBMENU,
)


def success_response(
    action_type,
    message="",
    value=None,
    item=None,
    **extra,
):
    result = {
        "success": True,
        "type": action_type,
        "message": message,
        "value": value or "",
        "item": item,
    }

    result.update(extra)
    return result


def error_response(
    message="❌ عملیات ناموفق بود.",
    action_type="error",
    item=None,
    **extra,
):
    result = {
        "success": False,
        "type": action_type,
        "message": message,
        "value": "",
        "item": item,
    }

    result.update(extra)
    return result


def callback_response(
    message="",
    value="",
    item=None,
    **extra,
):
    return success_response(
        ACTION_CALLBACK,
        message=message,
        value=value,
        item=item,
        **extra,
    )


def url_response(
    url="",
    message="",
    item=None,
    **extra,
):
    return success_response(
        ACTION_URL,
        message=message,
        value=url,
        item=item,
        url=url,
        **extra,
    )


def submenu_response(
    parent_id=None,
    message="",
    item=None,
    **extra,
):
    return success_response(
        ACTION_SUBMENU,
        message=message,
        value="",
        item=item,
        parent_id=parent_id,
        **extra,
    )


def normalize_response(result):
    if not isinstance(result, dict):
        return error_response(
            "❌ پاسخ عملیات نامعتبر است."
        )

    return {
        "success": bool(result.get("success", False)),
        "type": result.get("type", "error"),
        "message": result.get("message", ""),
        "value": result.get("value", ""),
        "item": result.get("item"),
        **{
            key: value
            for key, value in result.items()
            if key not in {
                "success",
                "type",
                "message",
                "value",
                "item",
            }
        },
    }


def is_success(result):
    return bool(
        isinstance(result, dict)
        and result.get("success") is True
    )


def is_error(result):
    return not is_success(result)


def get_response_message(result):
    if not isinstance(result, dict):
        return "❌ پاسخ نامعتبر است."

    return result.get(
        "message",
        "❌ عملیات ناموفق بود.",
    )


def get_response_type(result):
    if not isinstance(result, dict):
        return "error"

    return result.get("type", "error")


def get_response_value(result):
    if not isinstance(result, dict):
        return ""

    return result.get("value", "")


def get_response_status(result):
    return {
        "success": is_success(result),
        "type": get_response_type(result),
        "message": get_response_message(result),
    }


def get_module_status():
    return {
        "module": "menu_action_response",
        "status": "ready",
        "supports": [
            ACTION_CALLBACK,
            ACTION_URL,
            ACTION_SUBMENU,
        ],
    }
