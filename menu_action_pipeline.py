# =========================
# MENU ACTION PIPELINE
# =========================

from menu_action_validator import validate_action
from menu_action_security import can_execute_menu_item
from menu_action_rate_limiter import is_action_allowed
from menu_action_cache import cache_get, cache_set
from menu_action_dispatcher import dispatch_menu_action
from menu_action_response import (
    success_response,
    error_response,
)


def prepare_menu_action(user_id, item_id):
    try:
        user_id = int(user_id)
        item_id = int(item_id)
    except (TypeError, ValueError):
        return error_response("❌ شناسه کاربر یا آیتم نامعتبر است.")

    cached = cache_get(f"action:{item_id}")

    if cached is None:
        result = dispatch_menu_action(item_id)

        if not result:
            return error_response("❌ عملیات پیدا نشد.")

        cache_set(f"action:{item_id}", result)
    else:
        result = cached

    if not result.get("success"):
        return error_response(
            result.get("message", "❌ عملیات نامعتبر است.")
        )

    return success_response(
        message="✅ عملیات آماده اجراست.",
        data=result,
    )


def validate_menu_action(user_id, item_id):
    prepared = prepare_menu_action(user_id, item_id)

    if not prepared.get("success"):
        return prepared

    action = prepared.get("data") or {}
    action_type = action.get("action_type")
    action_value = action.get("action_value")

    validation = validate_action(
        action_type,
        action_value,
    )

    if not validation.get("valid"):
        return error_response(
            validation.get(
                "message",
                "❌ عملیات نامعتبر است.",
            )
        )

    if not can_execute_menu_item(user_id, item_id):
        return error_response(
            "⛔ اجرای این عملیات مجاز نیست."
        )

    return success_response(
        message="✅ عملیات اعتبارسنجی شد.",
        data={
            "item_id": item_id,
            "action_type": validation.get("type"),
            "action_value": validation.get("value"),
        },
    )


def check_action_limit(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return error_response("❌ شناسه کاربر نامعتبر است.")

    if not is_action_allowed(user_id):
        return error_response(
            "⏳ لطفاً کمی صبر کنید و دوباره تلاش کنید."
        )

    return success_response(
        message="✅ محدودیت سرعت اجازه اجرا می‌دهد."
    )


def run_menu_action_pipeline(user_id, item_id):
    limit_result = check_action_limit(user_id)

    if not limit_result.get("success"):
        return limit_result

    validation_result = validate_menu_action(
        user_id,
        item_id,
    )

    if not validation_result.get("success"):
        return validation_result

    return success_response(
        message="✅ عملیات آماده اجراست.",
        data=validation_result.get("data"),
    )


def get_pipeline_status():
    return {
        "module": "menu_action_pipeline",
        "status": "ready",
        "validation": True,
        "security": True,
        "rate_limit": True,
        "cache": True,
        "dispatch": True,
    }
