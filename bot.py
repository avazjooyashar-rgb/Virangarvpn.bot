import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, add_user, get_stats, get_all_users


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="users"),
        ],
        [
            InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    add_user(user)

    await update.message.reply_text(
        "🔥 به VirangarVPN خوش آمدید!\n\n"
        "🚀 سرویس سریع و پایدار\n"
        "🔐 مدیریت آسان سرویس\n"
        "💎 پشتیبانی اختصاصی\n\n"
        "برای شروع از منوی ربات استفاده کنید."
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    await update.message.reply_text(
        "👑 پنل مدیریت VirangarVPN\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu(),
    )


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.answer("⛔ دسترسی غیرمجاز.", show_alert=True)
        return

    if query.data == "stats":
        stats = get_stats()

        text = (
            "╔════════════════════╗\n"
            "       📊 آمار ربات\n"
            "╚════════════════════╝\n\n"
            f"👥 کل کاربران: {stats['total']}\n"
            f"🟢 کاربران فعال: {stats['active']}\n"
            f"🆕 کاربران امروز: {stats['today']}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🤖 وضعیت ربات: 🟢 ONLINE"
        )

        await query.edit_message_text(
            text,
            reply_markup=admin_menu(),
        )

    elif query.data == "users":
        users = get_all_users()

        await query.edit_message_text(
            "👥 مدیریت کاربران\n\n"
            f"🟢 کاربران قابل دسترسی: {len(users)}\n\n"
            "بخش مدیریت کاربران در نسخه بعدی توسعه داده می‌شود.",
            reply_markup=admin_menu(),
        )

    elif query.data == "broadcast":
        context.user_data["broadcast_mode"] = True

        await query.edit_message_text(
            "📢 پیام همگانی\n\n"
            "پیامی که می‌خواهی برای کاربران ارسال شود را "
            "در پیام بعدی بفرست.\n\n"
            "برای لغو، /cancel را بزن."
        )


async def receive_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return

    if not context.user_data.get("broadcast_mode"):
        return

    context.user_data["broadcast_mode"] = False

    users = get_all_users()

    sent = 0
    failed = 0

    status_message = await update.message.reply_text(
        "📤 ارسال پیام شروع شد...\n\n"
        f"👥 گیرندگان: {len(users)}\n"
        "⏳ لطفاً صبر کنید..."
    )

    for target_id in users:
        try:
            await update.message.copy(chat_id=target_id)
            sent += 1

        except Exception as error:
            failed += 1
            logger.warning(
                "Broadcast failed for %s: %s",
                target_id,
                error,
            )

    await status_message.edit_text(
        "╔════════════════════╗\n"
        "      📢 گزارش ارسال\n"
        "╚════════════════════╝\n\n"
        f"👥 کل: {len(users)}\n"
        f"✅ موفق: {sent}\n"
        f"❌ ناموفق: {failed}\n\n"
        "🏁 ارسال به پایان رسید."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_mode"] = False

    await update.message.reply_text(
        "❌ عملیات لغو شد."
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Unhandled exception:",
        exc_info=context.error,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN داخل فایل .env تنظیم نشده است."
        )

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("admin", admin)
    )

    application.add_handler(
        CommandHandler("cancel", cancel)
    )

    application.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            receive_broadcast,
        )
    )

    application.add_error_handler(error_handler)

    logger.info("🔥 VirangarVPN Bot started.")

    application.run_polling()


if __name__ == "__main__":
    main()
