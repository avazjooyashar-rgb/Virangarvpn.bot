from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "➕ افزودن ادمین جدید",
            callback_data="admin_add",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🛡 تعیین نقش ادمین‌ها",
            callback_data="admin_admin_roles",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "👮 مدیریت ادمین‌ها",
            callback_data="admin_admins",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت به مدیریت",
            callback_data="admin_dashboard",
        )
    )

    return keyboard


def admin_item_keyboard(
    admin_id: int,
) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "⚙️ مدیریت ادمین",
            callback_data=f"admin_status_manage:{admin_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🛡 تغییر نقش",
            callback_data=f"admin_role_manage:{admin_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_admins",
        )
    )

    return keyboard
