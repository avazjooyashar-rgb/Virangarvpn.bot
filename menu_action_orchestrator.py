# =========================
# MENU ACTION ORCHESTRATOR
# =========================

from menu_action_pipeline import run_menu_action_pipeline
from menu_action_execution import execute_action
from menu_action_result import (
    success_result,
    error_result,
)


def prepare_action(user_id, item_id):
    return run_menu_action_pipeline(
        user_id=user_id,
        item_id=item_id,
    )


async def execute_orchestrated_action(
    user_id,
    item_id,
    update,
    context,
):
    preparation = prepare_action(
        user_id,
        item_id,
    )

    if not preparation.get("success"):
        return error_result(
            message=preparation.get(
                "message",
                "❌ عملیات قابل اجرا نیست.",
            ),
            item_id=item_id,
            user_id=user_id,
        )

    result = await execute_action(
        user_id=user_id,
        item_id=item_id,
        update=update,
        context=context,
    )

    if not result:
        return error_result(
            message="❌ نتیجه‌ای از اجرای عملیات دریافت نشد.",
            item_id=item_id,
            user_id=user_id,
        )

    if result.get("success"):
        return success_result(
            message=result.get(
                "message",
                "✅ عملیات با موفقیت اجرا شد.",
            ),
            action_type=result.get("type", ""),
            value=result.get("value", ""),
            item_id=item_id,
            user_id=user_id,
            data=result.get("data", {}),
        )

    return error_result(
        message=result.get(
            "message",
            "❌ اجرای عملیات ناموفق بود.",
        ),
        action_type=result.get("type", "error"),
        value=result.get("value", ""),
        item_id=item_id,
        user_id=user_id,
        data=result.get("data", {}),
    )


def get_orchestrator_status():
    return {
        "module": "menu_action_orchestrator",
        "status": "ready",
        "pipeline": True,
        "execution": True,
        "result_handling": True,
    }
