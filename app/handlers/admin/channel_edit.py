import telebot
from sqlalchemy.orm import Session

from app.database.models import RequiredChannel
from app.utils.permissions import is_super_admin


edit_states = {}


def register_channel_edit_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("channel_edit:")
    )
    def start_edit(call):

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

        finally:
            db.close()

        edit_states[call.from_user.id] = {
            "channel_id": channel_id,
            "step": "title",
        }

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "✏️ <b>ویرایش کانال</b>\n\n"
            "مرحله ۱ از ۳\n\n"
            "🏷 عنوان جدید کانال را ارسال کنید.",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in edit_states
            and edit_states[
                message.from_user.id
            ]["step"] == "title"
        )
    )
    def receive_title(message):

        user_id = message.from_user.id

        title = message.text.strip()

        if not title:
            bot.send_message(
                message.chat.id,
                "❌ عنوان نمی‌تواند خالی باشد.",
            )
            return

        edit_states[user_id]["title"] = title
        edit_states[user_id]["step"] = "username"

        bot.send_message(
            message.chat.id,
            "مرحله ۲ از ۳\n\n"
            "📌 یوزرنیم جدید کانال را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>@VirangarVPN</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in edit_states
            and edit_states[
                message.from_user.id
            ]["step"] == "username"
        )
    )
    def receive_username(message):

        user_id = message.from_user.id

        username = message.text.strip()

        if not username.startswith("@"):
            username = f"@{username}"

        if len(username) < 2:
            bot.send_message(
                message.chat.id,
                "❌ یوزرنیم معتبر نیست.",
            )
            return

        edit_states[user_id]["username"] = username
        edit_states[user_id]["step"] = "invite_link"

        bot.send_message(
            message.chat.id,
            "مرحله ۳ از ۳\n\n"
            "🔗 لینک جدید عضویت را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>https://t.me/VirangarVPN</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in edit_states
            and edit_states[
                message.from_user.id
            ]["step"] == "invite_link"
        )
    )
    def receive_invite_link(message):

        user_id = message.from_user.id

        invite_link = message.text.strip()

        if not (
            invite_link.startswith("https://t.me/")
            or invite_link.startswith("http://t.me/")
        ):
            bot.send_message(
                message.chat.id,
                "❌ لینک معتبر نیست.",
            )
            return

        data = edit_states[user_id]

        db: Session = db_factory()

        try:
            channel = db.get(
                RequiredChannel,
                data["channel_id"],
            )

            if not channel:
                bot.send_message(
                    message.chat.id,
                    "❌ کانال پیدا نشد.",
                )
                return

            channel.title = data["title"]
            channel.username = data["username"]
            channel.invite_link = invite_link

            db.commit()

            bot.send_message(
                message.chat.id,
                "✅ <b>کانال با موفقیت ویرایش شد.</b>\n\n"
                f"🏷 نام: <b>{channel.title}</b>\n"
                f"📌 کانال: <code>{channel.username}</code>\n"
                f"🔗 لینک: {channel.invite_link}",
            )

        finally:
            db.close()

            edit_states.pop(
                user_id,
                None,
            )
