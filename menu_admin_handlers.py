# =========================
# MENU ADMIN HANDLERS
# =========================

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from menu_permissions import (
    can_manage_menu,
    can_create_menu_item,
    can_edit_menu_item,
    can_delete_menu_item,
    can_toggle_menu_item,
    can_move_menu_item,
)

from menu_admin_service import (
    admin_create_menu_item,
    admin_update_menu_item,
    admin_delete_menu_item,
    admin_toggle_menu_item,
    admin_move_menu_item_up,
    admin_move_menu_item_down,
    admin_get_menu_item,
    admin_get_menu_items,
    admin_validate_menu,
    admin_repair_menu,
)

from admin_menu_ui import (
    build_admin_menu_ui,
    build_item_ui,
    build_delete_confirm_ui,
    build_action_type_ui,
    build_add_help,
    build_edit_help,
)

from menu_controller import (
    start_add_flow,
    save_add_title,
    save_add_icon,
    save_add_action_type,
    save_add_action_value,
    save_add_parent,
    save_add_order,
    finalize_add,
    start_edit_flow,
    save_edit_title,
    save_edit_icon,
    save_edit_action_type,
    save_edit_action_value,
    save_edit_parent,
    save_edit_order,
    finalize_edit,
    cancel_flow,
)

from menu_state_manager import (
    get_state,
    get_item_id,
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
)


def _user_id(update):
    return update.effective_user.id if update.effective_user else None


def _is_allowed(update):
    user_id = _user_id(update)
    return user_id is not None and can_manage_menu(user_id)


async def _deny(update):
    query = update.callback_query

    if query:
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
    elif update.message:
        await update.message.reply_text(
            "⛔ شما اجازه مدیریت منو را ندارید."
        )


async def _edit(query, text, reply_markup=None):
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )
    except Exception:
        pass


async def admin_menu_manager_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    result = admin_get_menu_items(_user_id(update))

    if not result.get("success"):
        await _edit(
            query,
            result.get("message", "❌ خطا."),
        )
        return

    await _edit(
        query,
        "🎛 مدیریت منوی کاربران\n\n"
        "از گزینه‌های زیر برای مدیریت منوی ربات استفاده کنید:",
        build_admin_menu_ui(),
    )


async def admin_menu_item_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = admin_get_menu_item(_user_id(update), item_id)

    if not result.get("success"):
        await query.answer(
            result.get("message", "❌ آیتم پیدا نشد."),
            show_alert=True,
        )
        return

    item = result["item"]

    await _edit(
        query,
        (
            "🎛 مدیریت آیتم\n\n"
            f"🆔 شناسه: {item.get('id')}\n"
            f"📝 عنوان: {item.get('title', '')}\n"
            f"🔘 آیکون: {item.get('icon', '') or '—'}\n"
            f"⚙️ نوع: {item.get('action_type', '')}\n"
            f"🎯 مقدار: {item.get('action_value', '') or '—'}\n"
            f"📂 والد: {item.get('parent_id') or 'اصلی'}\n"
            f"🔢 ترتیب: {item.get('sort_order', 0)}\n"
            f"📌 وضعیت: {'فعال' if int(item.get('is_active', 0)) else 'غیرفعال'}"
        ),
        build_item_ui(item_id),
    )


async def admin_menu_add_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    start_add_flow(context)

    await _edit(
        query,
        build_add_help(),
    )


async def admin_menu_edit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = start_edit_flow(context, item_id)

    if not result.get("success"):
        await query.answer(
            result.get("message", "❌ خطا."),
            show_alert=True,
        )
        return

    await _edit(
        query,
        build_edit_help(item_id),
    )


async def admin_menu_delete_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    if not can_delete_menu_item(_user_id(update), item_id):
        await _deny(update)
        return

    await _edit(
        query,
        "⚠️ حذف آیتم\n\n"
        "آیا مطمئن هستید که می‌خواهید این آیتم حذف شود؟",
        build_delete_confirm_ui(item_id),
    )


async def admin_menu_delete_confirm_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = admin_delete_menu_item(
        _user_id(update),
        item_id,
    )

    await _edit(
        query,
        result.get(
            "message",
            "✅ عملیات انجام شد.",
        ),
        build_admin_menu_ui(),
    )


async def admin_menu_toggle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = admin_toggle_menu_item(
        _user_id(update),
        item_id,
    )

    await query.answer(
        result.get(
            "message",
            "✅ وضعیت تغییر کرد.",
        ),
        show_alert=True,
    )

    await admin_menu_item_callback(update, context)


async def admin_menu_up_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = admin_move_menu_item_up(
        _user_id(update),
        item_id,
    )

    await query.answer(
        result.get(
            "message",
            "⬆️ ترتیب تغییر کرد.",
        ),
        show_alert=True,
    )

    await admin_menu_item_callback(update, context)


async def admin_menu_down_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    try:
        item_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("❌ آیتم نامعتبر است.", show_alert=True)
        return

    result = admin_move_menu_item_down(
        _user_id(update),
        item_id,
    )

    await query.answer(
        result.get(
            "message",
            "⬇️ ترتیب تغییر کرد.",
        ),
        show_alert=True,
    )

    await admin_menu_item_callback(update, context)


async def admin_menu_action_type_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    await _edit(
        query,
        "⚙️ نوع عملکرد دکمه را انتخاب کنید:",
        build_action_type_ui(),
    )


async def admin_menu_back_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    cancel_flow(context)

    await _edit(
        query,
        "🎛 مدیریت منوی کاربران\n\n"
        "از گزینه‌های زیر انتخاب کنید:",
        build_admin_menu_ui(),
    )


async def admin_menu_validation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not _is_allowed(update):
        await _deny(update)
        return

    await query.answer()

    result = admin_validate_menu(_user_id(update))

    if not result.get("success"):
        await _edit(
            query,
            result.get("message", "❌ خطا."),
        )
        return

    status = "✅ سالم" if result.get("healthy") else "⚠️ دارای مشکل"

    await _edit(
        query,
        f"
