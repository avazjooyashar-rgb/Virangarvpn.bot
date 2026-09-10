# =========================
# MENU ACTION MANAGER
# =========================

from menu_action_api import (
    prepare_menu_action,
    execute_menu_action_api,
)
from menu_action_health import run_health_check


class MenuActionManager:

    def __init__(self):
        self.enabled = True

    def prepare(self, user_id, item_id):
        if not self.enabled:
            return {
                "success": False,
                "message": "⛔ سیستم اکشن منو غیرفعال است.",
            }

        return prepare_menu_action(
            user_id=user_id,
            item_id=item_id,
        )

    async def execute(
        self,
        user_id,
        item_id,
        update,
        context,
    ):
        if not self.enabled:
            return {
                "success": False,
                "message": "⛔ سیستم اکشن منو غیرفعال است.",
            }

        return await execute_menu_action_api(
            user_id=user_id,
            item_id=item_id,
            update=update,
            context=context,
        )

    def enable(self):
        self.enabled = True
        return True

    def disable(self):
        self.enabled = False
        return True

    def is_enabled(self):
        return self.enabled

    def health(self):
        return run_health_check()

    def status(self):
        health = self.health()

        return {
            "module": "menu_action_manager",
            "status": "ready",
            "enabled": self.enabled,
            "healthy": health.get("healthy", False),
        }


menu_action_manager = MenuActionManager()


def prepare_action(user_id, item_id):
    return menu_action_manager.prepare(
        user_id,
        item_id,
    )


async def execute_action(
    user_id,
    item_id,
    update,
    context,
):
    return await menu_action_manager.execute(
        user_id=user_id,
        item_id=item_id,
        update=update,
        context=context,
    )


def enable_action_system():
    return menu_action_manager.enable()


def disable_action_system():
    return menu_action_manager.disable()


def is_action_system_enabled():
    return menu_action_manager.is_enabled()


def get_action_manager_status():
    return menu_action_manager.status()
