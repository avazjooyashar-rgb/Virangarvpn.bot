# =========================
# MENU PERMISSIONS
# =========================

SUPER_ADMIN_ID = 691651240


# =========================
# BASIC PERMISSION
# =========================

def is_super_admin(user_id):
    if not user_id:
        return False

    try:
        return int(user_id) == SUPER_ADMIN_ID
    except (TypeError, ValueError):
        return False


def can_manage_menu(user_id):
    return is_super_admin(user_id)


# =========================
# ITEM PERMISSIONS
# =========================

def can_create_menu_item(user_id):
    return can_manage_menu(user_id)


def can_edit_menu_item(user_id, item_id=None):
    return can_manage_menu(user_id)


def can_delete_menu_item(user_id, item_id=None):
    return can_manage_menu(user_id)


def can_toggle_menu_item(user_id, item_id=None):
    return can_manage_menu(user_id)


def can_move_menu_item(user_id, item_id=None):
    return can_manage_menu(user_id)


# =========================
# ACTION PERMISSIONS
# =========================

def can_use_menu_action(user_id, action_type):
    """
    بررسی می‌کند کاربر اجازه استفاده از نوع اکشن را دارد یا نه.
    این تابع برای کاربران عادی استفاده می‌شود.
    """

    allowed_types = {
        "callback",
        "url",
        "submenu",
    }

    return action_type in allowed_types


# =========================
# ADMIN PANEL ACCESS
# =========================

def can_open_menu_manager(user_id):
    return can_manage_menu(user_id)


# =========================
# PERMISSION DESCRIPTION
# =========================

def get_permission_name(user_id):
    if is_super_admin(user_id):
        return "👑 سوپر ادمین"

    return "👤 کاربر عادی"


# =========================
# PERMISSION CHECK
# =========================

def require_menu_permission(user_id):
    """
    نتیجه استاندارد برای استفاده در Handlerها
    """

    if can_manage_menu(user_id):
        return {
            "allowed": True,
            "message": "",
        }

    return {
        "allowed": False,
        "message": "⛔ شما اجازه مدیریت منوی ربات را ندارید.",
    }
