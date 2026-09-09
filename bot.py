import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_IDS, SUPER_ADMIN_ID
from database import (
    init_db,
    add_user,
    get_stats,
    get_all_users,
    get_channels,
    get_panels,
    get_balance,
)


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# USER MENU
# =========================

def user_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "🛡 سرویس‌های من",
                callback_data="my_services",
            ),
            InlineKeyboardButton(
                "🛒 خرید VPN",
                callback_data="buy_vpn",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 پنل‌ها",
                callback_data="panels",
            ),
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="wallet",
            ),
        ],
        [
            InlineKeyboardButton(
                "📚 راهنما",
                callback_data="help",
            ),
            InlineKeyboardButton(
                "🎫 پشتیبانی",
                callback_data="support",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# ADMIN MENU
# =========================

def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="stats",
            ),
            InlineKeyboardButton(
                "👥 کاربران",
                callback_data="users",
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 پیام همگانی",
                callback_data="broadcast",
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 عضویت اجباری",
                callback_data="channels",
            ),
            InlineKeyboardButton(
                "📦 مدیریت پنل‌ها",
                callback_data="manage_panels",
            ),
        ],
        [
            InlineKeyboardButton(
                "👑 مدیریت ادمین‌ها",
                callback_data="admins",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# FORCE JOIN
# =========================

async def check_membership(
    user_id,
    context,
):
    channels = get_channels(active_only=True)

    if not channels:
        return True

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel["chat_id"],
                user_id=user_id,
            )

            if member.status in (
                "left",
                "kicked",
            ):
                return False

        except Exception as error:
            logger.warning(
                "Membership check failed for %s: %s",
                channel["chat_id"],
                error,
            )

            # اگر بررسی کانال ممکن نبود،
            # فعلاً کاربر را رد نمی‌کنیم.
            continue

    return True


def force_join_menu(channels):
    keyboard = []

    for channel in channels:
        if channel.get("invite_link"):
            keyboard.append([
                InlineKeyboardButton(
                    f"📢 {channel.get('title') or 'عضویت در کانال'}",
                    url=channel["invite_link"],
                )
            ])

        elif channel.get("username"):
            username = channel["username"]

            if not username.startswith("@"):
                username = "@" + username

            keyboard.append([
                InlineKeyboardButton(
                    f"📢 {channel.get('title') or username}",
                    url=f"https://t.me/{username.lstrip('@')}",
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "✅ عضو شدم",
            callback_data="check_join",
        )
    ])

    return InlineKeyboardMarkup(keyboard)


async def require_membership(
    update,
    context,
):
    user = update.effective_user

    if user.id == SUPER_ADMIN_ID:
        return True

    is_member = await check_membership(
        user.id,
        context,
    )

    if is_member:
        return True

    channels = get_channels(active_only=True)

    text = (
        "🔒 دسترسی به ربات محدود است.\n\n"
        "برای استفاده از VirangarVPN ابتدا "
        "در کانال‌های زیر عضو شوید:\n\n"
        "بعد از عضویت روی «✅ عضو شدم» بزنید."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=force_join_menu(channels),
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=force_join_menu(channels),
        )

    return False


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    add_user(user)

    # 👑 Super Admin
    if user.id == SUPER_ADMIN_ID:
        await update.message.reply_text(
            "👑 پنل مدیریت VirangarVPN\n\n"
            "خوش آمدید مدیر اصلی.\n"
            "تمام دسترسی‌های مدیریتی برای شما فعال است.",
            reply_markup=admin_menu(),
        )
        return

    # 🔒 Force Join
    if not await require_membership(
        update,
        context,
    ):
        return

    await update.message.reply_text(
        "🔥 به VirangarVPN خوش آمدید!\n\n"
        "🚀 سرویس سریع و پایدار\n"
        "🔐 مدیریت آسان سرویس\n"
        "💎 پشتیبانی اختصاصی\n\n"
        "👇 از منوی زیر انتخاب کنید:",
        reply_markup=user_menu(),
    )


# =========================
# ADMIN COMMAND
# =========================

async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )
        return

    await update.message.reply_text(
        "👑 پنل مدیریت VirangarVPN\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu(),
    )


# =========================
# MAIN
# =========================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN داخل فایل .env تنظیم نشده است."
        )

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            receive_broadcast,
        )
    )

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "🔥 VirangarVPN Bot started."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
    # =========================
# CALLBACK HANDLER
# =========================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # =========================
    # CHECK FORCE JOIN
    # =========================

    if data == "check_join":
        if await check_membership(user_id, context):
            await query.edit_message_text(
                "✅ عضویت شما تأیید شد!\n\n"
                "🔥 حالا می‌توانید از VirangarVPN استفاده کنید.",
                reply_markup=user_menu(),
            )
        else:
            channels = get_channels(active_only=True)

            await query.edit_message_text(
                "❌ هنوز در همه کانال‌های اجباری عضو نشده‌اید.\n\n"
                "ابتدا عضو کانال‌ها شوید و دوباره "
                "روی «✅ عضو شدم» بزنید.",
                reply_markup=force_join_menu(channels),
            )

        return

    # =========================
    # ADMIN ACCESS
    # =========================

    admin_callbacks = {
        "stats",
        "users",
        "broadcast",
        "channels",
        "manage_panels",
        "admins",
    }

    if data in admin_callbacks:

        if user_id not in ADMIN_IDS:
            await query.answer(
                "⛔ دسترسی غیرمجاز.",
                show_alert=True,
            )
            return

        # =====================
        # STATS
        # =====================

        if data == "stats":
            stats = get_stats()

            text = (
                "╔════════════════════╗\n"
                "       📊 آمار ربات\n"
                "╚════════════════════╝\n\n"
                f"👥 کل کاربران: {stats['total']}\n"
                f"🟢 کاربران فعال: {stats['active']}\n"
                f"🆕 کاربران امروز: {stats['today']}\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🤖 وضعیت ربات: 🟢 ONLINE"
            )

            await query.edit_message_text(
                text,
                reply_markup=admin_menu(),
            )

        # =====================
        # USERS
        # =====================

        elif data == "users":
            users = get_all_users()

            await query.edit_message_text(
                "👥 مدیریت کاربران\n\n"
                f"👤 تعداد کاربران فعال: {len(users)}\n\n"
                "مدیریت پیشرفته کاربران در مرحله بعد اضافه می‌شود.",
                reply_markup=admin_menu(),
            )

        # =====================
        # BROADCAST
        # =====================

        elif data == "broadcast":
            context.user_data["broadcast_mode"] = True

            await query.edit_message_text(
                "📢 پیام همگانی\n\n"
                "پیام موردنظر را در پیام بعدی ارسال کنید.\n\n"
                "برای لغو عملیات:\n"
                "/cancel"
            )

        # =====================
        # FORCE JOIN
        # =====================

        elif data == "channels":
            channels = get_channels(active_only=False)

            if not channels:
                text = (
                    "📢 عضویت اجباری\n\n"
                    "هنوز هیچ کانالی ثبت نشده است."
                )
            else:
                lines = [
                    "📢 کانال‌های عضویت اجباری\n"
                ]

                for channel in channels:
                    status = (
                        "🟢 فعال"
                        if channel["is_active"]
                        else "🔴 غیرفعال"
                    )

                    lines.append(
                        f"• {channel['title'] or channel['chat_id']}\n"
                        f"  وضعیت: {status}\n"
                        f"  ID: {channel['chat_id']}\n"
                    )

                text = "\n".join(lines)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "➕ افزودن کانال",
                        callback_data="channel_add",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑 حذف کانال",
                        callback_data="channel_delete",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin_home",
                    )
                ],
            ]

            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        # =====================
        # PANELS
        # =====================

        elif data == "manage_panels":
            panels = get_panels(active_only=False)

            if not panels:
                text = (
                    "📦 مدیریت پنل‌ها\n\n"
                    "هنوز هیچ پنلی ایجاد نشده است."
                )
            else:
                lines = [
                    "📦 مدیریت پنل‌ها\n"
                ]

                for panel in panels:
                    status = (
                        "🟢 فعال"
                        if panel["is_active"]
                        else "🔴 غیرفعال"
                    )

                    lines.append(
                        f"📦 {panel['name']}\n"
                        f"💰 قیمت: {panel['price']:,} تومان\n"
                        f"⏱ مدت: {panel['duration'] or '-'}\n"
                        f"📊 حجم: {panel['volume'] or '-'}\n"
                        f"👥 کاربران: {panel['max_users']}\n"
                        f"وضعیت: {status}\n"
                    )

                text = "\n".join(lines)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "➕ افزودن پنل",
                        callback_data="panel_add",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✏️ ویرایش پنل",
                        callback_data="panel_edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑 حذف پنل",
                        callback_data="panel_delete",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin_home",
                    )
                ],
            ]

            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        # =====================
        # ADMINS
        # =====================

        elif data == "admins":

            if user_id != SUPER_ADMIN_ID:
                await query.edit_message_text(
                    "⛔ فقط Super Admin به مدیریت ادمین‌ها دسترسی دارد.",
                    reply_markup=admin_menu(),
                )
                return

            await query.edit_message_text(
                "👑 مدیریت ادمین‌ها\n\n"
                "در این بخش می‌توانیم:\n\n"
                "➕ ادمین جدید اضافه کنیم\n"
                "➖ ادمین حذف کنیم\n"
                "👥 لیست ادمین‌ها را ببینیم\n"
                "🔐 سطح دسترسی تعیین کنیم",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "➕ افزودن ادمین",
                            callback_data="admin_add",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "👥 لیست ادمین‌ها",
                            callback_data="admin_list",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 پنل مدیریت",
                            callback_data="admin_home",
                        )
                    ],
                ]),
            )

        return

    # =========================
    # ADMIN HOME
    # =========================

    if data == "admin_home":

        if user_id not in ADMIN_IDS:
            return

        await query.edit_message_text(
            "👑 پنل مدیریت VirangarVPN\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=admin_menu(),
        )

        return

    # =========================
    # USER ACCESS
    # =========================

    if not await require_membership(
        update,
        context,
    ):
        return

    # =========================
    # USER: HOME
    # =========================

    if data == "back_home":

        await query.edit_message_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=user_menu(),
        )

    # =========================
    # USER: BUY
    # =========================

    elif data == "buy_vpn":

        panels = get_panels(active_only=True)

        if not panels:
            await query.edit_message_text(
                "🛒 خرید VPN\n\n"
                "❌ در حال حاضر پنلی برای فروش فعال نیست.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data="back_home",
                        )
                    ]
                ]),
            )
            return

        keyboard = []

        for panel in panels:
            keyboard.append([
                InlineKeyboardButton(
                    f"🛒 {panel['name']} | {panel['price']:,} تومان",
                    callback_data=f"buy_panel_{panel['id']}",
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_home",
            )
        ])

        await query.edit_message_text(
            "🛒 خرید VPN\n\n"
            "📦 پنل موردنظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # =========================
    # USER: PANELS
    # =========================

    elif data == "panels":

        panels = get_panels(active_only=True)

        if not panels:
            await query.edit_message_text(
                "📦 پنل‌ها\n\n"
                "فعلاً پنل فعالی وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data="back_home",
                        )
                    ]
                ]),
            )
            return

        lines = ["📦 پنل‌های VirangarVPN\n"]

        for panel in panels:
            lines.append(
                f"💎 {panel['name']}\n"
                f"💰 قیمت: {panel['price']:,} تومان\n"
                f"⏱ مدت: {panel['duration'] or '-'}\n"
                f"📊 حجم: {panel['volume'] or '-'}\n"
                f"👥 کاربران: {panel['max_users']}\n"
                f"📝 {panel['description'] or '-'}\n"
                "━━━━━━━━━━━━━━"
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛒 خرید VPN",
                        callback_data="buy_vpn",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_home",
                    )
                ],
            ]),
        )

    # =========================
    # USER: WALLET
    # =========================

    elif data == "wallet":

        balance = get_balance(user_id)

        await query.edit_message_text(
            "💰 کیف پول\n\n"
            f"💵 موجودی شما: {balance:,} تومان\n\n"
            "از گزینه‌های زیر استفاده کنید:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ افزایش موجودی",
                        callback_data="wallet_charge",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📜 تراکنش‌ها",
                        callback_data="transactions",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_home",
                    )
                ],
            ]),
        )

    # =========================
    # USER: SERVICES
    # =========================

    elif data == "my_services":

        await query.edit_message_text(
            "🛡 سرویس‌های من\n\n"
            "فعلاً سرویسی برای حساب شما ثبت نشده است.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛒 خرید VPN",
                        callback_data="buy_vpn",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_home",
                    )
                ],
            ]),
        )

    # =========================
    # USER: SUPPORT
    # =========================

    elif data == "support":

        await query.edit_message_text(
            "🎫 پشتیبانی VirangarVPN\n\n"
            "برای ارتباط با پشتیبانی، تیکت جدید ایجاد کنید.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎫 ایجاد تیکت",
                        callback_data="ticket_create",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📂 تیکت‌های من",
                        callback_data="my_tickets",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_home",
                    )
                ],
            ]),
        )

    # =========================
    # USER: HELP
    # =========================

    elif data == "help":

        await query.edit_message_text(
            "📚 راهنمای VirangarVPN\n\n"
            "🛒 خرید VPN\n"
            "از بخش خرید، پنل موردنظر را انتخاب کنید.\n\n"
            "📦 پنل‌ها\n"
            "مشخصات و قیمت پنل‌های فعال را ببینید.\n\n"
            "💰 کیف پول\n"
            "موجودی خود را مدیریت کنید.\n\n"
            "🎫 پشتیبانی\n"
            "برای مشکلات خود تیکت ایجاد کنید.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back_home",
                    )
                ]
            ]),
        )
        # =========================
# DATABASE HELPERS
# =========================

from database import connect, now


def db_add_channel(chat_id, title="", username="", invite_link=""):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO channels (
            chat_id,
            title,
            username,
            invite_link,
            is_active,
            created_at
        )
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (
            chat_id,
            title,
            username,
            invite_link,
            now(),
        ),
    )

    db.commit()
    db.close()


def db_delete_channel(channel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM channels WHERE id = ?",
        (channel_id,),
    )

    db.commit()
    db.close()


def db_add_panel(
    name,
    price,
    duration,
    volume,
    max_users,
    description,
):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO panels (
            name,
            price,
            duration,
            volume,
            max_users,
            description,
            is_active,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            name,
            price,
            duration,
            volume,
            max_users,
            description,
            now(),
        ),
    )

    db.commit()
    db.close()


def db_delete_panel(panel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM panels WHERE id = ?",
        (panel_id,),
    )

    db.commit()
    db.close()


# =========================
# ADMIN CHECK
# =========================

def is_admin(user_id):
    if user_id == SUPER_ADMIN_ID:
        return True

    if user_id in ADMIN_IDS:
        return True

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM admins
        WHERE user_id = ?
        AND is_active = 1
        """,
        (user_id,),
    )

    result = cursor.fetchone()

    db.close()

    return result is not None


# =========================
# ADD CHANNEL
# =========================

async def start_add_channel(update, context):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    context.user_data["channel_add_mode"] = True

    await update.callback_query.edit_message_text(
        "📢 افزودن کانال اجباری\n\n"
        "آیدی کانال را ارسال کن.\n\n"
        "مثال:\n"
        "@YourChannel\n\n"
        "یا:\n"
        "-100123456789\n\n"
        "❌ برای لغو /cancel را بزن."
    )


# =========================
# ADD PANEL
# =========================

async def start_add_panel(update, context):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    context.user_data["panel_add_step"] = "name"

    await update.callback_query.edit_message_text(
        "📦 افزودن پنل فروش\n\n"
        "مرحله 1 از 6\n\n"
        "نام پنل را ارسال کن.\n\n"
        "مثال:\n"
        "🔥 VIP 30GB"
    )


# =========================
# ADD ADMIN
# =========================

async def start_add_admin(update, context):
    user_id = update.effective_user.id

    if user_id != SUPER_ADMIN_ID:
        await update.callback_query.answer(
            "⛔ فقط سوپر ادمین می‌تواند ادمین اضافه کند.",
            show_alert=True,
        )
        return

    context.user_data["admin_add_mode"] = True

    await update.callback_query.edit_message_text(
        "👑 افزودن ادمین\n\n"
        "آیدی عددی تلگرام شخص را ارسال کن.\n\n"
        "مثال:\n"
        "123456789\n\n"
        "❌ برای لغو /cancel"
    )


# =========================
# MESSAGE HANDLER
# =========================

async def process_admin_input(update, context):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    if not is_admin(user_id):
        return

    # -------------------------
    # ADD CHANNEL
    # -------------------------

    if context.user_data.get("channel_add_mode"):

        chat_id = text

        try:
            chat = await context.bot.get_chat(chat_id)

            title = chat.title or ""
            username = chat.username or ""

            invite_link = ""

            if username:
                invite_link = f"https://t.me/{username}"

            db_add_channel(
                chat_id=str(chat.id),
                title=title,
                username=username,
                invite_link=invite_link,
            )

            context.user_data["channel_add_mode"] = False

            await update.message.reply_text(
                "✅ کانال با موفقیت اضافه شد.\n\n"
                f"📢 نام: {title}\n"
                f"🆔 ID: {chat.id}\n\n"
                "🔒 عضویت اجباری فعال شد."
            )

        except Exception as error:
            logger.error("Add channel error: %s", error)

            await update.message.reply_text(
                "❌ نتوانستم کانال را شناسایی کنم.\n\n"
                "مطمئن شو:\n"
                "1️⃣ آیدی کانال درست است\n"
                "2️⃣ ربات داخل کانال عضو است\n"
                "3️⃣ ربات دسترسی لازم را دارد\n\n"
                "دوباره ارسال کن یا /cancel بزن."
            )

        return

    # -------------------------
    # ADD ADMIN
    # -------------------------

    if context.user_data.get("admin_add_mode"):

        if not text.isdigit():
            await update.message.reply_text(
                "❌ آیدی باید عددی باشد.\n\n"
                "مثال: 123456789"
            )
            return

        admin_id = int(text)

        if admin_id == SUPER_ADMIN_ID:
            await update.message.reply_text(
                "👑 این کاربر خود سوپر ادمین است."
            )
            context.user_data["admin_add_mode"] = False
            return

        db = connect()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO admins (
                user_id,
                username,
                first_name,
                added_at,
                is_active
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                admin_id,
                "",
                "",
                now(),
            ),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO admin_permissions (
                admin_id,
                permission
            )
            VALUES (?, ?)
            """,
            (
                admin_id,
                "all",
            ),
        )

        db.commit()
        db.close()

        context.user_data["admin_add_mode"] = False

        await update.message.reply_text(
            "✅ ادمین با موفقیت اضافه شد.\n\n"
            f"👤 ID: {admin_id}\n"
            "🔐 دسترسی: کامل"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 1
    # -------------------------

    if context.user_data.get("panel_add_step") == "name":

        context.user_data["new_panel_name"] = text
        context.user_data["panel_add_step"] = "price"

        await update.message.reply_text(
            "💰 مرحله 2 از 6\n\n"
            "قیمت پنل را به تومان ارسال کن.\n\n"
            "مثال:\n"
            "150000"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 2
    # -------------------------

    if context.user_data.get("panel_add_step") == "price":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ قیمت باید فقط عدد باشد.\n\n"
                "مثال:\n"
                "150000"
            )

            return

        context.user_data["new_panel_price"] = int(text)
        context.user_data["panel_add_step"] = "duration"

        await update.message.reply_text(
            "⏱ مرحله 3 از 6\n\n"
            "مدت سرویس را ارسال کن.\n\n"
            "مثال:\n"
            "30 روز"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 3
    # -------------------------

    if context.user_data.get("panel_add_step") == "duration":

        context.user_data["new_panel_duration"] = text
        context.user_data["panel_add_step"] = "volume"

        await update.message.reply_text(
            "📊 مرحله 4 از 6\n\n"
            "حجم سرویس را ارسال کن.\n\n"
            "مثال:\n"
            "30GB"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 4
    # -------------------------

    if context.user_data.get("panel_add_step") == "volume":

        context.user_data["new_panel_volume"] = text
        context.user_data["panel_add_step"] = "max_users"

        await update.message.reply_text(
            "👥 مرحله 5 از 6\n\n"
            "حداکثر تعداد کاربر/دستگاه را ارسال کن.\n\n"
            "مثال:\n"
            "1"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 5
    # -------------------------

    if context.user_data.get("panel_add_step") == "max_users":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ تعداد باید عدد باشد."
            )

            return

        context.user_data["new_panel_max_users"] = int(text)
        context.user_data["panel_add_step"] = "description"

        await update.message.reply_text(
            "📝 مرحله 6 از 6\n\n"
            "توضیحات پنل را ارسال کن.\n\n"
            "مثال:\n"
            "⚡ سرعت بالا\n"
            "🔐 مناسب استفاده روزمره\n"
            "📱 یک دستگاه"
        )

        return

    # -------------------------
    # ADD PANEL - STEP 6
    # -------------------------

    if context.user_data.get("panel_add_step") == "description":

        db_add_panel(
            name=context.user_data["new_panel_name"],
            price=context.user_data["new_panel_price"],
            duration=context.user_data["new_panel_duration"],
            volume=context.user_data["new_panel_volume"],
            max_users=context.user_data["new_panel_max_users"],
            description=text,
        )

        context.user_data.pop("panel_add_step", None)

        await update.message.reply_text(
            "✅ پنل با موفقیت ساخته شد.\n\n"
            f"📦 نام: {context.user_data.pop('new_panel_name')}\n"
            f"💰 قیمت: {context.user_data.pop('new_panel_price'):,} تومان\n"
            f"⏱ مدت: {context.user_data.pop('new_panel_duration')}\n"
            f"📊 حجم: {context.user_data.pop('new_panel_volume')}\n"
            f"👥 کاربران: {context.user_data.pop('new_panel_max_users')}\n\n"
            "🟢 پنل فعال شد."
        )

        return


# =========================
# CANCEL
# =========================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ عملیات لغو شد."
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Unhandled exception:",
        exc_info=context.error,
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN داخل فایل .env تنظیم نشده است."
        )

    init_db()

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("admin", admin)
    )

    application.add_handler(
        CommandHandler("cancel", cancel)
    )

    application.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            process_admin_input,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            receive_broadcast,
        )
    )

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "🔥 VirangarVPN Bot started."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
