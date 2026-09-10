# =========================
# MENU REGISTRY
# =========================

from menu_service import get_menu_item_safe
from menu_user_handlers import register_menu_action_handler


class MenuRegistry:
    """
    مدیریت ثبت عملیات داخلی منوی داینامیک.
    """

    def __init__(self, application):
        self.application = application

    def register(self, action_value, handler):
        """
        ثبت یک عملیات داخلی.
        """

        if not action_value:
            return False

        if not callable(handler):
            return False

        register_menu_action_handler(
            self.application,
            action_value,
            handler,
        )

        return True

    def register_many(self, handlers):
        """
        ثبت چند عملیات به صورت همزمان.

        handlers:
            {
                "buy_vpn": buy_vpn_handler,
                "wallet": wallet_handler,
            }
        """

        if not isinstance(handlers, dict):
            return False

        success_count = 0

        for action_value, handler in handlers.items():

            if self.register(
                action_value,
                handler,
            ):
                success_count += 1

        return success_count

    def is_registered(self, action_value):
        """
        بررسی وجود یک عملیات.
        """

        handlers = self.application.bot_data.get(
            "menu_action_handlers",
            {},
        )

        return action_value in handlers

    def get_handler(self, action_value):
        """
        دریافت Handler یک عملیات.
        """

        handlers = self.application.bot_data.get(
            "menu_action_handlers",
            {},
        )

        return handlers.get(action_value)

    def get_all(self):
        """
        دریافت تمام عملیات‌های ثبت‌شده.
        """

        handlers = self.application.bot_data.get(
            "menu_action_handlers",
            {},
        )

        return dict(handlers)

    def count(self):
        """
        تعداد عملیات‌های ثبت‌شده.
        """

        return len(self.get_all())

    def can_execute_item(self, item_id):
        """
        بررسی می‌کند آیا آیتم منو عملیات قابل اجرا دارد.
        """

        item = get_menu_item_safe(item_id)

        if not item:
            return False

        action_type = (
            item.get("action_type") or
            ""
        )

        if action_type != "callback":
            return True

        action_value = (
            item.get("action_value") or
            ""
        ).strip()

        if not action_value:
            return False

        return self.is_registered(
            action_value
        )

    def get_item_status(self, item_id):
        """
        وضعیت اتصال یک آیتم به Handler.
        """

        item = get_menu_item_safe(item_id)

        if not item:
            return {
                "exists": False,
                "connected": False,
                "action_type": None,
                "action_value": None,
            }

        action_type = (
            item.get("action_type") or
            ""
        )

        action_value = (
            item.get("action_value") or
            ""
        ).strip()

        if action_type != "callback":
            connected = True
        else:
            connected = (
                bool(action_value)
                and self.is_registered(
                    action_value
                )
            )

        return {
            "exists": True,
            "connected": connected,
            "action_type": action_type,
            "action_value": action_value,
        }


def create_menu_registry(application):
    """
    ساخت Registry برای Application.
    """

    registry = MenuRegistry(application)

    application.bot_data[
        "menu_registry"
    ] = registry

    return registry


def get_menu_registry(application):
    """
    دریافت Registry موجود.
    """

    registry = application.bot_data.get(
        "menu_registry"
    )

    if registry is None:
        registry = create_menu_registry(
            application
        )

    return registry


def register_menu_action(
    application,
    action_value,
    handler,
):
    """
    ثبت سریع یک عملیات.
    """

    registry = get_menu_registry(
        application
    )

    return registry.register(
        action_value,
        handler,
    )


def register_menu_actions(
    application,
    handlers,
):
    """
    ثبت سریع چند عملیات.
    """

    registry = get_menu_registry(
        application
    )

    return registry.register_many(
        handlers
    )


def is_menu_action_registered(
    application,
    action_value,
):
    """
    بررسی ثبت بودن یک عملیات.
    """

    registry = get_menu_registry(
        application
    )

    return registry.is_registered(
        action_value
    )


def get_menu_action_handler(
    application,
    action_value,
):
    """
    دریافت Handler یک عملیات.
    """

    registry = get_menu_registry(
        application
    )

    return registry.get_handler(
        action_value
    )


def get_menu_registry_status(application):
    """
    گزارش وضعیت Registry.
    """

    registry = get_menu_registry(
        application
    )

    return {
        "registered_actions": registry.count(),
        "actions": list(
            registry.get_all().keys()
        ),
    }
