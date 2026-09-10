# =========================
# MENU SYSTEM STATUS
# =========================

from menu_bootstrap import check_menu_system
from menu_admin_service import get_admin_menu_service_status
from menu_action_manager import get_action_manager_status
from menu_action_health import get_health_status


def get_full_menu_status():
    menu_status = check_menu_system()
    admin_status = get_admin_menu_service_status()
    action_status = get_action_manager_status()
    health_status = get_health_status()

    healthy = (
        menu_status.get("healthy", False)
        and admin_status.get("status") == "ready"
        and action_status.get("status") == "ready"
        and health_status.get("status") == "ready"
        and health_status.get("healthy", False)
    )

    return {
        "module": "menu_system_status",
        "status": "ready",
        "healthy": healthy,
        "menu": menu_status,
        "admin": admin_status,
        "actions": action_status,
        "health": health_status,
    }


def get_menu_system_status_text():
    result = get_full_menu_status()

    status = "🟢 سالم" if result["healthy"] else "🔴 نیاز به بررسی"

    return (
        "🧩 وضعیت سیستم منو\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 وضعیت کلی: {status}\n\n"
        f"📂 سیستم منو: "
        f"{'🟢' if result['menu'].get('healthy') else '🔴'}\n"
        f"👑 مدیریت منو: "
        f"{'🟢' if result['admin'].get('status') == 'ready' else '🔴'}\n"
        f"⚡ سیستم اکشن: "
        f"{'🟢' if result['actions'].get('status') == 'ready' else '🔴'}\n"
        f"🏥 سلامت اکشن‌ها: "
        f"{'🟢' if result['health'].get('healthy') else '🔴'}"
    )


def is_menu_system_healthy():
    return get_full_menu_status().get("healthy", False)


def get_status_summary():
    result = get_full_menu_status()

    return {
        "module": "menu_system_status",
        "healthy": result["healthy"],
        "status": "healthy" if result["healthy"] else "warning",
    }
