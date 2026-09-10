# =========================================================
# VIRANGAR VPN
# MENU CONTROLLER
# =========================================================
#
# کنترل عملیات مدیریت منوی کاربران
# اتصال نهایی به Telegram handlers در مرحله Integration
# =========================================================

from admin_menu_manager import (
    create_menu_item,
    edit_menu_item,
    remove_menu_item,
    toggle_item,
    move_item_up,
    move_item_down,
    get_item_details,
    get_menu_summary,
)

from menu_state_manager import (
    get_state,
    set_state,
    clear_state,
    get_data,
    set_data,
    get_data_value,
    get_item_id,
    set_item_id,
    move_to_next_state,
    STATE_NONE,
    STATE_ADD_TITLE,
    STATE_ADD_ICON,
    STATE_ADD_ACTION_TYPE,
    STATE_ADD_ACTION_VALUE,
    STATE_ADD_PARENT,
    STATE_ADD_ORDER,
    STATE_EDIT_TITLE,
    STATE_EDIT_ICON,
    STATE_EDIT_ACTION_TYPE,
    STATE_EDIT_ACTION_VALUE,
    STATE_EDIT_PARENT,
    STATE_EDIT_ORDER,
)


# =========================================================
# DEFAULT VALUES
# =========================================================

DEFAULT_ICON = "🔘"
DEFAULT_ACTION_TYPE = "callback"
DEFAULT_PARENT_ID = None
DEFAULT_ORDER = None


# =========================================================
# INPUT CLEANER
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def clean_int(value, default=None):
    if value is None:
        return default

    value = clean_text(value)

    if not value:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# ADD FLOW
# =========================================================

def start_add_flow(context):
    clear_state(context)

    set_state(
        context,
        STATE_ADD_TITLE
    )

    return STATE_ADD_TITLE


def save_add_title(context, value):
    value = clean_text(value)

    if not value:
        raise ValueError(
            "عنوان دکمه نمی‌تواند خالی باشد."
        )

    set_data(
        context,
        "title",
        value
    )

    set_state(
        context,
        STATE_ADD_ICON
    )

    return STATE_ADD_ICON


def save_add_icon(context, value):
    value = clean_text(value)

    if not value:
        value = DEFAULT_ICON

    set_data(
        context,
        "icon",
        value
    )

    set_state(
        context,
        STATE_ADD_ACTION_TYPE
    )

    return STATE_ADD_ACTION_TYPE


def save_add_action_type(context, value):
    value = clean_text(value).lower()

    allowed = {
        "callback",
        "url",
        "submenu",
    }

    if value not in allowed:
        raise ValueError(
            "نوع عملیات نامعتبر است."
        )

    set_data(
        context,
        "action_type",
        value
    )

    set_state(
        context,
        STATE_ADD_ACTION_VALUE
    )

    return STATE_ADD_ACTION_VALUE


def save_add_action_value(context, value):
    value = clean_text(value)

    action_type = get_data_value(
        context,
        "action_type",
        DEFAULT_ACTION_TYPE
    )

    if action_type == "submenu":
        value = ""

    set_data(
        context,
        "action_value",
        value
    )

    set_state(
        context,
        STATE_ADD_PARENT
    )

    return STATE_ADD_PARENT


def save_add_parent(context, value):
    value = clean_text(value)

    if value in ("", "-", "none", "null", "اصلی"):
        parent_id = DEFAULT_PARENT_ID
    else:
        parent_id = clean_int(value)

        if parent_id is None:
            raise ValueError(
                "شناسه والد باید عدد باشد."
            )

    set_data(
        context,
        "parent_id",
        parent_id
    )

    set_state(
        context,
        STATE_ADD_ORDER
    )

    return STATE_ADD_ORDER


def save_add_order(context, value):
    value = clean_text(value)

    if value in ("", "-", "auto", "خودکار"):
        order = DEFAULT_ORDER
    else:
        order = clean_int(value)

        if order is None:
            raise ValueError(
                "ترتیب باید عدد باشد."
            )

    set_data(
        context,
        "sort_order",
        order
    )

    return finalize_add(context)


def finalize_add(context):
    data = get_data(context)

    item = create_menu_item(
        title=data.get("title", ""),
        icon=data.get("icon", DEFAULT_ICON),
        action_type=data.get(
            "action_type",
            DEFAULT_ACTION_TYPE
        ),
        action_value=data.get(
            "action_value",
            ""
        ),
        parent_id=data.get(
            "parent_id",
            DEFAULT_PARENT_ID
        ),
        sort_order=data.get(
            "sort_order",
            DEFAULT_ORDER
        ),
    )

    clear_state(context)

    return item


# =========================================================
# EDIT FLOW
# =========================================================

def start_edit_flow(context, item_id):
    item = get_item_details(item_id)

    if not item:
        return None

    clear_state(context)

    set_item_id(
        context,
        item_id
    )

    set_data(
        context,
        "old_data",
        item
    )

    set_state(
        context,
        STATE_EDIT_TITLE
    )

    return STATE_EDIT_TITLE


def save_edit_title(context, value):
    value = clean_text(value)

    if not value:
        raise ValueError(
            "عنوان دکمه نمی‌تواند خالی باشد."
        )

    set_data(
        context,
        "title",
        value
    )

    set_state(
        context,
        STATE_EDIT_ICON
    )

    return STATE_EDIT_ICON


def save_edit_icon(context, value):
    value = clean_text(value)

    if not value:
        value = DEFAULT_ICON

    set_data(
        context,
        "icon",
        value
    )

    set_state(
        context,
        STATE_EDIT_ACTION_TYPE
    )

    return STATE_EDIT_ACTION_TYPE


def save_edit_action_type(context, value):
    value = clean_text(value).lower()

    allowed = {
        "callback",
        "url",
        "submenu",
    }

    if value not in allowed:
        raise ValueError(
            "نوع عملیات نامعتبر است."
        )

    set_data(
        context,
        "action_type",
        value
    )

    set_state(
        context,
        STATE_EDIT_ACTION_VALUE
    )

    return STATE_EDIT_ACTION_VALUE


def save_edit_action_value(context, value):
    value = clean_text(value)

    action_type = get_data_value(
        context,
        "action_type",
        DEFAULT_ACTION_TYPE
    )

    if action_type == "submenu":
        value = ""

    set_data(
        context,
        "action_value",
        value
    )

    set_state(
        context,
        STATE_EDIT_PARENT
    )

    return STATE_EDIT_PARENT


def save_edit_parent(context, value):
    value = clean_text(value)

    if value in ("", "-", "none", "null", "اصلی"):
        parent_id = DEFAULT_PARENT_ID
    else:
        parent_id = clean_int(value)

        if parent_id is None:
            raise ValueError(
                "شناسه والد باید عدد باشد."
            )

    set_data(
        context,
        "parent_id",
        parent_id
    )

    set_state(
        context,
        STATE_EDIT_ORDER
    )

    return STATE_EDIT_ORDER


def save_edit_order(context, value):
    value = clean_text(value)

    if value in ("", "-", "auto", "خودکار"):
        order = DEFAULT_ORDER
    else:
        order = clean_int(value)

        if order is None:
            raise ValueError(
                "ترتیب باید عدد باشد."
            )

    set_data(
        context,
        "sort_order",
        order
    )

    return finalize_edit(context)


def finalize_edit(context):
    item_id = get_item_id(context)

    if not item_id:
        clear_state(context)
        return False

    data = get_data(context)

    result = edit_menu_item(
        item_id=item_id,
        title=data.get("title"),
        icon=data.get("icon"),
        action_type=data.get("action_type"),
        action_value=data.get("action_value"),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order"),
    )

    clear_state(context)

    return result


# =========================================================
# QUICK OPERATIONS
# =========================================================

def toggle_menu_item(item_id):
    return toggle_item(item_id)


def delete_menu_item(item_id):
    return remove_menu_item(item_id)


def move_menu_item_up(item_id):
    return move_item_up(item_id)


def move_menu_item_down(item_id):
    return move_item_down(item_id)


# =========================================================
# ITEM PREVIEW
# =========================================================

def get_item_preview(item_id):
    item = get_item_details(item_id)

    if not item:
        return None

    return {
        "id": item["id"],
        "title": item["title"],
        "icon": item["icon"],
        "action_type": item["action_type"],
        "action_value": item["action_value"],
        "parent_id": item["parent_id"],
        "sort_order": item["sort_order"],
        "is_active": item["is_active"],
    }


# =========================================================
# CURRENT FLOW DATA
# =========================================================

def get_current_flow(context):
    return {
        "state": get_state(context),
        "item_id": get_item_id(context),
        "data": dict(get_data(context)),
    }


# =========================================================
# CANCEL
# =========================================================

def cancel_flow(context):
    clear_state(context)
    return STATE_NONE


# =========================================================
# SUMMARY
# =========================================================

def get_controller_summary():
    return get_menu_summary()


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "start_add_flow",
    "save_add_title",
    "save_add_icon",
    "save_add_action_type",
    "save_add_action_value",
    "save_add_parent",
    "save_add_order",
    "finalize_add",

    "start_edit_flow",
    "save_edit_title",
    "save_edit_icon",
    "save_edit_action_type",
    "save_edit_action_value",
    "save_edit_parent",
    "save_edit_order",
    "finalize_edit",

    "toggle_menu_item",
    "delete_menu_item",
    "move_menu_item_up",
    "move_menu_item_down",

    "get_item_preview",
    "get_current_flow",
    "cancel_flow",
    "get_controller_summary",
]
