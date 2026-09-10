# =========================
# MENU ADMIN SERVICE
# =========================

from menu_permissions import (
    can_manage_menu,
    can_create_menu_item,
    can_edit_menu_item,
    can_delete_menu_item,
    can_toggle_menu_item,
    can_move_menu_item,
)

from menu_service import (
    create_menu_item_safe,
    update_menu_item_safe,
    delete_menu_item_safe,
    toggle_menu_item_safe,
    move_menu_item_up_safe,
    move_menu_item_down_safe,
    get_menu_item_safe,
    get_admin_menu_items,
    get_menu_tree_safe,
    get_menu_preview,
)

from menu_integrity import (
    validate_menu_integrity,
    repair_menu,
)


def _deny():
    return {
        "success": False,
        "message": "⛔ شما اجازه انجام این عملیات را ندارید.",
    }


def _allow(user_id, permission_func, item_id=None):
    try:
        return permission_func(user_id, item_id)
    except TypeError:
        return permission_func(user_id)


def admin_create_menu_item(
    user_id,
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
):
    if not _allow(user_id, can_create_menu_item):
        return _deny()

    return create_menu_item_safe(
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
    )


def admin_update_menu_item(
    user_id,
    item_id,
    title=None,
    icon=None,
    action_type=None,
    action_value=None,
    parent_id=None,
    sort_order=None,
    is_active=None,
):
    if not _allow(user_id, can_edit_menu_item, item_id):
        return _deny()

    return update_menu_item_safe(
        item_id=item_id,
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=is_active,
    )


def admin_delete_menu_item(user_id, item_id):
    if not _allow(user_id, can_delete_menu_item, item_id):
        return _deny()

    return delete_menu_item_safe(item_id)


def admin_toggle_menu_item(user_id, item_id):
    if not _allow(user_id, can_toggle_menu_item, item_id):
        return _deny()

    return toggle_menu_item_safe(item_id)


def admin_move_menu_item_up(user_id, item_id):
    if not _allow(user_id, can_move_menu_item, item_id):
        return _deny()

    return move_menu_item_up_safe(item_id)


def admin_move_menu_item_down(user_id, item_id):
    if not _allow(user_id, can_move_menu_item, item_id):
        return _deny()

    return move_menu_item_down_safe(item_id)


def admin_get_menu_item(user_id, item_id):
    if not can_manage_menu(user_id):
        return _deny()

    item = get_menu_item_safe(item_id)

    if not item:
        return {
            "success": False,
            "message": "❌ آیتم موردنظر پیدا نشد.",
        }

    return {
        "success": True,
        "item": item,
    }


def admin_get_menu_items(user_id, include_disabled=True):
    if not can_manage_menu(user_id):
        return _deny()

    return {
        "success": True,
        "items": get_admin_menu_items(
            include_disabled=include_disabled
        ),
    }


def admin_get_menu_tree(user_id):
    if not can_manage_menu(user_id):
        return _deny()

    return {
        "success": True,
        "tree": get_menu_tree_safe(),
    }


def admin_get_menu_preview(user_id):
    if not can_manage_menu(user_id):
        return _deny()

    return {
        "success": True,
        "preview": get_menu_preview(),
    }


def admin_validate_menu(user_id):
    if not can_manage_menu(user_id):
        return _deny()

    report = validate_menu_integrity()

    return {
        "success": True,
        "healthy": report.get("valid", False),
        "report": report,
    }


def admin_repair_menu(user_id):
    if not can_manage_menu(user_id):
        return _deny()

    result = repair_menu()

    return {
        "success": True,
        "result": result,
    }


def get_admin_menu_service_status(user_id):
    if not can_manage_menu(user_id):
        return _deny()

    report = validate_menu_integrity()

    items = get_admin_menu_items(include_disabled=True)

    active_count = sum(
        1 for item in items
        if int(item.get("is_active", 0)) == 1
    )

    disabled_count = len(items) - active_count

    return {
        "success": True,
        "total_items": len(items),
        "active_items": active_count,
        "disabled_items": disabled_count,
        "healthy": report.get("valid", False),
        "error_count": report.get("error_count", 0),
    }
