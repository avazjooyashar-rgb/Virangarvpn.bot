import telebot
from sqlalchemy.orm import Session

from app.database.models import RequiredChannel
from app.utils.permissions import is_super_admin


# وضعیت موقت مراحل افزودن کانال
channel_states = {}


def register_channel_wizard_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "channel_add"
    )
    def start_channel_add(call):

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

        finally:
            db.close()

        channel_states[call.from_user.id] = {
            "step": "title",
            "title": None,
            "username": None,
            "invite_link": None,
        }

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "➕ <b>افزودن کانال اجباری</b>\n\n"
            "مرحله ۱ از ۳\n\n"
            "🏷 نام نمایشی کانال را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>کانال اصلی VirangarVPN</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in channel_states
            and channel_states[
                message.from_user.id
            ]["step"] == "title"
        )
    )
    def receive_channel_title(message):

        user_id = message.from_user.id

        title = message.text.strip()

        if not title:
            bot.send_message(
                message.chat.id,
                "❌ عنوان نمی‌تواند خالی باشد.\n"
                "دوباره ارسال کنید:",
            )
            return

        channel_states[user_id]["title"] = title
        channel_states[user_id]["step"] = "username"

        bot.send_message(
            message.chat.id,
            "مرحله ۲ از ۳\n\n"
            "📌 یوزرنیم کانال را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>@VirangarVPN</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in channel_states
            and channel_states[
                message.from_user.id
            ]["step"] == "username"
        )
    )
    def receive_channel_username(message):

        user_id = message.from_user.id

        username = message.text.strip()

        if not username.startswith("@"):
            username = f"@{username}"

        if len(username) < 2:
            bot.send_message(
                message.chat.id,
                "❌ یوزرنیم معتبر نیست.\n"
                "دوباره ارسال کنید:",
            )
            return

        channel_states[user_id]["username"] = username
        channel_states[user_id]["step"] = "invite_link"

        bot.send_message(
            message.chat.id,
            "مرحله ۳ از ۳\n\n"
            "🔗 لینک عضویت کانال را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>https://t.me/VirangarVPN</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in channel_states
            and channel_states[
                message.from_user.id
            ]["step"] == "invite_link"
        )
    )
    def receive_channel_invite_link(message):

        user_id = message.from_user.id

        invite_link = message.text.strip()

        if not (
            invite_link.startswith("https://t.me/")
            or invite_link.startswith("http://t.me/")
        ):
            bot.send_message(
                message.chat.id,
                "❌ لینک معتبر نیست.\n\n"
                "لینک باید به شکل زیر باشد:\n"
                "<code>https://t.me/ChannelName</code>",
            )
            return

        data = channel_states[user_id]

        db: Session = db_factory()

        try:
            existing = db.query(
                RequiredChannel
            ).filter(
                RequiredChannel.username
                == data["username"]
            ).first()

            if existing:
                bot.send_message(
                    message.chat.id,
                    "⚠️ این کانال قبلاً ثبت شده است.",
                )
                return

            channel = RequiredChannel(
                title=data["title"],
                username=data["username"],
                invite_link=invite_link,
                is_active=True,
            )

            db.add(channel)
            db.commit()
            db.refresh(channel)

            bot.send_message(
                message.chat.id,
                "✅ <b>کانال با موفقیت اضافه شد.</b>\n\n"
                f"🏷 نام: <b>{channel.title}</b>\n"
                f"📌 کانال: <code>{channel.username}</code>\n"
                f"🔗 لینک: {channel.invite_link}\n"
                "🟢 وضعیت: فعال",
            )

        finally:
            db.close()

            channel_states.pop(
                user_id,
                None,
            )
