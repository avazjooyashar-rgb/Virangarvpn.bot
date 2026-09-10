# =========================
# MENU ACTION EXECUTION
# =========================

from menu_action_executor import execute_menu_action
from menu_action_audit import (
    audit_action_attempt,
    audit_action_success,
    audit_action_failure,
)


async def execute_action(user_id, item_id, update, context):
    try:
        user_id = int(user_id)
        item_id = int(item_id)
    except (TypeError, ValueError):
        return {
            "success": False,
            "type": "error",
            "message": "❌ شناسه نامعتبر است.",
        }

    audit_action_attempt(
        user_id=user_id,
        item_id=item_id,
    )

    try:
        result = await execute_menu_action(
            item_id,
            update,
            context,
        )

        if result and result.get("success"):
            audit_action_success(
                user_id=user_id,
                item_id=item_id,
                action_type=result.get("type", ""),
                action_value=result.get("value", ""),
            )

            return result

        message = (
            result.get("message", "❌ اجرای عملیات ناموفق بود.")
            if result
            else "❌ اجرای عملیات ناموفق بود."
        )

        audit_action_failure(
            user_id=user_id,
            item_id=item_id,
            action_type=(result or {}).get("type", ""),
            action_value=(result or {}).get("value", ""),
            message=message,
        )

        return {
            "success": False,
            "type": "error",
            "message": message,
        }

    except Exception as exc:
        message = f"❌ خطا هنگام اجرای عملیات: {exc}"

        audit_action_failure(
            user_id=user_id,
            item_id=item_id,
            action_type="error",
            action_value="",
            message=message,
        )

        return {
            "success": False,
            "type": "error",
            "message": message,
        }


def get_execution_status():
    return {
        "module": "menu_action_execution",
        "status": "ready",
        "audit": True,
        "executor": True,
    }
