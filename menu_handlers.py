# ============================================
# MENU HANDLERS
# Dynamic User Menu Management
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from config import SUPER_ADMIN_ID
from bot import is_admin

from admin_menu_ui import (
    build_admin_menu_ui,
    build_item_ui,
    build_delete_confirm_ui,
    build_action_type_ui,
)

from menu_controller import (
    start_add_flow,
    save_add_title,
    save_add_icon,
    save_add_action_type,
    save_add_action_value,
    save_add_parent,
    save_add_order,
    start_edit_flow,
    save_edit_title,
    save_edit_icon,
    save_edit_action_type,
    save_edit_action_value,
    save_edit_parent,
    save_edit_order,
    toggle_menu_item,
    delete_menu_item,
    move_menu_item_up,
    move_menu_item_down,
    get_item_preview,
    cancel_flow,
)

from menu_state_manager import (
    get_state,
    get_item_id,
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
    STATE_DELETE_CONFIRM,
)


# ============================================
# ACCESS
# ============================================

def is_super_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID


def can_manage_menu(user_id: int) -> bool:
    return is_super_admin(user_id)


# ============================================
# SAFE EDIT MESSAGE
# ============================================

async def edit_message(query, text, reply_markup=None):
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )
    except Exception:
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
            )
        except Exception:
            pass


# ============================================
# MAIN MENU MANAGER
# ============================================

async def menu_manager_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await edit_message(
        query,
        "🎛 مدیریت منوی کاربران\n\n"
        "از این بخش می‌توانید دکمه‌های منوی کاربران را مدیریت کنید.",
        build_admin_menu_ui(),
    )


# ============================================
# ITEM SELECT
# ============================================

async def menu_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    result = get_item_preview(item_id)

    if not result:
        await edit_message(
            query,
            "❌ آیتم موردنظر پیدا نشد.",
            build_admin_menu_ui(),
        )
        return

    await edit_message(
        query,
        result,
        build_item_ui(item_id),
    )


# ============================================
# ADD
# ============================================

async def menu_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    start_add_flow(context)

    await edit_message(
        query,
        "➕ افزودن دکمه جدید\n\n"
        "📝 لطفاً نام دکمه را ارسال کنید.\n\n"
        "مثال:\n"
        "🛒 خرید VPN",
    )


# ============================================
# EDIT
# ============================================

async def menu_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    if not start_edit_flow(context, item_id):
        await edit_message(
            query,
            "❌ آیتم پیدا نشد.",
            build_admin_menu_ui(),
        )
        return

    await edit_message(
        query,
        "✏️ ویرایش دکمه\n\n"
        "📝 نام جدید دکمه را ارسال کنید.",
    )


# ============================================
# DELETE
# ============================================

async def menu_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    await edit_message(
        query,
        "⚠️ حذف دکمه\n\n"
        "آیا از حذف این دکمه مطمئن هستید؟",
        build_delete_confirm_ui(item_id),
    )


# ============================================
# DELETE CONFIRM
# ============================================

async def menu_delete_confirm_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    success, message = delete_menu_item(item_id)

    await edit_message(
        query,
        message,
        build_admin_menu_ui(),
    )


# ============================================
# TOGGLE
# ============================================

async def menu_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    success, message = toggle_menu_item(item_id)

    if success:
        await edit_message(
            query,
            message,
            build_item_ui(item_id),
        )
    else:
        await edit_message(
            query,
            message,
            build_admin_menu_ui(),
        )


# ============================================
# MOVE UP
# ============================================

async def menu_up_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    success, message = move_menu_item_up(item_id)

    if success:
        await edit_message(
            query,
            message,
            build_admin_menu_ui(),
        )
    else:
        await edit_message(
            query,
            message,
            build_item_ui(item_id),
        )


# ============================================
# MOVE DOWN
# ============================================

async def menu_down_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except Exception:
        return

    success, message = move_menu_item_down(item_id)

    if success:
        await edit_message(
            query,
            message,
            build_admin_menu_ui(),
        )
    else:
        await edit_message(
            query,
            message,
            build_item_ui(item_id),
        )


# ============================================
# ACTION TYPE
# ============================================

async def menu_action_type_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    await edit_message(
        query,
        "⚙️ نوع عملکرد دکمه را انتخاب کنید:",
        build_action_type_ui(),
    )


# ============================================
# TEXT INPUT
# ============================================

async def menu_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    state = get_state(context)

    if state == STATE_NONE:
        return

    text = update.message.text.strip()

    # ----------------------------------------
    # ADD
    # ----------------------------------------

    if state == STATE_ADD_TITLE:
        result = save_add_title(context, text)

        await update.message.reply_text(
            result or "🎨 آیکون دکمه را ارسال کنید.\n\n"
            "مثال: 🛒"
        )
        return

    if state == STATE_ADD_ICON:
        result = save_add_icon(context, text)

        await update.message.reply_text(
            result or "⚙️ نوع عملکرد را انتخاب کنید:\n\n"
            "callback\n"
            "url\n"
            "submenu"
        )
        return

    if state == STATE_ADD_ACTION_VALUE:
        result = save_add_action_value(context, text)

        await update.message.reply_text(
            result or "📂 شناسه والد را ارسال کنید.\n"
            "اگر زیرمنو نیست، بنویسید: 0"
        )
        return

    if state == STATE_ADD_PARENT:
        result = save_add_parent(context, text)

        await update.message.reply_text(
            result or "🔢 ترتیب نمایش را ارسال کنید.\n"
            "برای خودکار: 0"
        )
        return

    if state == STATE_ADD_ORDER:
        success, message = save_add_order(context, text)

        await update.message.reply_text(message)

        if success:
            await update.message.reply_text(
                "🎛 مدیریت منوی کاربران",
                reply_markup=build_admin_menu_ui(),
            )
        return

    # ----------------------------------------
    # EDIT
    # ----------------------------------------

    if state == STATE_EDIT_TITLE:
        result = save_edit_title(context, text)

        await update.message.reply_text(
            result or "🎨 آیکون جدید را ارسال کنید."
        )
        return

    if state == STATE_EDIT_ICON:
        result = save_edit_icon(context, text)

        await update.message.reply_text(
            result or "⚙️ نوع عملکرد جدید را ارسال کنید."
        )
        return

    if state == STATE_EDIT_ACTION_VALUE:
        result = save_edit_action_value(context, text)

        await update.message.reply_text(
            result or "📂 شناسه والد جدید را ارسال کنید.\n"
            "برای اصلی: 0"
        )
        return

    if state == STATE_EDIT_PARENT:
        result = save_edit_parent(context, text)

        await update.message.reply_text(
            result or "🔢 ترتیب جدید را ارسال کنید.\n"
            "برای خودکار: 0"
        )
        return

    if state == STATE_EDIT_ORDER:
        success, message = save_edit_order(context, text)

        await update.message.reply_text(message)

        if success:
            await update.message.reply_text(
                "🎛 مدیریت منوی کاربران",
                reply_markup=build_admin_menu_ui(),
            )
        return

    # ----------------------------------------
    # DELETE CONFIRM
    # ----------------------------------------

    if state == STATE_DELETE_CONFIRM:
        if text.lower() in ("بله", "yes", "y"):
            item_id = get_item_id(context)

            if item_id:
                success, message = delete_menu_item(item_id)
                cancel_flow(context)

                await update.message.reply_text(
                    message,
                    reply_markup=build_admin_menu_ui(),
                )
            return

        if text.lower() in ("خیر", "نه", "no", "n"):
            cancel_flow(context)

            await update.message.reply_text(
                "❌ حذف لغو شد.",
                reply_markup=build_admin_menu_ui(),
            )
            return


# ============================================
# CANCEL
# ============================================

async def menu_cancel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if not user or not can_manage_menu(user.id):
        return

    cancel_flow(context)

    await edit_message(
        query,
        "❌ عملیات لغو شد.",
        build_admin_menu_ui(),
    )


# ============================================
# REGISTER HANDLERS
# ============================================

def register_menu_handlers(application):
    """
    Register all dynamic menu handlers.

    این تابع فعلاً در bot.py صدا زده نمی‌شود.
    در مرحله اتصال، فقط آن را از bot.py فراخوانی می‌کنیم.
    """

    application.add_handler(
        CallbackQueryHandler(
            menu_manager_callback,
            pattern=r"^amu_menu$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_add_callback,
            pattern=r"^amu_add$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_edit_callback,
            pattern=r"^amu_edit_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_delete_callback,
            pattern=r"^amu_delete_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_delete_confirm_callback,
            pattern=r"^amu_delete_confirm_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_toggle_callback,
            pattern=r"^amu_toggle_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_up_callback,
            pattern=r"^amu_up_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_down_callback,
            pattern=r"^amu_down_\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_action_type_callback,
            pattern=r"^amu_action_type$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_cancel_callback,
            pattern=r"^amu_back$",
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_text_input,
        )
    )

    return application
