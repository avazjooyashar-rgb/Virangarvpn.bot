import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.utils.permissions import is_super_admin


def admin_status_keyboard(admin_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "🔄 تغییر وضعیت",
            callback_data=f"admin_status_toggle:{admin_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🗑 حذف ادمین",
            callback_data=f"admin_remove:{admin_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_admins",
        )
    )

    return keyboard


def register_admin_status_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_status_manage:"
        )
    )
    def manage_admin_status(call):

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

            admin_id = int(
                call.data.split(":")[1]
            )

            admin = db.get(
                Admin,
                admin_id,
            )

            if not admin:
                bot.answer_callback_query(
                    call.id,
                    "❌ ادمین پیدا نشد.",
                    show_alert=True,
                )
                return

            status = (
                "🟢 فعال"
                if admin.is_active
                else "🔴 غیرفعال"
            )

            text = (
                "👮 <b>مدیریت ادمین</b>\n\n"
                f"🆔 آیدی: "
                f"<code>{admin.telegram_id}</code>\n"
                f"🛡 نقش: <b>{admin.role}</b>\n"
                f"📊 وضعیت: {status}\n\n"
                "عملیات موردنظر را انتخاب کنید:"
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_status_keyboard(
                    admin.id
                ),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_status_toggle:"
        )
    )
    def toggle_admin_status(call):

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

            admin_id = int(
                call.data.split(":")[1]
            )

            admin = db.get(
                Admin,
                admin_id,
            )

            if not admin:
                bot.answer_callback_query(
                    call.id,
                    "❌ ادمین پیدا نشد.",
                    show_alert=True,
                )
                return

            admin.is_active = not admin.is_active

            db.commit()

            status = (
                "فعال"
                if admin.is_active
                else "غیرفعال"
            )

            bot.answer_callback_query(
                call.id,
                f"✅ ادمین {status} شد.",
            )

            status_icon = (
                "🟢"
                if admin.is_active
                else "🔴"
            )

            bot.edit_message_text(
                "👮 <b>مدیریت ادمین</b>\n\n"
                f"🆔 آیدی: "
                f"<code>{admin.telegram_id}</code>\n"
                f"🛡 نقش: <b>{admin.role}</b>\n"
                f"📊 وضعیت: "
                f"{status_icon} "
                f"{status}\n\n"
                "عملیات موردنظر را انتخاب کنید:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_status_keyboard(
                    admin.id
                ),
            )

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_remove:"
        )
    )
    def remove_admin(call):

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

            admin_id = int(
                call.data.split(":")[1]
            )

            admin = db.get(
                Admin,
                admin_id,
            )

            if not admin:
                bot.answer_callback_query(
                    call.id,
                    "❌ ادمین پیدا نشد.",
                    show_alert=True,
                )
                return

            if admin.telegram_id == call.from_user.id:
                bot.answer_callback_query(
                    call.id,
                    "⛔️ نمی‌توانید خودتان را حذف کنید.",
                    show_alert=True,
                )
                return

            keyboard = InlineKeyboardMarkup(row_width=2)

            keyboard.add(
                InlineKeyboardButton(
                    "✅ بله، حذف شود",
                    callback_data=f"admin_remove_confirm:{admin.id}",
                ),
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data=f"admin_status_manage:{admin.id}",
                ),
            )

            bot.edit_message_text(
                "⚠️ <b>تأیید حذف ادمین</b>\n\n"
                f"🆔 آیدی: "
                f"<code>{admin.telegram_id}</code>\n"
                f"🛡 نقش: <b>{admin.role}</b>\n\n"
                "آیا مطمئن هستید؟",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_remove_confirm:"
        )
    )
    def confirm_remove_admin(call):

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

            admin_id = int(
                call.data.split(":")[1]
            )

            admin = db.get(
                Admin,
                admin_id,
            )

            if not admin:
                bot.answer_callback_query(
                    call.id,
                    "❌ ادمین پیدا نشد.",
                    show_alert=True,
                )
                return

            if admin.telegram_id == call.from_user.id:
                bot.answer_callback_query(
                    call.id,
                    "⛔️ نمی‌توانید خودتان را حذف کنید.",
                    show_alert=True,
                )
                return

            telegram_id = admin.telegram_id

            db.delete(admin)
            db.commit()

            bot.answer_callback_query(
                call.id,
                "🗑 ادمین حذف شد.",
            )

            admins = db.scalars(
                select(Admin).order_by(Admin.id)
            ).all()

            if not admins:
                text = (
                    "👮 <b>مدیریت ادمین‌ها</b>\n\n"
                    "هیچ ادمینی ثبت نشده است."
                )
            else:
                lines = [
                    "👮 <b>مدیریت ادمین‌ها</b>\n"
                ]

                for item in admins:
                    status = (
                        "🟢 فعال"
                        if item.is_active
                        else "🔴 غیرفعال"
                    )

                    lines.append(
                        f"• <code>{item.telegram_id}</code>\n"
                        f"  نقش: <b>{item.role}</b>\n"
                        f"  وضعیت: {status}\n"
                    )

                text = "\n".join(lines)

            keyboard = InlineKeyboardMarkup()

            keyboard.add(
                InlineKeyboardButton(
                    "🔙 بازگشت به مدیریت",
                    callback_data="admin_dashboard",
                )
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
            )

        finally:
            db.close()
