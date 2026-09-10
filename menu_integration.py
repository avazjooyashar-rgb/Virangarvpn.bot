# =========================
# MENU SYSTEM INTEGRATION
# =========================

from menu_system_manager import (
    initialize_menu,
    get_system_status,
)

from menu_admin_handlers import (
    register_menu_admin_handlers,
)

from menu_user_handlers import (
    register_user_menu_handlers,
)

from menu_event_handlers import (
    register_menu_event_handlers,
)


def initialize_menu_integration():
    """
    Initialize the complete menu system.
    """

    result = initialize_menu()

    return {
        "success": True,
        "initialized": result,
        "status": get_system_status(),
    }


def register_menu_system(application):
    """
    Register all menu-related Telegram handlers.
    """

    registered = []

    try:
        register_menu_admin_handlers(application)
        registered.append("admin_handlers")
    except Exception as exc:
        return {
            "success": False,
            "message": f"❌ خطا در ثبت هندلرهای مدیریت منو: {exc}",
            "registered": registered,
        }

    try:
        register_user_menu_handlers(application)
        registered.append("user_handlers")
    except Exception as exc:
        return {
            "success": False,
            "message": f"❌ خطا در ثبت هندلرهای کاربر: {exc}",
            "registered": registered,
        }

    try:
        register_menu_event_handlers(application)
        registered.append("event_handlers")
    except Exception as exc:
        return {
            "success": False,
            "message": f"❌ خطا در ثبت هندلرهای رویداد منو: {exc}",
            "registered": registered,
        }

    return {
        "success": True,
        "message": "✅ تمام هندلرهای سیستم منو ثبت شدند.",
        "registered": registered,
    }


def setup_menu_system(application):
    """
    Complete setup:
    1. Initialize database/menu
    2. Validate system
    3. Register handlers
    """

    initialization = initialize_menu_integration()

    if not initialization.get("success"):
        return initialization

    registration = register_menu_system(application)

    return {
        "success": registration.get("success", False),
        "initialization": initialization,
        "registration": registration,
        "status": get_system_status(),
    }


def get_integration_status():
    status = get_system_status()

    return {
        "module": "menu_integration",
        "status": "ready",
        "system_healthy": status.get("healthy", False),
        "system_enabled": status.get("system_enabled", True),
        "action_system_enabled": status.get(
            "action_system_enabled",
            True,
        ),
    }
