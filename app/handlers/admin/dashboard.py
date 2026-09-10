import telebot
from sqlalchemy.orm import Session

from app.keyboards.admin import (
    admin_main_keyboard,
    force_membership_keyboard,
)
from app.services.membership_service import check_required_membership
from app.utils.permissions import is_admin


def register_admin_dashboard_handlers(
    bot: telebot.TeleBot,
    db_factory,
):

    def open_admin_panel(chat_id: int, user_id: int):
        db: Session = db_factory()

        try:
            # اول بررسی دسترسی ادمین
            if not is_admin(db, user_id):
                bot.send_message(
                    chat_id,
                    "⛔️ <b>دسترسی غیرمجاز</b>\n\n"
                    "شما دسترسی ورود به پنل مدیریت را ندارید.",
                )
                return

            # بررسی عضویت اجباری
            is_member, missing_channels = check_required_membership(
                bot=bot,
                db=db,
                user_id=user_id,
            )

            if not is_member:
                bot.send_message(
                    chat_id,
                    "🔐 <b>ورود به پنل مدیریت</b>\n\n"
                    "برای دسترسی به پنل، ابتدا در کانال‌های زیر عضو شوید:",
                    reply_markup=force_membership_keyboard(
                        missing_channels
                    ),
                )
                return

            # ورود موفق به پنل
            bot.send_message(
                chat_id,
                "🛡 <b>پنل مدیریت VirangarVPN</b>\n\n"
                "خوش آمدید مدیر 👑\n\n"
                "یکی از بخش‌های زیر را انتخاب کنید:",
                reply_markup=admin_main_keyboard(),
            )

        finally:
            db.close()

    @bot.message_handler(commands=["admin"])
    def admin_command(message):
        open_admin_panel(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        )

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_dashboard"
    )
    def admin_dashboard_callback(call):
        bot.answer_callback_query(call.id)

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass

        open_admin_panel(
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
        )

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_close"
    )
    def admin_close_callback(call):
        bot.answer_callback_query(
            call.id,
            "پنل مدیریت بسته شد.",
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass

    @bot.callback_query_handler(
        func=lambda call: call.data == "admin_check_membership"
    )
    def admin_check_membership_callback(call):
        db: Session = db_factory()

        try:
            if not is_admin(
                db,
                call.from_user.id,
            ):
                bot.answer_callback_query(
                    call.id,
                    "⛔️ دسترسی ندارید.",
                    show_alert=True,
                )
                return

            is_member, missing_channels = check_required_membership(
                bot=bot,
                db=db,
                user_id=call.from_user.id,
            )

            if not is_member:
                bot.answer_callback_query(
                    call.id,
                    "❌ هنوز عضویت شما کامل نشده.",
                    show_alert=True,
                )

                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=force_membership_keyboard(
                            missing_channels
                        ),
                    )
                except Exception:
                    pass

                return

            bot.answer_callback_query(
                call.id,
                "✅ عضویت تأیید شد.",
            )

            try:
                bot.edit_message_text(
                    "🛡 <b>پنل مدیریت VirangarVPN</b>\n\n"
                    "✅ عضویت شما تأیید شد.\n\n"
                    "یکی از بخش‌های زیر را انتخاب کنید:",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=admin_main_keyboard(),
                )
            except Exception:
                pass

        finally:
            db.close()
