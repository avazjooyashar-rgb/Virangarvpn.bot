import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import RequiredChannel
from app.utils.permissions import is_super_admin


def channel_management_keyboard(channels) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "➕ افزودن کانال",
            callback_data="channel_add",
        )
    )

    for channel in channels:
        status = "🟢" if channel.is_active else "🔴"

        keyboard.add(
            InlineKeyboardButton(
                f"{status} {channel.title}",
                callback_data=f"channel_manage:{channel.id}",
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت به مدیریت",
            callback_data="admin_dashboard",
        )
    )

    return keyboard


def channel_edit_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton(
            "✏️ ویرایش",
            callback_data=f"channel_edit:{channel_id}",
        ),
        InlineKeyboardButton(
            "🗑 حذف",
            callback_data=f"channel_delete:{channel_id}",
        ),
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔄 تغییر وضعیت",
            callback_data=f"channel_toggle:{channel_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_channels",
        )
    )

    return keyboard


def register_channel_action_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_channels"
    )
    def channel_list(call):
        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ دسترسی ندارید.",
                    show_alert=True,
                )
                return

            channels = db.scalars(
                select(RequiredChannel)
                .order_by(RequiredChannel.id)
            ).all()

            if channels:
                text = (
                    "📢 <b>مدیریت کانال‌های اجباری</b>\n\n"
                    "برای مدیریت هر کانال روی آن بزنید:"
                )
            else:
                text = (
                    "📢 <b>مدیریت کانال‌های اجباری</b>\n\n"
                    "هیچ کانال اجباری ثبت نشده است."
                )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=channel_management_keyboard(
                    channels
                ),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "channel_manage:"
        )
    )
    def channel_manage(call):
        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ دسترسی ندارید.",
                    show_alert=True,
                )
                return

            channel_id = int(
                call.data.split(":")[1]
            )

            channel = db.get(
                RequiredChannel,
                channel_id,
            )

            if not channel:
                bot.answer_callback_query(
                    call.id,
                    "❌ کانال پیدا نشد.",
                    show_alert=True,
                )
                return

            status = (
                "🟢 فعال"
                if channel.is_active
                else "🔴 غیرفعال"
            )

            text = (
                "📢 <b>مدیریت کانال</b>\n\n"
                f"🏷 عنوان: <b>{channel.title}</b>\n"
                f"📌 یوزرنیم: <code>{channel.username}</code>\n"
                f"🔗 لینک: {channel.invite_link or 'ثبت نشده'}\n"
                f"📊 وضعیت: {status}\n\n"
                "عملیات موردنظر را انتخاب کنید:"
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=channel_edit_keyboard(
                    channel.id
                ),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "channel_toggle:"
        )
    )
    def channel_toggle(call):
        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ دسترسی ندارید.",
                    show_alert=True,
                )
                return

            channel_id = int(
                call.data.split(":")[1]
            )

            channel = db.get(
                RequiredChannel,
                channel_id,
            )

            if not channel:
                bot.answer_callback_query(
                    call.id,
                    "❌ کانال پیدا نشد.",
                    show_alert=True,
                )
                return

            channel.is_active = not channel.is_active

            db.commit()

            bot.answer_callback_query(
                call.id,
                "✅ وضعیت کانال تغییر کرد.",
            )

            channel_manage(call)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "channel_delete:"
        )
    )
    def channel_delete(call):
        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ دسترسی ندارید.",
                    show_alert=True,
                )
                return

            channel_id = int(
                call.data.split(":")[1]
            )

            channel = db.get(
                RequiredChannel,
                channel_id,
            )

            if not channel:
                bot.answer_callback_query(
                    call.id,
                    "❌ کانال پیدا نشد.",
                    show_alert=True,
                )
                return

            db.delete(channel)
            db.commit()

            bot.answer_callback_query(
                call.id,
                "🗑 کانال حذف شد.",
            )

            channels = db.scalars(
                select(RequiredChannel)
                .order_by(RequiredChannel.id)
            ).all()

            bot.edit_message_text(
                "📢 <b>مدیریت کانال‌های اجباری</b>\n\n"
                "کانال با موفقیت حذف شد.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=channel_management_keyboard(
                    channels
                ),
            )

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data == "channel_add"
    )
    def channel_add(call):
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "➕ <b>افزودن کانال اجباری</b>\n\n"
            "این بخش در مرحله بعد با سیستم دریافت اطلاعات "
            "کانال به‌صورت کامل فعال می‌شود.\n\n"
            "فرمت اطلاعات:\n"
            "<code>عنوان | @username | لینک عضویت</code>",
        )

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "channel_edit:"
        )
    )
    def channel_edit(call):
        bot.answer_callback_query(
            call.id,
            "🚧 ویرایش در مرحله بعد تکمیل می‌شود.",
            show_alert=True,
        )
