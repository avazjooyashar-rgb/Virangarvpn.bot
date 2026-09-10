import telebot
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin, Role
from app.utils.permissions import is_super_admin


admin_add_states = {}


def register_admin_add_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_add"
    )
    def start_admin_add(call):

        db: Session = db_factory()

        try:
            if not is_super_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ فقط Super Admin دسترسی دارد.",
                    show_alert=True,
                )
                return
        finally:
            db.close()

        admin_add_states[call.from_user.id] = {
            "step": "telegram_id",
            "telegram_id": None,
            "role_id": None,
        }

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "➕ <b>افزودن ادمین جدید</b>\n\n"
            "مرحله ۱ از ۲\n\n"
            "🆔 آیدی عددی تلگرام ادمین را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>123456789</code>",
        )

    @bot.message_handler(
        func=lambda message: (
            message.from_user.id in admin_add_states
            and admin_add_states[
                message.from_user.id
            ]["step"] == "telegram_id"
        )
    )
    def receive_admin_id(message):

        user_id = message.from_user.id
        raw_id = message.text.strip()

        if not raw_id.isdigit():
            bot.send_message(
                message.chat.id,
                "❌ آیدی باید فقط عدد باشد.\n"
                "دوباره ارسال کنید:",
            )
            return

        telegram_id = int(raw_id)

        if telegram_id <= 0:
            bot.send_message(
                message.chat.id,
                "❌ آیدی واردشده معتبر نیست.",
            )
            return

        db: Session = db_factory()

        try:
            existing = db.scalar(
                select(Admin).where(
                    Admin.telegram_id == telegram_id
                )
            )

            if existing:
                bot.send_message(
                    message.chat.id,
                    "⚠️ این کاربر قبلاً ادمین است.",
                )
                return

            roles = db.scalars(
                select(Role)
                .order_by(Role.id)
            ).all()

            if not roles:
                bot.send_message(
                    message.chat.id,
                    "❌ هیچ نقشی در سیستم وجود ندارد.",
                )
                return

        finally:
            db.close()

        admin_add_states[user_id]["telegram_id"] = telegram_id
        admin_add_states[user_id]["step"] = "role"

        bot.send_message(
            message.chat.id,
            "مرحله ۲ از ۲\n\n"
            "🛡 نقش ادمین را انتخاب کنید:",
            reply_markup=role_keyboard(
                telegram_id,
                roles,
            ),
        )

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_add_role:"
        )
    )
    def select_admin_role(call):

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

            data = call.data.split(":")

            telegram_id = int(data[1])
            role_id = int(data[2])

            role = db.get(
                Role,
                role_id,
            )

            if not role:
                bot.answer_callback_query(
                    call.id,
                    "❌ نقش پیدا نشد.",
                    show_alert=True,
                )
                return

            existing = db.scalar(
                select(Admin).where(
                    Admin.telegram_id == telegram_id
                )
            )

            if existing:
                bot.answer_callback_query(
                    call.id,
                    "⚠️ این کاربر قبلاً ادمین است.",
                    show_alert=True,
                )
                return

            admin = Admin(
                telegram_id=telegram_id,
                role_id=role.id,
                role=role.name,
                is_active=True,
            )

            db.add(admin)
            db.commit()
            db.refresh(admin)

            admin_add_states.pop(
                call.from_user.id,
                None,
            )

            bot.answer_callback_query(
                call.id,
                "✅ ادمین اضافه شد.",
            )

            bot.edit_message_text(
                "✅ <b>ادمین با موفقیت اضافه شد.</b>\n\n"
                f"🆔 آیدی: <code>{admin.telegram_id}</code>\n"
                f"🛡 نقش: <b>{role.name}</b>\n"
                "🟢 وضعیت: فعال",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )

        finally:
            db.close()


def role_keyboard(
    telegram_id: int,
    roles,
):

    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(row_width=1)

    for role in roles:
        keyboard.add(
            InlineKeyboardButton(
                f"🛡 {role.name}",
                callback_data=(
                    f"admin_add_role:"
                    f"{telegram_id}:"
                    f"{role.id}"
                ),
            )
        )

    return keyboard
