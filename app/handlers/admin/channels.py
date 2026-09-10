import telebot
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import RequiredChannel
from app.keyboards.admin import back_to_admin_keyboard
from app.utils.permissions import is_super_admin


def register_channel_management_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_channels"
    )
    def admin_channels(call):
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

            channels = db.scalars(
                select(RequiredChannel)
                .order_by(RequiredChannel.id)
            ).all()

            if not channels:
                text = (
                    "📢 <b>کانال‌های اجباری</b>\n\n"
                    "هنوز هیچ کانالی ثبت نشده است.\n\n"
                    "در مرحله بعد امکان افزودن کانال را فعال می‌کنیم."
                )
            else:
                lines = [
                    "📢 <b>کانال‌های اجباری</b>\n"
                ]

                for channel in channels:
                    status = (
                        "🟢 فعال"
                        if channel.is_active
                        else "🔴 غیرفعال"
                    )

                    username = channel.username

                    if not username.startswith("@"):
                        username = f"@{username}"

                    lines.append(
                        f"📌 <b>{channel.title}</b>\n"
                        f"├ کانال: {username}\n"
                        f"└ وضعیت: {status}\n"
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
