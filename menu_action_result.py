# =========================
# MENU ACTION RESULT
# =========================

from datetime import datetime


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def build_result(
    success,
    action_type="",
    value="",
    message="",
    item_id=None,
    user_id=None,
    data=None,
):
    return {
        "success": bool(success),
        "type": action_type or "",
        "value": value or "",
        "message": message or "",
        "item_id": item_id,
        "user_id": user_id,
        "data": data or {},
        "timestamp": _now(),
    }


def success_result(
    message="✅ عملیات با موفقیت انجام شد.",
    action_type="",
    value="",
    item_id=None,
    user_id=None,
    data=None,
):
    return build_result(
        success=True,
        action_type=action_type,
        value=value,
        message=message,
        item_id=item_id,
        user_id=user_id,
        data=data,
    )


def error_result(
    message="❌ اجرای عملیات ناموفق بود.",
    action_type="error",
    value="",
    item_id=None,
    user_id=None,
    data=None,
):
    return build_result(
        success=False,
        action_type=action_type,
        value=value,
        message=message,
        item_id=item_id,
        user_id=user_id,
        data=data,
    )


def is_success(result):
    return bool(
        isinstance(result, dict)
        and result.get("success") is True
    )


def is_failure(result):
    return not is_success(result)


def get_result_message(result):
    if not isinstance(result, dict):
        return "❌ نتیجه نامعتبر است."

    return result.get(
        "message",
        "❌ نتیجه‌ای دریافت نشد.",
    )


def get_result_type(result):
    if not isinstance(result, dict):
        return "error"

    return result.get("type", "error")


def get_result_value(result):
    if not isinstance(result, dict):
        return ""

    return result.get("value", "")


def get_result_data(result):
    if not isinstance(result, dict):
        return {}

    data = result.get("data")

    if isinstance(data, dict):
        return data

    return {}


def normalize_result(result):
    if not isinstance(result, dict):
        return error_result()

    return build_result(
        success=result.get("success", False),
        action_type=result.get("type", ""),
        value=result.get("value", ""),
        message=result.get("message", ""),
        item_id=result.get("item_id"),
        user_id=result.get("user_id"),
        data=result.get("data", {}),
    )


def get_result_status(result):
    normalized = normalize_result(result)

    return {
        "success": normalized["success"],
        "type": normalized["type"],
        "message": normalized["message"],
        "item_id": normalized["item_id"],
        "user_id": normalized["user_id"],
        "timestamp": normalized["timestamp"],
    }


def get_module_status():
    return {
        "module": "menu_action_result",
        "status": "ready",
        "success_result": True,
        "error_result": True,
        "normalization": True,
    }
