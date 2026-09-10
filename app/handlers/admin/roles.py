import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Role, Permission, RolePermission
from app.utils.permissions import is_super_admin


def roles_keyboard(roles) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "➕ ساخت نقش جدید",
            callback_data="role_add",
        )
    )

    for role in roles:
        icon = "👑" if role.name == "super_admin" else "🛡"
        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {role.name}",
                callback_data=f"role_manage:{role.id}",
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت به مدیریت",
            callback_data="admin_dashboard",
        )
    )

    return keyboard


def role_manage_keyboard(role_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "🔐 مدیریت دسترسی‌ها",
            callback_data=f"role_permissions:{role_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_roles",
        )
    )

    return keyboard


def register_role_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_roles"
    )
    def admin_roles(call):

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

            roles = db.scalars(
                select(Role).order_by(Role.id)
            ).all()

            text = (
                "🛡 <b>مدیریت نقش‌ها</b>\n\n"
                "نقش موردنظر را انتخاب کنید:"
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=roles_keyboard(roles),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "role_manage:"
        )
    )
    def role_manage(call):

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

            role_id = int(
                call.data.split(":")[1]
            )

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

            text = (
                "🛡 <b>مدیریت نقش</b>\n\n"
                f"🏷 نام: <code>{role.name}</code>\n"
                f"📝 توضیح: "
                f"{role.description or 'ثبت نشده'}\n"
                f"⚙️ سیستمی: "
                f"{'بله' if role.is_system else 'خیر'}\n\n"
                "عملیات موردنظر:"
            )

            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=role_manage_keyboard(role.id),
            )

            bot.answer_callback_query(call.id)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(
            "role_permissions:"
        )
    )
    def role_permissions(call):

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

            role_id = int(
                call.data.split(":")[1]
            )

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

            permissions = db.scalars(
                select(Permission)
                .order_by(Permission.id)
            ).all()

            assigned_ids = {
                item.permission_id
                for item in db.scalars(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id
                    )
                ).all()
            }

            keyboard = InlineKeyboardMarkup(row_width=1)

            for permission in permissions:
                icon = (
                    "✅"
                    if permission.id in assigned_ids
                    else "⬜️"
                )

                keyboard.add(
                    InlineKeyboardButton(
                        f"{icon} {permission.code}",
                        callback_data=(
                            f"permission_toggle:"
                            f"{role.id}:"
                            f"{permission.id}"
                        ),
                    )
                )

            keyboard.add(
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"role_manage:{role.id}",
                )
            )

            text = (
                f"🔐 <b>دسترسی‌های نقش</b>\n\n"
                f"نقش: <code>{role.name}</code>\n\n"
                "روی هر دسترسی بزنید تا فعال/غیرفعال شود:"
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
            "permission_toggle:"
        )
    )
    def permission_toggle(call):

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

            _, role_id, permission_id = (
                call.data.split(":")
            )

            role_id = int(role_id)
            permission_id = int(permission_id)

            role = db.get(Role, role_id)
            permission = db.get(
                Permission,
                permission_id,
            )

            if not role or not permission:
                bot.answer_callback_query(
                    call.id,
                    "❌ اطلاعات پیدا نشد.",
                    show_alert=True,
                )
                return

            existing = db.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id
                    == permission_id,
                )
            )

            if existing:
                db.delete(existing)
                message = "🔴 دسترسی غیرفعال شد."
            else:
                db.add(
                    RolePermission(
                        role_id=role_id,
                        permission_id=permission_id,
                    )
                )
                message = "🟢 دسترسی فعال شد."

            db.commit()

            bot.answer_callback_query(
                call.id,
                message,
            )

            role_permissions(call)

        finally:
            db.close()

    @bot.callback_query_handler(
        func=lambda call: call.data == "role_add"
    )
    def role_add(call):

        if not call.message:
            return

        bot.answer_callback_query(
            call.id,
            "🚧 ساخت نقش در مرحله بعد تکمیل می‌شود.",
            show_alert=True,
        )
