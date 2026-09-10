import telebot
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Role
from app.utils.permissions import is_super_admin


role_states = {}


def register_role_wizard_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "role_add"
    )
    def start_role_add(call):

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

        role_states[call.from_user.id] = {
            "step": "name",
            "name": None,
            "description": None,
        }

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "➕ <b>ساخت نقش جدید</b>\n\n"
            "مرحله ۱ از ۲\n\n"
            "🏷 نام نقش را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>sales_manager</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in role_states
            and role_states[
                message.from_user.id
            ]["step"] == "name"
        )
    )
    def receive_role_name(message):

        user_id = message.from_user.id
        name = message.text.strip()

        if not name:
            bot.send_message(
                message.chat.id,
                "❌ نام نقش نمی‌تواند خالی باشد.",
            )
            return

        if len(name) > 100:
            bot.send_message(
                message.chat.id,
                "❌ نام نقش نباید بیشتر از ۱۰۰ کاراکتر باشد.",
            )
            return

        db: Session = db_factory()

        try:
            existing = db.scalar(
                select(Role).where(
                    Role.name == name
                )
            )

            if existing:
                bot.send_message(
                    message.chat.id,
                    "⚠️ این نام نقش قبلاً استفاده شده است.\n"
                    "یک نام دیگر ارسال کنید:",
                )
                return

        finally:
            db.close()

        role_states[user_id]["name"] = name
        role_states[user_id]["step"] = "description"

        bot.send_message(
            message.chat.id,
            "مرحله ۲ از ۲\n\n"
            "📝 توضیح نقش را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>مدیر فروش و سفارشات</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in role_states
            and role_states[
                message.from_user.id
            ]["step"] == "description"
        )
    )
    def receive_role_description(message):

        user_id = message.from_user.id
        description = message.text.strip()

        if not description:
            bot.send_message(
                message.chat.id,
                "❌ توضیح نمی‌تواند خالی باشد.",
            )
            return

        if len(description) > 500:
            bot.send_message(
                message.chat.id,
                "❌ توضیح نباید بیشتر از ۵۰۰ کاراکتر باشد.",
            )
            return

        data = role_states[user_id]

        db: Session = db_factory()

        try:
            existing = db.scalar(
                select(Role).where(
                    Role.name == data["name"]
                )
            )

            if existing:
                bot.send_message(
                    message.chat.id,
                    "⚠️ این نقش قبلاً ایجاد شده است.",
                )
                return

            role = Role(
                name=data["name"],
                description=description,
                is_system=False,
            )

            db.add(role)
            db.commit()
            db.refresh(role)

            bot.send_message(
                message.chat.id,
                "✅ <b>نقش با موفقیت ساخته شد.</b>\n\n"
                f"🏷 نام: <code>{role.name}</code>\n"
                f"📝 توضیح: {role.description}\n\n"
                "🔐 حالا می‌توانی دسترسی‌های این نقش را "
                "از بخش مدیریت نقش‌ها تعیین کنی.",
            )

        finally:
            db.close()

            role_states.pop(
                user_id,
                None,
            )
