# =========================
# MENU BOOTSTRAP
# =========================

from user_menu_manager import initialize_user_menu
from menu_integrity import validate_menu_integrity


def initialize_menu_system():
    """
    راه‌اندازی کامل سیستم منوی داینامیک.
    """

    # ساخت جدول و منوی پیش‌فرض
    initialize_user_menu()

    # بررسی سلامت ساختار منو
    report = validate_menu_integrity()

    return {
        "initialized": True,
        "healthy": report.get("valid", False),
        "report": report,
    }


def check_menu_system():
    """
    بررسی وضعیت فعلی سیستم منو.
    """

    report = validate_menu_integrity()

    return {
        "healthy": report.get("valid", False),
        "errors": report.get("errors", []),
        "error_count": report.get("error_count", 0),
    }


def get_menu_system_status():
    """
    وضعیت خلاصه سیستم منو.
    """

    report = validate_menu_integrity()

    return {
        "module": "menu_bootstrap",
        "status": "ready",
        "healthy": report.get("valid", False),
        "error_count": report.get("error_count", 0),
    }


def ensure_menu_system():
    """
    اطمینان از آماده بودن سیستم منو.
    """

    result = initialize_menu_system()

    if result["healthy"]:
        return {
            "success": True,
            "message": "✅ سیستم منو با موفقیت آماده شد.",
            "data": result,
        }

    return {
        "success": False,
        "message": "⚠️ سیستم منو آماده شد اما نیاز به بررسی دارد.",
        "data": result,
    }
