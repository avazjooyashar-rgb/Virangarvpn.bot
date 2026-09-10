# =========================================================
# VIRANGAR VPN
# ADMIN MENU UI
# =========================================================
#
# رابط تلگرامی مدیریت منوی کاربران
# اتصال نهایی به bot.py در مرحله Integration انجام می‌شود.
# =========================================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from admin_menu_manager import (
    ACTION_TYPES,
    get_admin_menu_items,
    get_item_details,
    create_menu_item,
    edit_menu_item,
    remove_menu_item,
    toggle_item,
    move_item_up,
    move_item_down,
    get_menu_summary,
)


# =========================================================
# CALLBACK PREFIXES
# =========================================================

PREFIX_MENU = "amu_menu"
PREFIX_ADD = "amu_add"
PREFIX_EDIT = "amu_edit"
PREFIX_DELETE = "amu_delete"
PREFIX_TOGGLE = "amu_toggle"
PREFIX_UP = "amu_up"
PREFIX_DOWN = "amu_down"
PREFIX_BACK = "amu_back"


# =========================================================
# CALLBACK BUILDERS
# =========================================================

def cb_menu():
    return PREFIX_MENU


def cb_add():
    return PREFIX_ADD


def cb_edit(item_id):
    return f"{PREFIX_EDIT}_{item_id}"


def cb_delete(item_id):
    return f"{PREFIX_DELETE}_{item_id}"


def cb_toggle(item_id):
    return f"{PREFIX_TOGGLE}_{item_id}"


def cb_up(item_id):
    return f"{PREFIX_UP}_{item_id}"


def cb_down(item_id):
    return f"{PREFIX_DOWN}_{item_id}"


def cb_back():
    return PREFIX_BACK


# =========================================================
# MAIN ADMIN MENU MANAGER
# =========================================================

def build_admin_menu_ui():
    summary = get_menu_summary()

    text = (
        "🎛 <b>مدیریت منوی کاربران</b>\n\n"
        f"📊 تعداد کل: <b>{summary['total']}</b>\n"
        f"🟢 فعال: <b>{summary['active']}</b>\n"
        f"🔴 غیرفعال: <b>{summary['disabled']}</b>\n"
        f"📌 اصلی: <b>{summary['main']}</b>\n"
        f"📂 زیرمنو: <b>{summary['submenu']}</b>\n\n"
        "👇 عملیات موردنظر را انتخاب کنید:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ افزودن دکمه",
                callback_data=cb_add()
            )
        ]
    ]

    items = get_admin_menu_items()

    for item in items:
        icon = item.get("icon") or "🔘"
        title = item.get("title") or "بدون عنوان"

        status = "🟢" if item.get("is_active") else "🔴"

        keyboard.append([
            InlineKeyboardButton(
                f"{status} {icon} {title}",
                callback_data=f"{PREFIX_MENU}_{item['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔄 بروزرسانی",
            callback_data=cb_menu()
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "🏠 بازگشت",
            callback_data=cb_back()
        )
    ])

    return text, InlineKeyboardMarkup(keyboard)


# =========================================================
# ITEM MANAGEMENT UI
# =========================================================

def build_item_ui(item_id):
    item = get_item_details(item_id)

    if not item:
        return (
            "❌ این دکمه پیدا نشد.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data=cb_menu()
                    )
                ]
            ])
        )

    icon = item["icon"] or "🔘"
    title = item["title"] or "-"

    status = "🟢 فعال" if item["is_active"] else "🔴 غیرفعال"

    action_name = ACTION_TYPES.get(
        item["action_type"],
        item["action_type"]
    )

    text = (
        f"🎛 <b>مدیریت دکمه</b>\n\n"
        f"🔘 عنوان: <b>{icon} {title}</b>\n"
        f"🆔 شناسه: <code>{item['id']}</code>\n"
        f"📌 ترتیب: <b>{item['sort_order']}</b>\n"
        f"📂 والد: <code>{item['parent_id'] or 'اصلی'}</code>\n"
        f"📡 نوع: <b>{action_name}</b>\n"
        f"⚡ وضعیت: <b>{status}</b>\n"
    )

    if item["action_value"]:
        text += (
            f"🔗 مقدار عملیات:\n"
            f"<code>{item['action_value']}</code>\n"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=cb_edit(item_id)
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 فعال / غیرفعال",
                callback_data=cb_toggle(item_id)
            )
        ],
        [
            InlineKeyboardButton(
                "⬆️ بالا",
                callback_data=cb_up(item_id)
            ),
            InlineKeyboardButton(
                "⬇️ پایین",
                callback_data=cb_down(item_id)
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف",
                callback_data=cb_delete(item_id)
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=cb_menu()
            )
        ]
    ]

    return text, InlineKeyboardMarkup(keyboard)


# =========================================================
# DELETE CONFIRMATION
# =========================================================

def build_delete_confirm_ui(item_id):
    item = get_item_details(item_id)

    if not item:
        return (
            "❌ دکمه پیدا نشد.",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data=cb_menu()
                    )
                ]
            ])
        )

    icon = item["icon"] or "🔘"
    title = item["title"] or "-"

    text = (
        "⚠️ <b>تأیید حذف</b>\n\n"
        f"آیا مطمئن هستید که می‌خواهید:\n\n"
        f"<b>{icon} {title}</b>\n\n"
        "را حذف کنید؟\n\n"
        "❗ این عملیات قابل برگشت نیست."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ بله، حذف شود",
                callback_data=f"{PREFIX_DELETE}_confirm_{item_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ انصراف",
                callback_data=f"{PREFIX_MENU}_{item_id}"
            )
        ]
    ]

    return text, InlineKeyboardMarkup(keyboard)


# =========================================================
# ACTION TYPE UI
# =========================================================

def build_action_type_ui():
    text = (
        "📡 <b>نوع عملیات دکمه</b>\n\n"
        "نوع عملکرد این دکمه را انتخاب کنید:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔘 دکمه داخلی",
                callback_data="amu_action_callback"
            )
        ],
        [
            InlineKeyboardButton(
                "🔗 لینک",
                callback_data="amu_action_url"
            )
        ],
        [
            InlineKeyboardButton(
                "📂 زیرمنو",
                callback_data="amu_action_submenu"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ انصراف",
                callback_data=cb_menu()
            )
        ]
    ]

    return text, InlineKeyboardMarkup(keyboard)


# =========================================================
# ADD MENU HELP
# =========================================================

def build_add_help():
    return (
        "➕ <b>افزودن دکمه جدید</b>\n\n"
        "برای ساخت دکمه جدید اطلاعات زیر لازم است:\n\n"
        "1️⃣ عنوان دکمه\n"
        "2️⃣ آیکون\n"
        "3️⃣ نوع عملیات\n"
        "4️⃣ مقدار عملیات\n"
        "5️⃣ محل قرارگیری\n\n"
        "مثال:\n"
        "🛒 خرید VPN\n"
        "🔘 دکمه داخلی\n"
        "buy_vpn"
    )


# =========================================================
# EDIT HELP
# =========================================================

def build_edit_help(item_id):
    item = get_item_details(item_id)

    if not item:
        return "❌ دکمه پیدا نشد."

    icon = item["icon"] or "🔘"
    title = item["title"] or "-"

    return (
        "✏️ <b>ویرایش دکمه</b>\n\n"
        f"دکمه فعلی:\n"
        f"<b>{icon} {title}</b>\n\n"
        "می‌توانید عنوان، آیکون، نوع عملیات، "
        "مقدار عملیات و ترتیب را تغییر دهید."
    )


# =========================================================
# QUICK ACTIONS
# =========================================================

def perform_toggle(item_id):
    return toggle_item(item_id)


def perform_delete(item_id):
    return remove_menu_item(item_id)


def perform_move_up(item_id):
    return move_item_up(item_id)


def perform_move_down(item_id):
    return move_item_down(item_id)


# =========================================================
# STATUS TEXT
# =========================================================

def operation_result_text(operation, success=True):
    if success:
        messages = {
            "add": "✅ دکمه با موفقیت ساخته شد.",
            "edit": "✅ دکمه با موفقیت ویرایش شد.",
            "delete": "🗑 دکمه با موفقیت حذف شد.",
            "toggle": "🔄 وضعیت دکمه تغییر کرد.",
            "up": "⬆️ دکمه جابه‌جا شد.",
            "down": "⬇️ دکمه جابه‌جا شد.",
        }
        return messages.get(operation, "✅ عملیات با موفقیت انجام شد.")

    return "❌ انجام عملیات ناموفق بود."


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "build_admin_menu_ui",
    "build_item_ui",
    "build_delete_confirm_ui",
    "build_action_type_ui",
    "build_add_help",
    "build_edit_help",
    "perform_toggle",
    "perform_delete",
    "perform_move_up",
    "perform_move_down",
    "operation_result_text",
]
