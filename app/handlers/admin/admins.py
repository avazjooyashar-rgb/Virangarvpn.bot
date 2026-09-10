import telebot
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin, Role
from app.keyboards.admin import back_to_admin_keyboard
from app.utils.permissions import is_super_admin


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
                select(Admin)
                .order_by(Admin.id)
            ).all()

            if not admins:
                text = (
                    "👮 <b>مدیریت ادمین‌ها</b>\n\n"
                    "هنوز هیچ ادمینی ثبت نشده است."
                )
            else:
                lines = [
                    "👮 <b>مدیریت ادمین‌ها</b>\n"
                ]

                for admin in admins:
                    status = "🟢 فعال" if admin.is_active else "🔴 غیرفعال"

                    lines.append(
                        f"• <code>{admin.telegram_id}</code>\n"
                        f"  نقش: <b>{admin.role}</b>\n"
                        f"  وضعیت: {status}\n"
                    )

                text = "\n".join(lines)

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=back_to_admin_keyboard(),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_users"
    )
    def admin_users_placeholder(call):
        bot.answer_callback_query(
            call.id,
            "🚧 بخش مدیریت کاربران در مرحله بعد فعال می‌شود.",
            show_alert=True,
        )
