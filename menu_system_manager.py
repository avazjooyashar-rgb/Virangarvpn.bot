# =========================
# MENU SYSTEM MANAGER
# =========================

from menu_bootstrap import initialize_menu_system
from menu_system_status import get_full_menu_status
from menu_admin_service import (
    admin_validate_menu,
    admin_repair_menu,
)
from menu_action_manager import (
    enable_action_system,
    disable_action_system,
    is_action_system_enabled,
)


class MenuSystemManager:
    def __init__(self):
        self.enabled = True

    def initialize(self):
        if not self.enabled:
            return {
                "success": False,
                "message": "⛔ سیستم منو غیرفعال است.",
            }

        return initialize_menu_system()

    def status(self):
        result = get_full_menu_status()

        result["system_enabled"] = self.enabled
        result["action_system_enabled"] = is_action_system_enabled()

        return result

    def validate(self):
        if not self.enabled:
            return {
                "success": False,
                "message": "⛔ سیستم منو غیرفعال است.",
            }

        return admin_validate_menu()

    def repair(self):
        if not self.enabled:
            return {
                "success": False,
                "message": "⛔ سیستم منو غیرفعال است.",
            }

        return admin_repair_menu()

    def enable(self):
        self.enabled = True
        enable_action_system()

        return {
            "success": True,
            "message": "✅ سیستم منو فعال شد.",
        }

    def disable(self):
        self.enabled = False
        disable_action_system()

        return {
            "success": True,
            "message": "⛔ سیستم منو غیرفعال شد.",
        }

    def is_enabled(self):
        return self.enabled


menu_system_manager = MenuSystemManager()


def initialize_menu():
    return menu_system_manager.initialize()


def get_system_status():
    return menu_system_manager.status()


def validate_menu_system():
    return menu_system_manager.validate()


def repair_menu_system():
    return menu_system_manager.repair()


def enable_menu_system():
    return menu_system_manager.enable()


def disable_menu_system():
    return menu_system_manager.disable()


def is_menu_system_enabled():
    return menu_system_manager.is_enabled()


def get_manager_status():
    return {
        "module": "menu_system_manager",
        "status": "ready",
        "enabled": menu_system_manager.is_enabled(),
        "action_system": is_action_system_enabled(),
    }
