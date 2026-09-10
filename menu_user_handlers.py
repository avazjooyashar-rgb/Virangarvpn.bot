# =========================
# MENU USER HANDLERS
# =========================

from telegram import Update
from telegram.ext import ContextTypes

from menu_renderer import (
    build_user_menu_keyboard,
    build_submenu_keyboard,
    build_item_keyboard,
    build_empty_menu_keyboard,
)

from menu_action_router import route_menu_action


async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    نمایش منوی اصلی داینامیک کاربر.
    """

    query = update.callback_query

    if query:
        await query.answer()

        await query.edit_message_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    if update.message:
        await update.message.reply_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=build_user_menu_keyboard(),
        )


async def user_menu_item_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    مدیریت کلیک روی دکمه‌های منوی داینامیک کاربر.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("menu_item_"):
        return

    try:
        item_id = int(data.replace("menu_item_", "", 1))
    except ValueError:
        await query.edit_message_text(
            "❌ شناسه دکمه نامعتبر است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    result = route_menu_action(item_id)

    if not result.get("success"):
        await query.edit_message_text(
            "❌ این گزینه در دسترس نیست.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    action_type = result.get("type")
    item = result.get("item") or {}

    title = item.get("title") or "گزینه انتخاب‌شده"

    if action_type == "submenu":

        await query.edit_message_text(
            f"📂 {title}\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=build_submenu_keyboard(item_id),
        )
        return

    if action_type == "url":

        await query.edit_message_text(
            f"🔗 {title}\n\n"
            "برای ادامه روی دکمه زیر بزنید:",
            reply_markup=build_item_keyboard(item_id),
        )
        return

    if action_type == "callback":

        await handle_internal_callback(
            update,
            context,
            item,
        )
        return

    await query.edit_message_text(
        "❌ نوع عملیات این دکمه پشتیبانی نمی‌شود.",
        reply_markup=build_user_menu_keyboard(),
    )


async def handle_internal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    item: dict,
):
    """
    محل اتصال اکشن‌های داخلی منو به منطق اصلی ربات.

    در مرحله اتصال به bot.py،
    اکشن‌های واقعی مثل خرید، کیف پول، پشتیبانی و...
    از این بخش اجرا خواهند شد.
    """

    query = update.callback_query

    if not query:
        return

    action_value = (
        item.get("action_value") or ""
    ).strip()

    title = (
        item.get("title") or
        "گزینه انتخاب‌شده"
    )

    if not action_value:

        await query.edit_message_text(
            f"⚙️ {title}\n\n"
            "این گزینه هنوز به عملیات اصلی ربات متصل نشده است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    handlers = context.application.bot_data.get(
        "menu_action_handlers",
        {},
    )

    handler = handlers.get(action_value)

    if handler is None:

        await query.edit_message_text(
            f"⚙️ {title}\n\n"
            "این گزینه فعلاً آماده اتصال به بخش اصلی ربات است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    try:

        if callable(handler):
            result = handler(
                update,
                context,
            )

            if hasattr(result, "__await__"):
                await result

    except Exception:

        await query.edit_message_text(
            "❌ هنگام اجرای این گزینه خطایی رخ داد.",
            reply_markup=build_user_menu_keyboard(),
        )


async def user_menu_back_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    بازگشت به منوی اصلی کاربر.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "🔥 منوی اصلی VirangarVPN\n\n"
        "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=build_user_menu_keyboard(),
    )


def register_user_menu_handlers(application):
    """
    ثبت Handlerهای منوی کاربر.
    """

    from telegram.ext import CallbackQueryHandler

    application.add_handler(
        CallbackQueryHandler(
            user_menu_item_callback,
            pattern=r"^menu_item_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            user_menu_back_callback,
            pattern=r"^menu_back$",
        )
    )


def register_menu_action_handler(
    application,
    action_value,
    handler,
):
    """
    ثبت یک عملیات داخلی برای دکمه‌های منوی داینامیک.

    مثال:
    register_menu_action_handler(
        application,
        "buy_vpn",
        buy_vpn_handler,
    )
    """

    if not action_value:
        return False

    if not callable(handler):
        return False

    handlers = application.bot_data.setdefault(
        "menu_action_handlers",
        {},
    )

    handlers[action_value] = handler

    return True


def unregister_menu_action_handler(
    application,
    action_value,
):
    """
    حذف یک عملیات ثبت‌شده.
    """

    handlers = application.bot_data.get(
        "menu_action_handlers",
        {},
    )

    if action_value not in handlers:
        return False

    del handlers[action_value]

    return True


def get_registered_menu_actions(application):
    """
    دریافت لیست عملیات‌های ثبت‌شده.
    """

    handlers = application.bot_data.get(
        "menu_action_handlers",
        {},
    )

    return list(handlers.keys())


def clear_registered_menu_actions(application):
    """
    پاک کردن تمام عملیات‌های ثبت‌شده.
    """

    application.bot_data[
        "menu_action_handlers"
    ] = {}

    return True
