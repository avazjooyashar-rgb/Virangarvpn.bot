# =========================
# MENU RENDERER
# =========================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from menu_service import (
    get_user_menu,
    get_user_submenu,
    get_menu_item_safe,
)


# =========================
# LABEL
# =========================

def build_item_label(item):
    icon = (item.get("icon") or "").strip()
    title = (item.get("title") or "").strip()

    return f"{icon} {title}".strip()


# =========================
# USER MAIN MENU
# =========================

def build_user_menu_keyboard():
    items = get_user_menu()

    rows = []
    current_row = []

    for item in items:
        button = InlineKeyboardButton(
            build_item_label(item),
            callback_data=f"menu_item_{item['id']}",
        )

        current_row.append(button)

        # دو دکمه در هر ردیف
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    return InlineKeyboardMarkup(rows)


# =========================
# USER SUBMENU
# =========================

def build_submenu_keyboard(parent_id):
    items = get_user_submenu(parent_id)

    rows = []
    current_row = []

    for item in items:
        action_type = item.get("action_type")

        # لینک مستقیم
        if action_type == "url":
            button = InlineKeyboardButton(
                build_item_label(item),
                url=item.get("action_value") or "",
            )

        # زیرمنو / callback
        else:
            button = InlineKeyboardButton(
                build_item_label(item),
                callback_data=f"menu_item_{item['id']}",
            )

        current_row.append(button)

        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    # دکمه برگشت
    rows.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="menu_back",
        )
    ])

    return InlineKeyboardMarkup(rows)


# =========================
# SINGLE ITEM
# =========================

def build_item_keyboard(item_id):
    item = get_menu_item_safe(item_id)

    if not item:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="menu_back",
                )
            ]
        ])

    action_type = item.get("action_type")

    # لینک
    if action_type == "url":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    build_item_label(item),
                    url=item.get("action_value") or "",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="menu_back",
                )
            ]
        ])

    # زیرمنو
    if action_type == "submenu":
        return build_submenu_keyboard(item_id)

    # callback
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="menu_back",
            )
        ]
    ])


# =========================
# ADMIN MENU PREVIEW
# =========================

def build_admin_preview_keyboard():
    items = get_user_menu()

    rows = []

    for item in items:
        rows.append([
            InlineKeyboardButton(
                build_item_label(item),
                callback_data=f"menu_item_{item['id']}",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="amu_back",
        )
    ])

    return InlineKeyboardMarkup(rows)


# =========================
# EMPTY MENU
# =========================

def build_empty_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 بروزرسانی",
                callback_data="menu_back",
            )
        ]
    ])
