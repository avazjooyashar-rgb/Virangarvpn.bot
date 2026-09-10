# =========================
# MENU EVENT HANDLERS
# =========================

from telegram import Update
from telegram.ext import ContextTypes

from menu_permissions import can_manage_menu
from menu_service import (
    get_menu_item_safe,
    get_user_menu,
)
from menu_renderer import (
    build_user_menu_keyboard,
    build_submenu_keyboard,
)
from menu_action_router import route_menu_action


async def handle_menu_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    مدیریت کلیک روی آیتم‌های منوی کاربر.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("menu_item_"):
        return

    try:
        item_id = int(
            data.replace("menu_item_", "", 1)
        )
    except ValueError:
        await show_main_menu(update)
        return

    result = route_menu_action(item_id)

    if not result.get("success"):
        await query.edit_message_text(
            "❌ این گزینه دیگر در دسترس نیست.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    item = result.get("item") or {}
    action_type = result.get("type")

    if not item.get("is_active", 1):
        await query.edit_message_text(
            "⚠️ این گزینه در حال حاضر غیرفعال است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    if action_type == "submenu":
        await show_submenu(
            update,
            item_id,
            item,
        )
        return

    if action_type == "url":
        await show_url_action(
            update,
            item,
        )
        return

    if action_type == "callback":
        await execute_callback_action(
            update,
            context,
            item,
        )
        return

    await query.edit_message_text(
        "❌ نوع عملیات نامعتبر است.",
        reply_markup=build_user_menu_keyboard(),
    )


async def show_submenu(
    update: Update,
    item_id: int,
    item: dict,
):
    """
    نمایش زیرمنوی یک آیتم.
    """

    query = update.callback_query

    if not query:
        return

    title = (
        item.get("title") or
        "زیرمنو"
    )

    keyboard = build_submenu_keyboard(item_id)

    await query.edit_message_text(
        f"📂 {title}\n\n"
        "👇 گزینه موردنظر را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def show_url_action(
    update: Update,
    item: dict,
):
    """
    نمایش دکمه لینک.
    """

    query = update.callback_query

    if not query:
        return

    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )

    title = (
        item.get("title") or
        "لینک"
    )

    url = (
        item.get("action_value") or
        ""
    ).strip()

    if not url:
        await query.edit_message_text(
            "❌ لینک این گزینه تنظیم نشده است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🔗 {title}",
                url=url,
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="menu_back",
            )
        ],
    ])

    await query.edit_message_text(
        f"🔗 {title}\n\n"
        "برای ادامه روی دکمه زیر بزنید:",
        reply_markup=keyboard,
    )


async def execute_callback_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    item: dict,
):
    """
    اجرای عملیات داخلی.

    عملیات واقعی در مرحله اتصال به bot.py
    به این قسمت متصل می‌شود.
    """

    query = update.callback_query

    if not query:
        return

    action_value = (
        item.get("action_value") or
        ""
    ).strip()

    if not action_value:
        await query.edit_message_text(
            "⚙️ این گزینه هنوز تنظیم نشده است.",
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
            "⏳ این بخش هنوز به سیستم اصلی ربات متصل نشده است.",
            reply_markup=build_user_menu_keyboard(),
        )
        return

    try:
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


async def handle_menu_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    بازگشت به منوی اصلی.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await show_main_menu(update)


async def show_main_menu(update: Update):
    """
    نمایش منوی اصلی.
    """

    query = update.callback_query

    keyboard = build_user_menu_keyboard()

    if query:
        await query.edit_message_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
        )
        return

    if update.message:
        await update.message.reply_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
        )


def get_menu_callback_patterns():
    """
    الگوهای CallbackQuery مربوط به منوی کاربر.
    """

    return {
        "item": r"^menu_item_\d+$",
        "back": r"^menu_back$",
    }


def register_menu_event_handlers(application):
    """
    ثبت Handlerهای منوی کاربر.
    """

    from telegram.ext import CallbackQueryHandler

    patterns = get_menu_callback_patterns()

    application.add_handler(
        CallbackQueryHandler(
            handle_menu_item,
            pattern=patterns["item"],
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_menu_back,
            pattern=patterns["back"],
        )
    )


def menu_handler_status():
    """
    وضعیت ماژول.
    """

    return {
        "module": "menu_event_handlers",
        "status": "ready",
        "handlers": [
            "menu_item",
            "menu_back",
        ],
    }
