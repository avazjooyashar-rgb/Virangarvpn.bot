# =========================
# MENU SERVICE
# =========================

from user_menu_manager import (
    add_menu_item,
    get_menu_item,
    get_all_menu_items,
    get_main_menu_items,
    get_submenu_items,
    update_menu_item,
    delete_menu_item,
    set_menu_item_active,
    toggle_menu_item,
    move_item_up,
    move_item_down,
    normalize_menu_order,
    get_menu_tree,
)

from menu_validator import (
    validate_create,
    validate_edit,
)


# =========================
# CREATE
# =========================

def create_menu_item_safe(
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
    is_active=1,
):
    errors = validate_create(
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=is_active,
    )

    if errors:
        return {
            "success": False,
            "errors": errors,
            "item": None,
        }

    item_id = add_menu_item(
        title=title.strip(),
        icon=(icon or "").strip(),
        action_type=action_type,
        action_value=(action_value or "").strip(),
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=is_active,
    )

    return {
        "success": True,
        "errors": [],
        "item": get_menu_item(item_id),
    }


# =========================
# UPDATE
# =========================

def update_menu_item_safe(
    item_id,
    title=None,
    icon=None,
    action_type=None,
    action_value=None,
    parent_id=None,
    sort_order=None,
    is_active=None,
):
    current = get_menu_item(item_id)

    if not current:
        return {
            "success": False,
            "errors": ["دکمه موردنظر پیدا نشد."],
            "item": None,
        }

    data = {
        "title": current["title"] if title is None else title,
        "icon": current["icon"] if icon is None else icon,
        "action_type": (
            current["action_type"]
            if action_type is None
            else action_type
        ),
        "action_value": (
            current["action_value"]
            if action_value is None
            else action_value
        ),
        "parent_id": (
            current["parent_id"]
            if parent_id is None
            else parent_id
        ),
        "sort_order": (
            current["sort_order"]
            if sort_order is None
            else sort_order
        ),
        "is_active": (
            current["is_active"]
            if is_active is None
            else is_active
        ),
    }

    errors = validate_edit(
        item_id=item_id,
        title=data["title"],
        icon=data["icon"],
        action_type=data["action_type"],
        action_value=data["action_value"],
        parent_id=data["parent_id"],
        sort_order=data["sort_order"],
        is_active=data["is_active"],
    )

    if errors:
        return {
            "success": False,
            "errors": errors,
            "item": current,
        }

    update_menu_item(
        item_id=item_id,
        title=data["title"].strip(),
        icon=(data["icon"] or "").strip(),
        action_type=data["action_type"],
        action_value=(data["action_value"] or "").strip(),
        parent_id=data["parent_id"],
        sort_order=data["sort_order"],
        is_active=data["is_active"],
    )

    return {
        "success": True,
        "errors": [],
        "item": get_menu_item(item_id),
    }


# =========================
# DELETE
# =========================

def delete_menu_item_safe(item_id):
    item = get_menu_item(item_id)

    if not item:
        return {
            "success": False,
            "message": "دکمه پیدا نشد.",
        }

    result = delete_menu_item(item_id)

    normalize_menu_order(item["parent_id"])

    return {
        "success": bool(result),
        "message": (
            "دکمه با موفقیت حذف شد."
            if result
            else "حذف دکمه انجام نشد."
        ),
    }


# =========================
# TOGGLE
# =========================

def toggle_menu_item_safe(item_id):
    item = get_menu_item(item_id)

    if not item:
        return {
            "success": False,
            "message": "دکمه پیدا نشد.",
            "item": None,
        }

    result = toggle_menu_item(item_id)

    return {
        "success": bool(result),
        "message": (
            "وضعیت دکمه تغییر کرد."
            if result
            else "تغییر وضعیت انجام نشد."
        ),
        "item": get_menu_item(item_id),
    }


# =========================
# MOVE UP
# =========================

def move_menu_item_up_safe(item_id):
    item = get_menu_item(item_id)

    if not item:
        return {
            "success": False,
            "message": "دکمه پیدا نشد.",
        }

    result = move_item_up(item_id)

    return {
        "success": bool(result),
        "message": (
            "دکمه یک مرحله بالا رفت."
            if result
            else "دکمه از قبل در بالاترین جایگاه است."
        ),
    }


# =========================
# MOVE DOWN
# =========================

def move_menu_item_down_safe(item_id):
    item = get_menu_item(item_id)

    if not item:
        return {
            "success": False,
            "message": "دکمه پیدا نشد.",
        }

    result = move_item_down(item_id)

    return {
        "success": bool(result),
        "message": (
            "دکمه یک مرحله پایین رفت."
            if result
            else "دکمه از قبل در پایین‌ترین جایگاه است."
        ),
    }


# =========================
# GETTERS
# =========================

def get_user_menu():
    return get_main_menu_items(include_disabled=False)


def get_user_submenu(parent_id):
    return get_submenu_items(
        parent_id,
        include_disabled=False,
    )


def get_admin_menu_items():
    return get_all_menu_items(
        include_disabled=True
    )


def get_menu_item_safe(item_id):
    return get_menu_item(item_id)


def get_menu_tree_safe():
    return get_menu_tree()


# =========================
# PREVIEW
# =========================

def get_menu_preview():
    items = get_main_menu_items(
        include_disabled=False
    )

    preview = []

    for item in items:
        icon = item.get("icon") or ""
        title = item.get("title") or ""

        label = f"{icon} {title}".strip()

        preview.append({
            "id": item["id"],
            "label": label,
            "action_type": item["action_type"],
            "action_value": item.get("action_value") or "",
        })

    return preview


# =========================
# SUMMARY
# =========================

def get_menu_service_summary():
    items = get_all_menu_items(
        include_disabled=True
    )

    active = [
        item for item in items
        if item.get("is_active") == 1
    ]

    disabled = [
        item for item in items
        if item.get("is_active") == 0
    ]

    main_items = [
        item for item in items
        if item.get("parent_id") is None
    ]

    submenu_items = [
        item for item in items
        if item.get("parent_id") is not None
    ]

    return {
        "total": len(items),
        "active": len(active),
        "disabled": len(disabled),
        "main": len(main_items),
        "submenu": len(submenu_items),
    }
