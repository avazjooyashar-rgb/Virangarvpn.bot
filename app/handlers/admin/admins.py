import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.utils.permissions import is_super_admin


def admins_keyboard(admins) -> InlineKeyboardMarkup:
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

    for admin in admins:
        status = "🟢" if admin.is_active else "🔴"

        keyboard.add(
            InlineKeyboardButton(
                f"{status} {admin.telegram_id} | {admin.role}",
                callback_data=f"admin_status_manage:{admin.id}",
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت به مدیریت",
            callback_data="admin_dashboard",
        )
    )

    return keyboard


def register_admin_management_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_admins"
    )
    def admin_admins(call):

        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ فقط Super Admin به این بخش دسترسی دارد.",
                    show_alert=True,
                )
                return

            admins = db.scalars(
                select(Admin).order_by(Admin.id)
            ).all()

            if admins:
                text = (
                    "👮 <b>مدیریت ادمین‌ها</b>\n\n"
                    "از گزینه‌های زیر استفاده کنید:"
                )
            else:
                text = (
                    "👮 <b>مدیریت ادمین‌ها</b>\n\n"
                    "هنوز ادمینی ثبت نشده است."
                )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admins_keyboard(admins),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()
