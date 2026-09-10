# =========================================================
# VIRANGAR VPN
# ADMIN MENU MANAGER
# =========================================================
#
# پنل مدیریت منوی کاربر برای سوپر ادمین
#
# این فایل فعلاً فقط منطق و ساخت دکمه‌های پنل مدیریت را
# آماده می‌کند.
#
# اتصال به callback های bot.py در مرحله بعد انجام می‌شود.
# =========================================================

from user_menu_manager import (
    get_all_menu_items,
    get_menu_item,
    add_menu_item,
    update_menu_item,
    delete_menu_item,
    toggle_menu_item,
    move_menu_item_up,
    move_menu_item_down,
)


# =========================================================
# CONSTANTS
# =========================================================

ACTION_TYPES = {
    "callback": "🔘 دکمه داخلی",
    "url": "🔗 لینک",
    "submenu": "📂 زیرمنو",
}


# =========================================================
# HELPERS
# =========================================================

def format_status(item):
    return "🟢 فعال" if item.get("is_active") else "🔴 غیرفعال"


def format_action_type(item):
    return ACTION_TYPES.get(
        item.get("action_type"),
        item.get("action_type") or "-"
    )


def format_menu_item(item):
    icon = item.get("icon") or "🔘"
    title = item.get("title") or "-"
    status = format_status(item)
    action_type = format_action_type(item)

    return (
        f"{icon} {title}\n"
        f"   🆔 ID: {item['id']} | "
        f"📌 ترتیب: {item.get('sort_order', 0)}\n"
        f"   {status} | {action_type}"
    )


# =========================================================
# MENU LIST
# =========================================================

def get_admin_menu_items():
    """
    اطلاعات لازم برای نمایش منوی مدیریت.
    """

    items = get_all_menu_items(include_disabled=True)

    return items


def build_menu_manager_text():
    """
    متن اصلی مدیریت منوی کاربر.
    """

    items = get_admin_menu_items()

    lines = [
        "🎛 مدیریت منوی کاربران",
        "",
        "از این بخش می‌توانید منوی کاربران را بدون تغییر کد مدیریت کنید.",
        "",
    ]

    if not items:
        lines.append("❌ هنوز هیچ دکمه‌ای ساخته نشده است.")
        return "\n".join(lines)

    for item in items:
        lines.append(format_menu_item(item))
        lines.append("")

    return "\n".join(lines)


# =========================================================
# CALLBACK DATA
# =========================================================

def menu_callback(item_id):
    return f"umm_item_{item_id}"


def menu_edit_callback(item_id):
    return f"umm_edit_{item_id}"


def menu_delete_callback(item_id):
    return f"umm_del_{item_id}"


def menu_toggle_callback(item_id):
    return f"umm_toggle_{item_id}"


def menu_up_callback(item_id):
    return f"umm_up_{item_id}"


def menu_down_callback(item_id):
    return f"umm_down_{item_id}"


# =========================================================
# BUTTON DATA
# =========================================================

def get_menu_item_buttons(item_id):
    """
    دکمه‌های مدیریتی مربوط به یک آیتم.
    """

    return [
        {
            "text": "✏️ ویرایش",
            "callback_data": menu_edit_callback(item_id),
        },
        {
            "text": "🗑 حذف",
            "callback_data": menu_delete_callback(item_id),
        },
        {
            "text": "🔄 فعال/غیرفعال",
            "callback_data": menu_toggle_callback(item_id),
        },
        {
            "text": "⬆️ بالا",
            "callback_data": menu_up_callback(item_id),
        },
        {
            "text": "⬇️ پایین",
            "callback_data": menu_down_callback(item_id),
        },
    ]


# =========================================================
# CREATE
# =========================================================

def create_menu_item(
    title,
    icon="",
    action_type="callback",
    action_value="",
    parent_id=None,
    sort_order=None,
):
    """
    ساخت دکمه جدید.
    """

    if not title or not title.strip():
        raise ValueError("عنوان دکمه نمی‌تواند خالی باشد.")

    if action_type not in ACTION_TYPES:
        raise ValueError(
            f"نوع عملیات نامعتبر است: {action_type}"
        )

    if action_type == "submenu":
        action_value = ""

    return add_menu_item(
        title=title.strip(),
        icon=icon.strip() if icon else "",
        action_type=action_type,
        action_value=action_value.strip() if action_value else "",
        parent_id=parent_id,
        sort_order=sort_order,
        is_active=True,
    )


# =========================================================
# EDIT
# =========================================================

def edit_menu_item(
    item_id,
    title=None,
    icon=None,
    action_type=None,
    action_value=None,
    parent_id=None,
    sort_order=None,
):
    """
    ویرایش دکمه.
    """

    item = get_menu_item(item_id)

    if not item:
        return False

    if title is not None:
        title = title.strip()

        if not title:
            raise ValueError(
                "عنوان دکمه نمی‌تواند خالی باشد."
            )

    if action_type is not None:
        if action_type not in ACTION_TYPES:
            raise ValueError(
                f"نوع عملیات نامعتبر است: {action_type}"
            )

    if action_value is not None:
        action_value = action_value.strip()

    return update_menu_item(
        item_id=item_id,
        title=title,
        icon=icon,
        action_type=action_type,
        action_value=action_value,
        parent_id=parent_id,
        sort_order=sort_order,
    )


# =========================================================
# DELETE
# =========================================================

def remove_menu_item(item_id):
    """
    حذف دکمه.
    """

    item = get_menu_item(item_id)

    if not item:
        return False

    result = delete_menu_item(item_id)

    return result


# =========================================================
# TOGGLE
# =========================================================

def toggle_item(item_id):
    """
    فعال / غیرفعال کردن دکمه.
    """

    item = get_menu_item(item_id)

    if not item:
        return None

    return toggle_menu_item(item_id)


# =========================================================
# MOVE UP
# =========================================================

def move_item_up(item_id):
    """
    انتقال دکمه به بالا.
    """

    item = get_menu_item(item_id)

    if not item:
        return False

    return move_menu_item_up(item_id)


# =========================================================
# MOVE DOWN
# =========================================================

def move_item_down(item_id):
    """
    انتقال دکمه به پایین.
    """

    item = get_menu_item(item_id)

    if not item:
        return False

    return move_menu_item_down(item_id)


# =========================================================
# ITEM DETAILS
# =========================================================

def get_item_details(item_id):
    """
    اطلاعات کامل یک دکمه برای صفحه ویرایش.
    """

    item = get_menu_item(item_id)

    if not item:
        return None

    return {
        "id": item["id"],
        "title": item.get("title") or "",
        "icon": item.get("icon") or "",
        "action_type": item.get("action_type") or "callback",
        "action_value": item.get("action_value") or "",
        "parent_id": item.get("parent_id"),
        "sort_order": item.get("sort_order", 0),
        "is_active": bool(item.get("is_active")),
    }


# =========================================================
# PREVIEW
# =========================================================

def build_user_menu_preview():
    """
    پیش‌نمایش ساده منوی فعال کاربران.

    خروجی به شکل لیست دکمه‌هاست تا bot.py
    بعداً آن را به InlineKeyboardMarkup تبدیل کند.
    """

    items = get_all_menu_items(
        include_disabled=False
    )

    preview = []

    for item in items:
        icon = item.get("icon") or ""
        title = item.get("title") or ""

        text = f"{icon} {title}".strip()

        preview.append(
            {
                "id": item["id"],
                "text": text,
                "action_type": item.get(
                    "action_type",
                    "callback"
                ),
                "action_value": item.get(
                    "action_value",
                    ""
                ),
                "parent_id": item.get("parent_id"),
                "sort_order": item.get(
                    "sort_order",
                    0
                ),
            }
        )

    return preview


# =========================================================
# SAFETY CHECKS
# =========================================================

def can_delete_item(item_id):
    """
    بررسی وجود آیتم قبل از حذف.
    """

    return get_menu_item(item_id) is not None


def can_edit_item(item_id):
    """
    بررسی وجود آیتم قبل از ویرایش.
    """

    return get_menu_item(item_id) is not None


def can_toggle_item(item_id):
    """
    بررسی وجود آیتم قبل از تغییر وضعیت.
    """

    return get_menu_item(item_id) is not None


# =========================================================
# SUMMARY
# =========================================================

def get_menu_summary():
    """
    خلاصه وضعیت منوی کاربر.
    """

    items = get_all_menu_items(
        include_disabled=True
    )

    total = len(items)

    active = sum(
        1
        for item in items
        if item.get("is_active")
    )

    disabled = total - active

    main_items = sum(
        1
        for item in items
        if item.get("parent_id") is None
    )

    submenu_items = total - main_items

    return {
        "total": total,
        "active": active,
        "disabled": disabled,
        "main": main_items,
        "submenu": submenu_items,
    }
