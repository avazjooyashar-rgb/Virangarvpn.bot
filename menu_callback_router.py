# ============================================
# MENU CALLBACK ROUTER
# ============================================

import re


# ============================================
# CALLBACK PREFIXES
# ============================================

CALLBACK_PREFIXES = {
    "menu": "amu_menu",
    "add": "amu_add",
    "edit": "amu_edit",
    "delete": "amu_delete",
    "delete_confirm": "amu_delete_confirm",
    "toggle": "amu_toggle",
    "up": "amu_up",
    "down": "amu_down",
    "action_type": "amu_action_type",
    "back": "amu_back",
}


# ============================================
# ID EXTRACTOR
# ============================================

def extract_item_id(callback_data: str):
    """
    Extract numeric item ID from callback data.

    Examples:
        amu_edit_12          -> 12
        amu_delete_5        -> 5
        amu_toggle_8        -> 8
        amu_up_3            -> 3
    """

    if not callback_data:
        return None

    match = re.search(r"_(\d+)$", callback_data)

    if not match:
        return None

    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


# ============================================
# CALLBACK TYPE
# ============================================

def get_callback_type(callback_data: str):
    """
    Return logical callback type.
    """

    if not callback_data:
        return None

    if callback_data == CALLBACK_PREFIXES["menu"]:
        return "menu"

    if callback_data == CALLBACK_PREFIXES["add"]:
        return "add"

    if callback_data == CALLBACK_PREFIXES["action_type"]:
        return "action_type"

    if callback_data == CALLBACK_PREFIXES["back"]:
        return "back"

    if callback_data.startswith(
        CALLBACK_PREFIXES["delete_confirm"] + "_"
    ):
        return "delete_confirm"

    if callback_data.startswith(
        CALLBACK_PREFIXES["edit"] + "_"
    ):
        return "edit"

    if callback_data.startswith(
        CALLBACK_PREFIXES["delete"] + "_"
    ):
        return "delete"

    if callback_data.startswith(
        CALLBACK_PREFIXES["toggle"] + "_"
    ):
        return "toggle"

    if callback_data.startswith(
        CALLBACK_PREFIXES["up"] + "_"
    ):
        return "up"

    if callback_data.startswith(
        CALLBACK_PREFIXES["down"] + "_"
    ):
        return "down"

    return None


# ============================================
# CALLBACK VALIDATION
# ============================================

def is_menu_callback(callback_data: str) -> bool:
    """
    Check whether callback belongs to menu system.
    """

    return get_callback_type(callback_data) is not None


def is_item_callback(callback_data: str) -> bool:
    """
    Check whether callback contains an item ID.
    """

    callback_type = get_callback_type(callback_data)

    return callback_type in {
        "edit",
        "delete",
        "delete_confirm",
        "toggle",
        "up",
        "down",
    }


# ============================================
# ROUTE INFO
# ============================================

def parse_callback(callback_data: str) -> dict:
    """
    Convert callback data into structured information.

    Example:
        amu_edit_15

    Returns:
        {
            "type": "edit",
            "item_id": 15,
            "valid": True
        }
    """

    callback_type = get_callback_type(callback_data)
    item_id = extract_item_id(callback_data)

    return {
        "type": callback_type,
        "item_id": item_id,
        "valid": callback_type is not None,
    }


# ============================================
# CALLBACK BUILDERS
# ============================================

def build_callback(callback_type: str, item_id=None):
    """
    Build callback data safely.
    """

    prefix = CALLBACK_PREFIXES.get(callback_type)

    if not prefix:
        raise ValueError(
            f"Unknown callback type: {callback_type}"
        )

    if item_id is None:
        return prefix

    return f"{prefix}_{int(item_id)}"


# ============================================
# COMMON CALLBACKS
# ============================================

def menu_callback():
    return build_callback("menu")


def add_callback():
    return build_callback("add")


def action_type_callback():
    return build_callback("action_type")


def back_callback():
    return build_callback("back")


def edit_callback(item_id):
    return build_callback("edit", item_id)


def delete_callback(item_id):
    return build_callback("delete", item_id)


def delete_confirm_callback(item_id):
    return build_callback("delete_confirm", item_id)


def toggle_callback(item_id):
    return build_callback("toggle", item_id)


def up_callback(item_id):
    return build_callback("up", item_id)


def down_callback(item_id):
    return build_callback("down", item_id)


# ============================================
# DEBUG
# ============================================

def debug_callback(callback_data: str) -> str:
    """
    Human-readable callback information.
    """

    data = parse_callback(callback_data)

    return (
        f"callback={callback_data!r}\n"
        f"type={data['type']!r}\n"
        f"item_id={data['item_id']!r}\n"
        f"valid={data['valid']!r}"
    )
