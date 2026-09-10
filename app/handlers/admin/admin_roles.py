import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin, Role
from app.utils.permissions import is_super_admin


def admin_roles_keyboard(
    admins,
) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(row_width=1)

    for admin in admins:
        keyboard.add(
            InlineKeyboardButton(
                f"👤 {admin.telegram_id} | {admin.role}",
                callback_data=f"admin_role_manage:{admin.id}",
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت به مدیریت",
            callback_data="admin_admins",
        )
    )

    return keyboard


def role_select_keyboard(
    admin_id: int,
    roles,
) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(row_width=1)

    for role in roles:
        keyboard.add(
            InlineKeyboardButton(
                f"🛡 {role.name}",
                callback_data=(
                    f"admin_role_set:"
                    f"{admin_id}:"
                    f"{role.id}"
                ),
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=f"admin_role_manage:{admin_id}",
        )
    )

    return keyboard


def register_admin_role_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_admin_roles"
    )
    def admin_role_list(call):

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

            admins = db.scalars(
                select(Admin)
                .order_by(Admin.id)
            ).all()

            if not admins:
                text = (
                    "🛡 <b>تعیین نقش ادمین‌ها</b>\n\n"
                    "هیچ ادمینی ثبت نشده است."
                )
            else:
                text = (
                    "🛡 <b>تعیین نقش ادمین‌ها</b>\n\n"
                    "ادمین موردنظر را انتخاب کنید:"
                )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_roles_keyboard(admins),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_role_manage:"
        )
    )
    def admin_role_manage(call):

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

            text = (
                "👤 <b>مدیریت نقش ادمین</b>\n\n"
                f"🆔 Telegram ID: "
                f"<code>{admin.telegram_id}</code>\n"
                f"🛡 نقش فعلی: "
                f"<b>{admin.role}</b>\n\n"
                "برای تغییر نقش روی گزینه زیر بزن:"
            )

            keyboard = InlineKeyboardMarkup()

            keyboard.add(
                InlineKeyboardButton(
                    "🛡 تغییر نقش",
                    callback_data=f"admin_role_choose:{admin.id}",
                )
            )

            keyboard.add(
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="admin_admin_roles",
                )
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_role_choose:"
        )
    )
    def admin_role_choose(call):

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

            roles = db.scalars(
                select(Role)
                .order_by(Role.id)
            ).all()

            bot.edit_message_text(
                "🛡 <b>انتخاب نقش</b>\n\n"
                f"ادمین: <code>{admin.telegram_id}</code>\n\n"
                "نقش جدید را انتخاب کنید:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=role_select_keyboard(
                    admin.id,
                    roles,
                ),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "admin_role_set:"
        )
    )
    def admin_role_set(call):

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

            _, admin_id, role_id = (
                call.data.split(":")
            )

            admin_id = int(admin_id)
            role_id = int(role_id)

            admin = db.get(
                Admin,
                admin_id,
            )

            role = db.get(
                Role,
                role_id,
            )

            if not admin or not role:
                bot.answer_callback_query(
                    call.id,
                    "❌ اطلاعات پیدا نشد.",
                    show_alert=True,
                )
                return

            admin.role_id = role.id
            admin.role = role.name

            db.commit()

            bot.answer_callback_query(
                call.id,
                "✅ نقش ادمین تغییر کرد.",
            )

            bot.edit_message_text(
                "✅ <b>نقش با موفقیت تغییر کرد.</b>\n\n"
                f"👤 ادمین: "
                f"<code>{admin.telegram_id}</code>\n"
                f"🛡 نقش جدید: "
                f"<b>{role.name}</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_roles_keyboard(
                    db.scalars(
                        select(Admin)
                        .order_by(Admin.id)
                    ).all()
                ),
            )

        finally:
            db.close()
