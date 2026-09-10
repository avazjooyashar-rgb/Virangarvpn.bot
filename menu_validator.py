# ============================================
# MENU VALIDATOR
# Dynamic User Menu Validation
# ============================================

from user_menu_manager import (
    get_menu_item,
    get_all_menu_items,
)


# ============================================
# LIMITS
# ============================================

MAX_TITLE_LENGTH = 80
MAX_ICON_LENGTH = 10
MAX_ACTION_VALUE_LENGTH = 500
MAX_ORDER = 999999

VALID_ACTION_TYPES = {
    "callback",
    "url",
    "submenu",
}


# ============================================
# TEXT
# ============================================

def validate_title(title):
    if title is None:
        return False, "❌ عنوان وارد نشده است."

    title = str(title).strip()

    if not title:
        return False, "❌ عنوان نمی‌تواند خالی باشد."

    if len(title) > MAX_TITLE_LENGTH:
        return False, (
            f"❌ عنوان بیش از حد طولانی است.\n"
            f"حداکثر: {MAX_TITLE_LENGTH} کاراکتر"
        )

    return True, title


# ============================================
# ICON
# ============================================

def validate_icon(icon):
    if icon is None:
        return True, ""

    icon = str(icon).strip()

    if len(icon) > MAX_ICON_LENGTH:
        return False, (
            f"❌ آیکون نامعتبر است.\n"
            f"حداکثر {MAX_ICON_LENGTH} کاراکتر."
        )

    return True, icon


# ============================================
# ACTION TYPE
# ============================================

def validate_action_type(action_type):
    if action_type is None:
        return False, "❌ نوع عملکرد مشخص نشده است."

    action_type = str(action_type).strip().lower()

    if action_type not in VALID_ACTION_TYPES:
        return False, (
            "❌ نوع عملکرد نامعتبر است.\n\n"
            "انواع مجاز:\n"
            "• callback\n"
            "• url\n"
            "• submenu"
        )

    return True, action_type


# ============================================
# ACTION VALUE
# ============================================

def validate_action_value(action_type, action_value):
    if action_value is None:
        action_value = ""

    action_value = str(action_value).strip()

    if len(action_value) > MAX_ACTION_VALUE_LENGTH:
        return False, (
            f"❌ مقدار عملکرد بیش از حد طولانی است.\n"
            f"حداکثر: {MAX_ACTION_VALUE_LENGTH} کاراکتر"
        )

    if action_type == "url":
        if not action_value:
            return False, "❌ برای لینک باید URL وارد کنید."

        if not (
            action_value.startswith("http://")
            or action_value.startswith("https://")
        ):
            return False, (
                "❌ لینک باید با http:// یا https:// شروع شود."
            )

    elif action_type == "callback":
        if not action_value:
            return False, (
                "❌ برای callback باید مقدار callback را وارد کنید."
            )

    elif action_type == "submenu":
        # برای submenu مقدار action الزامی نیست
        pass

    return True, action_value


# ============================================
# PARENT
# ============================================

def validate_parent_id(parent_id, current_item_id=None):
    if parent_id in (None, "", 0, "0"):
        return True, None

    try:
        parent_id = int(parent_id)
    except (TypeError, ValueError):
        return False, "❌ شناسه والد باید عدد باشد."

    if parent_id <= 0:
        return True, None

    if current_item_id is not None:
        try:
            current_item_id = int(current_item_id)
        except (TypeError, ValueError):
            current_item_id = None

        if current_item_id == parent_id:
            return False, "❌ یک آیتم نمی‌تواند والد خودش باشد."

    parent = get_menu_item(parent_id)

    if not parent:
        return False, "❌ آیتم والد پیدا نشد."

    return True, parent_id


# ============================================
# ORDER
# ============================================

def validate_order(order):
    if order in (None, "", "0"):
        return True, None

    try:
        order = int(order)
    except (TypeError, ValueError):
        return False, "❌ ترتیب باید عدد باشد."

    if order < 0:
        return False, "❌ ترتیب نمی‌تواند منفی باشد."

    if order > MAX_ORDER:
        return False, (
            f"❌ ترتیب بیش از حد بزرگ است.\n"
            f"حداکثر: {MAX_ORDER}"
        )

    return True, order


# ============================================
# ACTIVE
# ============================================

def validate_active(active):
    if isinstance(active, bool):
        return True, int(active)

    if active in (0, 1, "0", "1", True, False):
        return True, int(active)

    return False, "❌ وضعیت فعال/غیرفعال نامعتبر است."


# ============================================
# COMPLETE ITEM
# ============================================

def validate_menu_item(
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
    current_item_id=None,
):
    errors = []

    ok, title_result = validate_title(title)
    if not ok:
        errors.append(title_result)

    ok, icon_result = validate_icon(icon)
    if not ok:
        errors.append(icon_result)

    ok, action_type_result = validate_action_type(action_type)
    if not ok:
        errors.append(action_type_result)
        action_type_clean = "callback"
    else:
        action_type_clean = action_type_result

    ok, action_value_result = validate_action_value(
        action_type_clean,
        action_value,
    )
    if not ok:
        errors.append(action_value_result)

    ok, parent_result = validate_parent_id(
        parent_id,
        current_item_id=current_item_id,
    )
    if not ok:
        errors.append(parent_result)

    ok, order_result = validate_order(sort_order)
    if not ok:
        errors.append(order_result)

    if errors:
        return False, errors

    return True, {
        "title": title_result,
        "icon": icon_result,
        "action_type": action_type_clean,
        "action_value": action_value_result,
        "parent_id": parent_result,
        "sort_order": order_result,
    }


# ============================================
# DUPLICATE TITLE CHECK
# ============================================

def title_exists(title, parent_id=None, exclude_item_id=None):
    if not title:
        return False

    title = str(title).strip().lower()

    items = get_all_menu_items(include_disabled=True)

    for item in items:
        item_id = item.get("id")

        if exclude_item_id is not None and item_id == exclude_item_id:
            continue

        item_title = str(item.get("title") or "").strip().lower()

        item_parent = item.get("parent_id")

        if item_parent == 0:
            item_parent = None

        if parent_id == 0:
            parent_id = None

        if item_title == title and item_parent == parent_id:
            return True

    return False


# ============================================
# CREATE VALIDATION
# ============================================

def validate_create(
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
):
    valid, result = validate_menu_item(
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
    )

    if not valid:
        return False, result

    if title_exists(
        result["title"],
        result["parent_id"],
    ):
        return False, [
            "❌ یک دکمه با همین عنوان در این بخش وجود دارد."
        ]

    return True, result


# ============================================
# EDIT VALIDATION
# ============================================

def validate_edit(
    item_id,
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
):
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return False, ["❌ شناسه آیتم نامعتبر است."]

    item = get_menu_item(item_id)

    if not item:
        return False, ["❌ آیتم موردنظر پیدا نشد."]

    valid, result = validate_menu_item(
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
        current_item_id=item_id,
    )

    if not valid:
        return False, result

    if title_exists(
        result["title"],
        result["parent_id"],
        exclude_item_id=item_id,
    ):
        return False, [
            "❌ یک دکمه با همین عنوان در این بخش وجود دارد."
        ]

    return True, result


# ============================================
# ERROR FORMATTER
# ============================================

def format_validation_errors(errors):
    if not errors:
        return ""

    if isinstance(errors, str):
        errors = [errors]

    return "\n".join(
        f"• {error}"
        for error in errors
        if error
    )


# ============================================
# QUICK CHECKS
# ============================================

def is_valid_title(title):
    valid, _ = validate_title(title)
    return valid


def is_valid_action_type(action_type):
    valid, _ = validate_action_type(action_type)
    return valid


def is_valid_url(url):
    valid, _ = validate_action_value("url", url)
    return valid


def is_valid_parent(parent_id, current_item_id=None):
    valid, _ = validate_parent_id(
        parent_id,
        current_item_id=current_item_id,
    )
    return valid


def is_valid_order(order):
    valid, _ = validate_order(order)
    return valid
