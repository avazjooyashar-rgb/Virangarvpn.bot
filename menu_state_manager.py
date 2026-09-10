# =========================================================
# VIRANGAR VPN
# MENU STATE MANAGER
# =========================================================
#
# مدیریت وضعیت کاربر هنگام:
# افزودن دکمه
# ویرایش دکمه
# حذف دکمه
#
# این فایل هنوز به bot.py وصل نمی‌شود.
# =========================================================


# =========================================================
# STATE NAMES
# =========================================================

STATE_NONE = "none"

STATE_ADD_TITLE = "add_title"
STATE_ADD_ICON = "add_icon"
STATE_ADD_ACTION_TYPE = "add_action_type"
STATE_ADD_ACTION_VALUE = "add_action_value"
STATE_ADD_PARENT = "add_parent"
STATE_ADD_ORDER = "add_order"

STATE_EDIT_TITLE = "edit_title"
STATE_EDIT_ICON = "edit_icon"
STATE_EDIT_ACTION_TYPE = "edit_action_type"
STATE_EDIT_ACTION_VALUE = "edit_action_value"
STATE_EDIT_PARENT = "edit_parent"
STATE_EDIT_ORDER = "edit_order"

STATE_DELETE_CONFIRM = "delete_confirm"


# =========================================================
# STATE KEYS
# =========================================================

STATE_KEY = "menu_state"
DATA_KEY = "menu_data"
ITEM_ID_KEY = "menu_item_id"


# =========================================================
# BASIC STATE
# =========================================================

def get_state(context):
    return context.user_data.get(
        STATE_KEY,
        STATE_NONE
    )


def set_state(context, state):
    context.user_data[STATE_KEY] = state


def clear_state(context):
    context.user_data.pop(STATE_KEY, None)
    context.user_data.pop(DATA_KEY, None)
    context.user_data.pop(ITEM_ID_KEY, None)


def is_active(context):
    return get_state(context) != STATE_NONE


# =========================================================
# DATA
# =========================================================

def get_data(context):
    return context.user_data.setdefault(
        DATA_KEY,
        {}
    )


def set_data(context, key, value):
    data = get_data(context)
    data[key] = value
    context.user_data[DATA_KEY] = data


def get_data_value(context, key, default=None):
    data = get_data(context)
    return data.get(key, default)


def remove_data(context, key):
    data = get_data(context)
    data.pop(key, None)
    context.user_data[DATA_KEY] = data


# =========================================================
# ITEM ID
# =========================================================

def set_item_id(context, item_id):
    context.user_data[ITEM_ID_KEY] = item_id


def get_item_id(context):
    return context.user_data.get(
        ITEM_ID_KEY
    )


# =========================================================
# ADD FLOW
# =========================================================

def start_add(context):
    clear_state(context)

    set_state(
        context,
        STATE_ADD_TITLE
    )

    return STATE_ADD_TITLE


def start_add_icon(context):
    set_state(
        context,
        STATE_ADD_ICON
    )

    return STATE_ADD_ICON


def start_add_action_type(context):
    set_state(
        context,
        STATE_ADD_ACTION_TYPE
    )

    return STATE_ADD_ACTION_TYPE


def start_add_action_value(context):
    set_state(
        context,
        STATE_ADD_ACTION_VALUE
    )

    return STATE_ADD_ACTION_VALUE


def start_add_parent(context):
    set_state(
        context,
        STATE_ADD_PARENT
    )

    return STATE_ADD_PARENT


def start_add_order(context):
    set_state(
        context,
        STATE_ADD_ORDER
    )

    return STATE_ADD_ORDER


# =========================================================
# EDIT FLOW
# =========================================================

def start_edit(context, item_id):
    clear_state(context)

    set_item_id(
        context,
        item_id
    )

    set_state(
        context,
        STATE_EDIT_TITLE
    )

    return STATE_EDIT_TITLE


def start_edit_icon(context):
    set_state(
        context,
        STATE_EDIT_ICON
    )

    return STATE_EDIT_ICON


def start_edit_action_type(context):
    set_state(
        context,
        STATE_EDIT_ACTION_TYPE
    )

    return STATE_EDIT_ACTION_TYPE


def start_edit_action_value(context):
    set_state(
        context,
        STATE_EDIT_ACTION_VALUE
    )

    return STATE_EDIT_ACTION_VALUE


def start_edit_parent(context):
    set_state(
        context,
        STATE_EDIT_PARENT
    )

    return STATE_EDIT_PARENT


def start_edit_order(context):
    set_state(
        context,
        STATE_EDIT_ORDER
    )

    return STATE_EDIT_ORDER


# =========================================================
# DELETE FLOW
# =========================================================

def start_delete(context, item_id):
    clear_state(context)

    set_item_id(
        context,
        item_id
    )

    set_state(
        context,
        STATE_DELETE_CONFIRM
    )

    return STATE_DELETE_CONFIRM


# =========================================================
# FLOW CHECKS
# =========================================================

def is_add_state(context):
    return get_state(context).startswith("add_")


def is_edit_state(context):
    return get_state(context).startswith("edit_")


def is_delete_state(context):
    return get_state(context) == STATE_DELETE_CONFIRM


def is_title_state(context):
    return get_state(context) in (
        STATE_ADD_TITLE,
        STATE_EDIT_TITLE,
    )


def is_icon_state(context):
    return get_state(context) in (
        STATE_ADD_ICON,
        STATE_EDIT_ICON,
    )


def is_action_type_state(context):
    return get_state(context) in (
        STATE_ADD_ACTION_TYPE,
        STATE_EDIT_ACTION_TYPE,
    )


def is_action_value_state(context):
    return get_state(context) in (
        STATE_ADD_ACTION_VALUE,
        STATE_EDIT_ACTION_VALUE,
    )


def is_parent_state(context):
    return get_state(context) in (
        STATE_ADD_PARENT,
        STATE_EDIT_PARENT,
    )


def is_order_state(context):
    return get_state(context) in (
        STATE_ADD_ORDER,
        STATE_EDIT_ORDER,
    )


# =========================================================
# STATE TRANSITIONS
# =========================================================

ADD_STATES = [
    STATE_ADD_TITLE,
    STATE_ADD_ICON,
    STATE_ADD_ACTION_TYPE,
    STATE_ADD_ACTION_VALUE,
    STATE_ADD_PARENT,
    STATE_ADD_ORDER,
]


EDIT_STATES = [
    STATE_EDIT_TITLE,
    STATE_EDIT_ICON,
    STATE_EDIT_ACTION_TYPE,
    STATE_EDIT_ACTION_VALUE,
    STATE_EDIT_PARENT,
    STATE_EDIT_ORDER,
]


def get_next_add_state(state):
    if state not in ADD_STATES:
        return None

    index = ADD_STATES.index(state)

    if index + 1 >= len(ADD_STATES):
        return None

    return ADD_STATES[index + 1]


def get_next_edit_state(state):
    if state not in EDIT_STATES:
        return None

    index = EDIT_STATES.index(state)

    if index + 1 >= len(EDIT_STATES):
        return None

    return EDIT_STATES[index + 1]


def move_to_next_state(context):
    current = get_state(context)

    if current in ADD_STATES:
        next_state = get_next_add_state(current)

    elif current in EDIT_STATES:
        next_state = get_next_edit_state(current)

    else:
        next_state = None

    if next_state:
        set_state(
            context,
            next_state
        )

    return next_state


# =========================================================
# DATA RESET
# =========================================================

def reset_data(context):
    context.user_data[DATA_KEY] = {}


def reset_keep_item(context):
    item_id = get_item_id(context)

    context.user_data.pop(
        STATE_KEY,
        None
    )

    context.user_data.pop(
        DATA_KEY,
        None
    )

    if item_id is not None:
        context.user_data[ITEM_ID_KEY] = item_id
    else:
        context.user_data.pop(
            ITEM_ID_KEY,
            None
        )


# =========================================================
# SNAPSHOT
# =========================================================

def get_state_snapshot(context):
    return {
        "state": get_state(context),
        "item_id": get_item_id(context),
        "data": dict(get_data(context)),
        "active": is_active(context),
    }


# =========================================================
# VALIDATION
# =========================================================

def valid_state(state):
    return (
        state == STATE_NONE
        or state in ADD_STATES
        or state in EDIT_STATES
        or state == STATE_DELETE_CONFIRM
    )


def set_safe_state(context, state):
    if not valid_state(state):
        raise ValueError(
            f"Invalid menu state: {state}"
        )

    set_state(
        context,
        state
    )

    return state


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "STATE_NONE",

    "STATE_ADD_TITLE",
    "STATE_ADD_ICON",
    "STATE_ADD_ACTION_TYPE",
    "STATE_ADD_ACTION_VALUE",
    "STATE_ADD_PARENT",
    "STATE_ADD_ORDER",

    "STATE_EDIT_TITLE",
    "STATE_EDIT_ICON",
    "STATE_EDIT_ACTION_TYPE",
    "STATE_EDIT_ACTION_VALUE",
    "STATE_EDIT_PARENT",
    "STATE_EDIT_ORDER",

    "STATE_DELETE_CONFIRM",

    "get_state",
    "set_state",
    "clear_state",
    "is_active",

    "get_data",
    "set_data",
    "get_data_value",
    "remove_data",

    "set_item_id",
    "get_item_id",

    "start_add",
    "start_add_icon",
    "start_add_action_type",
    "start_add_action_value",
    "start_add_parent",
    "start_add_order",

    "start_edit",
    "start_edit_icon",
    "start_edit_action_type",
    "start_edit_action_value",
    "start_edit_parent",
    "start_edit_order",

    "start_delete",

    "is_add_state",
    "is_edit_state",
    "is_delete_state",
    "is_title_state",
    "is_icon_state",
    "is_action_type_state",
    "is_action_value_state",
    "is_parent_state",
    "is_order_state",

    "get_next_add_state",
    "get_next_edit_state",
    "move_to_next_state",

    "reset_data",
    "reset_keep_item",

    "get_state_snapshot",

    "valid_state",
    "set_safe_state",
]
