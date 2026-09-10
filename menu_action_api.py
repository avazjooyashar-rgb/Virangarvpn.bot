# =========================
# MENU ACTION API
# =========================

from menu_action_orchestrator import execute_orchestrated_action
from menu_action_result import (
    success_result,
    error_result,
)


def prepare_menu_action(user_id, item_id):
    from menu_action_pipeline import run_menu_action_pipeline

    return run_menu_action_pipeline(
        user_id=user_id,
        item_id=item_id,
    )


async def execute_menu_action_api(
    user_id,
    item_id,
    update,
    context,
):
    try:
        user_id = int(user_id)
        item_id = int(item_id)
    except (TypeError, ValueError):
        return error_result(
            message="❌ شناسه کاربر یا آیتم نامعتبر است.",
            user_id=user_id,
            item_id=item_id,
        )

    try:
        result = await execute_orchestrated_action(
            user_id=user_id,
            item_id=item_id,
            update=update,
            context=context,
        )

        if not result:
            return error_result(
                message="❌ نتیجه‌ای دریافت نشد.",
                user_id=user_id,
                item_id=item_id,
            )

        return result

    except Exception as exc:
        return error_result(
            message=f"❌ خطا در API اکشن: {exc}",
            user_id=user_id,
            item_id=item_id,
        )


def get_action_api_status():
    return {
        "module": "menu_action_api",
        "status": "ready",
        "prepare": True,
        "execute": True,
        "error_handling": True,
    }
