# =========================
# MENU ACTION EXECUTOR
# =========================

import inspect

from menu_action_dispatcher import (
    dispatch_menu_action,
    ACTION_CALLBACK,
    ACTION_URL,
    ACTION_SUBMENU,
)


async def _execute_handler(handler, update, context, item):
    """
    اجرای امن handler ثبت‌شده.
    هم handler معمولی و هم async را پشتیبانی می‌کند.
    """

    if handler is None:
        return {
            "success": False,
            "message": "❌ handler برای این گزینه پیدا نشد.",
        }

    try:
        result = handler(update, context, item)

        if inspect.isawaitable(result):
            result = await result

        if result is None:
            return {
                "success": True,
                "message": "✅ عملیات با موفقیت اجرا شد.",
            }

        if isinstance(result, dict):
            return result

        return {
            "success": True,
            "message": str(result),
            "result": result,
        }

    except Exception as exc:
        return {
            "success": False,
            "message": "❌ هنگام اجرای عملیات خطایی رخ داد.",
            "error": str(exc),
        }


async def execute_menu_action(item_id, update, context):
    """
    اجرای کامل عملیات یک آیتم منو.
    """

    result = dispatch_menu_action(item_id)

    if not result.get("success"):
        return result

    action_type = result.get("type")

    if action_type == ACTION_CALLBACK:
        return await _execute_handler(
            result.get("handler"),
            update,
            context,
            result.get("item"),
        )

    if action_type == ACTION_URL:
        return {
            "success": True,
            "type": ACTION_URL,
            "url": result.get("value", ""),
            "item": result.get("item"),
            "message": "🔗 لینک آماده ارسال است.",
        }

    if action_type == ACTION_SUBMENU:
        return {
            "success": True,
            "type": ACTION_SUBMENU,
            "parent_id": result.get("parent_id"),
            "item": result.get("item"),
            "message": "📂 زیرمنو آماده نمایش است.",
        }

    return {
        "success": False,
        "message": "❌ نوع عملیات پشتیبانی نمی‌شود.",
    }


async def execute_callback_action(item_id, update, context):
    result = dispatch_menu_action(item_id)

    if not result.get("success"):
        return result

    if result.get("type") != ACTION_CALLBACK:
        return {
            "success": False,
            "message": "❌ این گزینه از نوع callback نیست.",
        }

    return await _execute_handler(
        result.get("handler"),
        update,
        context,
        result.get("item"),
    )


def is_executable_result(result):
    return bool(
        isinstance(result, dict)
        and result.get("success")
    )


def get_executor_status():
    return {
        "module": "menu_action_executor",
        "status": "ready",
        "supports_async": True,
        "supports_callback": True,
        "supports_url": True,
        "supports_submenu": True,
    }
