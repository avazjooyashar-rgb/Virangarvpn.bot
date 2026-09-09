import logging
import html
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    get_panel,
    get_balance,
    set_balance,
    add_balance,
    add_transaction,
    get_transactions,
    get_user_services,
    add_service,
    create_ticket,
    get_user_tickets,
    add_ticket_message,
    get_ticket_messages,
    get_payment_settings,
    set_payment_settings,
    add_admin,
    remove_admin,
    get_admins,
    is_admin_db,
    connect,
    now,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("VirangarVPN")


# =========================================================
# GENERAL
# =========================================================

def is_admin(user_id: int) -> bool:
    return (
        user_id == SUPER_ADMIN_ID
        or user_id in ADMIN_IDS
        or is_admin_db(user_id)
    )


def admin_ids():
    ids = set(ADMIN_IDS)
    ids.add(SUPER_ADMIN_ID)
    for item in get_admins():
        ids.add(int(item["user_id"]))
    return ids


def money(value) -> str:
    return f"{int(value):,} تومان"


def clear_state(context):
    for key in (
        "state",
        "broadcast_mode",
        "channel_add_mode",
        "panel_add_step",
        "panel_edit_id",
        "admin_add_mode",
        "payment_edit_step",
        "ticket_id",
        "ticket_reply_mode",
        "deposit_amount",
        "deposit_transaction_id",
    ):
        context.user_data.pop(key, None)


# =========================================================
# KEYBOARDS
# =========================================================

def user_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛡 سرویس‌های من", callback_data="my_services"),
            InlineKeyboardButton("🛒 خرید VPN", callback_data="buy_vpn"),
        ],
        [
            InlineKeyboardButton("📦 پنل‌ها", callback_data="panels"),
            InlineKeyboardButton("💰 کیف پول", callback_data="wallet"),
        ],
        [
            InlineKeyboardButton("📚 راهنما", callback_data="help"),
            InlineKeyboardButton("🎫 پشتیبانی", callback_data="support"),
        ],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 آمار", callback_data="a_stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="a_users"),
        ],
        [
            InlineKeyboardButton("📢 ارسال همگانی", callback_data="a_broadcast"),
            InlineKeyboardButton("📢 کانال‌ها", callback_data="a_channels"),
        ],
        [
            InlineKeyboardButton("📦 مدیریت پنل‌ها", callback_data="a_panels"),
            InlineKeyboardButton("🎫 تیکت‌ها", callback_data="a_tickets"),
        ],
        [
            InlineKeyboardButton("💳 تنظیمات پرداخت", callback_data="a_payment"),
            InlineKeyboardButton("👑 مدیران", callback_data="a_admins"),
        ],
        [
            InlineKeyboardButton("🏠 منوی کاربر", callback_data="back_home"),
        ],
    ])


def back_admin():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")]
    ])


def back_user():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_home")]
    ])


# =========================================================
# FORCE JOIN
# =========================================================

async def check_membership(context, user_id: int) -> bool:
    channels = get_channels(active_only=True)

    if not channels:
        return True

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel["chat_id"],
                user_id=user_id,
            )
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            logger.exception("Membership check failed for %s", channel["chat_id"])
            # If Telegram cannot check the channel, don't lock all users out.
            continue

    return True


def force_join_menu():
    rows = []
    for channel in get_channels(active_only=True):
        link = channel.get("invite_link") or ""
        username = channel.get("username") or ""

        if link:
            url = link
        elif username:
            url = f"https://t.me/{username.lstrip('@')}"
        else:
            continue

        title = channel.get("title") or username or "کانال"
        rows.append([InlineKeyboardButton(f"📢 {title}", url=url)])

    rows.append([InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join")])
    return InlineKeyboardMarkup(rows)


async def require_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False

    if user.id == SUPER_ADMIN_ID:
        return True

    ok = await check_membership(context, user.id)
    if ok:
        return True

    text = (
        "🔒 برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید.\n\n"
        "بعد از عضویت روی «بررسی عضویت» بزنید."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=force_join_menu(),
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            text,
            reply_markup=force_join_menu(),
        )

    return False


# =========================================================
# DATABASE HELPERS
# =========================================================

def db_execute(sql, params=(), fetchone=False, fetchall=False, commit=True):
    db = connect()
    cur = db.cursor()
    cur.execute(sql, params)

    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()

    if commit:
        db.commit()
    db.close()
    return result


def get_user_row(user_id):
    return db_execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
        fetchone=True,
        commit=False,
    )


def get_users_all():
    rows = db_execute(
        "SELECT * FROM users ORDER BY id DESC",
        fetchall=True,
        commit=False,
    )
    return [dict(x) for x in rows]


def set_user_blocked(user_id, blocked: bool):
    db_execute(
        "UPDATE users SET is_blocked = ? WHERE id = ?",
        (1 if blocked else 0, user_id),
    )


def update_transaction_status(transaction_id, status):
    db_execute(
        "UPDATE transactions SET status = ? WHERE id = ?",
        (status, transaction_id),
    )


def get_transaction(transaction_id):
    row = db_execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,),
        fetchone=True,
        commit=False,
    )
    return dict(row) if row else None


def update_panel(panel_id, name, price, duration, volume, max_users, description):
    db_execute(
        """
        UPDATE panels
        SET name = ?, price = ?, duration = ?, volume = ?,
            max_users = ?, description = ?
        WHERE id = ?
        """,
        (
            name,
            price,
            duration,
            volume,
            max_users,
            description,
            panel_id,
        ),
    )


def delete_panel(panel_id):
    db_execute("DELETE FROM panels WHERE id = ?", (panel_id,))


def add_panel(name, price, duration, volume, max_users, description):
    db_execute(
        """
        INSERT INTO panels
        (name, price, duration, volume, max_users, description, is_active, created_at)
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


def set_channel_active(channel_id, active):
    db_execute(
        "UPDATE channels SET is_active = ? WHERE id = ?",
        (1 if active else 0, channel_id),
    )


def get_all_tickets():
    rows = db_execute(
        """
        SELECT t.*, u.username, u.first_name
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        ORDER BY
            CASE WHEN t.status = 'open' THEN 0 ELSE 1 END,
            t.updated_at DESC
        """,
        fetchall=True,
        commit=False,
    )
    return [dict(x) for x in rows]


def get_ticket(ticket_id):
    row = db_execute(
        """
        SELECT t.*, u.username, u.first_name
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        WHERE t.id = ?
        """,
        (ticket_id,),
        fetchone=True,
        commit=False,
    )
    return dict(row) if row else None


def set_ticket_status(ticket_id, status):
    db_execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (status, now(), ticket_id),
    )


def purchase_service(user_id, panel):
    """
    Atomic wallet deduction + transaction + service creation.
    The service stays pending until a real VPN panel API is connected.
    """
    db = connect()
    cur = db.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            "SELECT balance FROM wallets WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        balance = int(row["balance"]) if row else 0

        price = int(panel["price"])
        if balance < price:
            db.rollback()
            return False, balance, None

        new_balance = balance - price

        cur.execute(
            """
            INSERT INTO wallets (user_id, balance)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET balance = excluded.balance
            """,
            (user_id, new_balance),
        )

        cur.execute(
            """
            INSERT INTO transactions
            (user_id, amount, type, status, description, created_at)
            VALUES (?, ?, 'purchase', 'approved', ?, ?)
            """,
            (
                user_id,
                -price,
                f"خرید سرویس {panel['name']}",
                now(),
            ),
        )

        cur.execute(
            """
            INSERT INTO services
            (user_id, panel_id, panel_name, price, duration, volume,
             status, config, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', '', ?, NULL)
            """,
            (
                user_id,
                panel["id"],
                panel["name"],
                price,
                panel.get("duration") or "",
                panel.get("volume") or "",
                now(),
            ),
        )

        service_id = cur.lastrowid
        db.commit()
        return True, new_balance, service_id

    except Exception:
        db.rollback()
        logger.exception("Purchase failed")
        return False, 0, None
    finally:
        db.close()


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)

    user = update.effective_user
    if not user:
        return

    add_user(user)

    if not await require_membership(update, context):
        return

    await update.message.reply_text(
        "🔥 منوی اصلی VirangarVPN\n\n"
        "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=user_menu(),
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)

    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return

    await update.message.reply_text(
        "👑 پنل مدیریت VirangarVPN\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu(),
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=user_menu() if not is_admin(update.effective_user.id) else admin_menu(),
    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_id = user.id
    data = query.data or ""

    # ---------- JOIN ----------
    if data == "check_join":
        if await check_membership(context, user_id):
            await query.edit_message_text(
                "🔥 عضویت شما تأیید شد.\n\n"
                "منوی اصلی VirangarVPN:",
                reply_markup=user_menu(),
            )
        else:
            await query.edit_message_text(
                "❌ هنوز عضویت شما در همه کانال‌ها تأیید نشده است.",
                reply_markup=force_join_menu(),
            )
        return

    # ---------- ADMIN ----------
    admin_prefixes = (
        "admin_home",
        "a_",
        "u_",
        "ch_",
        "p_",
        "adm_",
        "bc_",
        "pay_",
        "at_",
        "dep_",
    )

    if data == "admin_home" or data.startswith(admin_prefixes):
        if not is_admin(user_id):
            await query.edit_message_text("⛔ دسترسی ندارید.")
            return

    if data == "admin_home":
        clear_state(context)
        await query.edit_message_text(
            "👑 پنل مدیریت VirangarVPN\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=admin_menu(),
        )
        return

    # ---------- ADMIN STATS ----------
    if data == "a_stats":
        stats = get_stats()
        await query.edit_message_text(
            "📊 آمار ربات\n\n"
            f"👥 کل کاربران: {stats['total']}\n"
            f"🟢 کاربران فعال: {stats['active']}\n"
            f"🆕 عضویت امروز: {stats['today']}",
            reply_markup=back_admin(),
        )
        return

    # ---------- ADMIN USERS ----------
    if data == "a_users":
        users = get_users_all()

        if not users:
            text = "👥 هنوز کاربری ثبت نشده است."
            markup = back_admin()
        else:
            lines = ["👥 مدیریت کاربران\n"]
            buttons = []

            for u in users[:40]:
                name = u.get("first_name") or "بدون نام"
                username = f"@{u['username']}" if u.get("username") else "بدون یوزرنیم"
                status = "🚫 مسدود" if u["is_blocked"] else "🟢 فعال"

                lines.append(
                    f"• {name} | {username}\n"
                    f"  ID: {u['id']} | {status}"
                )

                action = "بازکردن" if u["is_blocked"] else "مسدود"
                icon = "🟢" if u["is_blocked"] else "🚫"
                buttons.append([
                    InlineKeyboardButton(
                        f"{icon} {action} {u['id']}",
                        callback_data=f"u_toggle_{u['id']}",
                    )
                ])

            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
            text = "\n".join(lines)
            markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(text, reply_markup=markup)
        return

    if data.startswith("u_toggle_"):
        target_id = int(data.split("_")[-1])
        row = get_user_row(target_id)

        if not row:
            await query.edit_message_text("❌ کاربر پیدا نشد.", reply_markup=back_admin())
            return

        new_blocked = not bool(row["is_blocked"])

        if target_id == SUPER_ADMIN_ID:
            await query.edit_message_text(
                "⛔ سوپر ادمین قابل مسدود کردن نیست.",
                reply_markup=back_admin(),
            )
            return

        set_user_blocked(target_id, new_blocked)

        await query.edit_message_text(
            f"✅ وضعیت کاربر {target_id} تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 بازگشت به کاربران", callback_data="a_users")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    # ---------- BROADCAST ----------
    if data == "a_broadcast":
        clear_state(context)
        context.user_data["broadcast_mode"] = True
        await query.edit_message_text(
            "📢 ارسال همگانی\n\n"
            "پیام، عکس، ویدیو، فایل یا هر محتوایی را که می‌خواهید ارسال شود بفرستید.\n\n"
            "❌ برای لغو /cancel را بزنید.",
            reply_markup=back_admin(),
        )
        return

    # ---------- CHANNELS ----------
    if data == "a_channels":
        channels = get_channels(active_only=False)

        lines = ["📢 کانال‌های اجباری\n"]
        buttons = []

        if not channels:
            lines.append("هیچ کانالی ثبت نشده است.")
        else:
            for ch in channels:
                status = "🟢 فعال" if ch["is_active"] else "🔴 غیرفعال"
                lines.append(
                    f"• {ch.get('title') or ch.get('username') or ch['chat_id']}\n"
                    f"  ID: {ch['id']} | {status}"
                )
                buttons.append([
                    InlineKeyboardButton(
                        f"🗑 حذف {ch['id']}",
                        callback_data=f"ch_del_{ch['id']}",
                    ),
                    InlineKeyboardButton(
                        "🔄 فعال/غیرفعال",
                        callback_data=f"ch_toggle_{ch['id']}",
                    ),
                ])

        buttons.append([InlineKeyboardButton("➕ افزودن کانال", callback_data="ch_add")])
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data == "ch_add":
        clear_state(context)
        context.user_data["channel_add_mode"] = True
        await query.edit_message_text(
            "➕ افزودن کانال\n\n"
            "اول ID کانال را بفرستید.\n"
            "مثال:\n"
            "-1001234567890\n\n"
            "ربات باید داخل کانال ادمین باشد.",
            reply_markup=back_admin(),
        )
        return

    if data.startswith("ch_del_"):
        channel_id = int(data.split("_")[-1])
        db_execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await query.edit_message_text(
            "🗑 کانال حذف شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 کانال‌ها", callback_data="a_channels")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    if data.startswith("ch_toggle_"):
        channel_id = int(data.split("_")[-1])
        row = db_execute(
            "SELECT is_active FROM channels WHERE id = ?",
            (channel_id,),
            fetchone=True,
            commit=False,
        )
        if row:
            set_channel_active(channel_id, not bool(row["is_active"]))

        await query.edit_message_text(
            "✅ وضعیت کانال تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 کانال‌ها", callback_data="a_channels")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    # ---------- PANELS ----------
    if data == "a_panels":
        panels = get_panels(active_only=False)
        lines = ["📦 مدیریت پنل‌ها\n"]
        buttons = []

        if not panels:
            lines.append("هیچ پنلی ثبت نشده است.")
        else:
            for p in panels:
                status = "🟢 فعال" if p["is_active"] else "🔴 غیرفعال"
                lines.append(
                    f"• {p['name']} — {money(p['price'])}\n"
                    f"  ⏱ {p.get('duration') or '-'} | 📦 {p.get('volume') or '-'} | {status}"
                )
                buttons.append([
                    InlineKeyboardButton("✏️ ویرایش", callback_data=f"p_edit_{p['id']}"),
                    InlineKeyboardButton("🗑 حذف", callback_data=f"p_del_{p['id']}"),
                ])
                buttons.append([
                    InlineKeyboardButton(
                        "🔄 فعال/غیرفعال",
                        callback_data=f"p_toggle_{p['id']}",
                    )
                ])

        buttons.append([InlineKeyboardButton("➕ افزودن پنل", callback_data="p_add")])
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data == "p_add":
        clear_state(context)
        context.user_data["panel_add_step"] = "name"
        await query.edit_message_text(
            "➕ افزودن پنل\n\n"
            "مرحله 1 از 6\n"
            "نام پنل را بفرستید.",
            reply_markup=back_admin(),
        )
        return

    if data.startswith("p_del_"):
        panel_id = int(data.split("_")[-1])
        delete_panel(panel_id)
        await query.edit_message_text(
            "🗑 پنل حذف شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 پنل‌ها", callback_data="a_panels")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    if data.startswith("p_toggle_"):
        panel_id = int(data.split("_")[-1])
        row = db_execute(
            "SELECT is_active FROM panels WHERE id = ?",
            (panel_id,),
            fetchone=True,
            commit=False,
        )
        if row:
            db_execute(
                "UPDATE panels SET is_active = ? WHERE id = ?",
                (0 if row["is_active"] else 1, panel_id),
            )

        await query.edit_message_text(
            "✅ وضعیت پنل تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 پنل‌ها", callback_data="a_panels")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    if data.startswith("p_edit_"):
        panel_id = int(data.split("_")[-1])
        panel = get_panel(panel_id)

        if not panel:
            await query.edit_message_text("❌ پنل پیدا نشد.", reply_markup=back_admin())
            return

        context.user_data["panel_edit_id"] = panel_id
        context.user_data["panel_edit_step"] = "name"

        await query.edit_message_text(
            f"✏️ ویرایش پنل «{panel['name']}»\n\n"
            "مرحله 1 از 6\n"
            "نام جدید را بفرستید.\n"
            "برای حفظ مقدار فعلی، همان مقدار فعلی را بفرستید.",
            reply_markup=back_admin(),
        )
        return

    # ---------- ADMINS ----------
    if data == "a_admins":
        if user_id != SUPER_ADMIN_ID:
            await query.edit_message_text(
                "⛔ فقط سوپر ادمین به مدیریت مدیران دسترسی دارد.",
                reply_markup=back_admin(),
            )
            return

        admins = get_admins()
        lines = ["👑 مدیران\n"]
        buttons = []

        if not admins:
            lines.append("هیچ مدیر دیتابیسی ثبت نشده است.")
        else:
            for a in admins:
                lines.append(
                    f"• {a.get('first_name') or '-'} "
                    f"(@{a.get('username') or '-'})\n"
                    f"  ID: {a['user_id']}"
                )
                if int(a["user_id"]) != SUPER_ADMIN_ID:
                    buttons.append([
                        InlineKeyboardButton(
                            f"🗑 حذف {a['user_id']}",
                            callback_data=f"adm_del_{a['user_id']}",
                        )
                    ])

        buttons.append([InlineKeyboardButton("➕ افزودن مدیر", callback_data="adm_add")])
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data == "adm_add":
        if user_id != SUPER_ADMIN_ID:
            return

        clear_state(context)
        context.user_data["admin_add_mode"] = True

        await query.edit_message_text(
            "➕ افزودن مدیر\n\n"
            "User ID عددی شخص را ارسال کنید.",
            reply_markup=back_admin(),
        )
        return

    if data.startswith("adm_del_"):
        if user_id != SUPER_ADMIN_ID:
            return

        target = int(data.split("_")[-1])
        if target == SUPER_ADMIN_ID:
            await query.edit_message_text(
                "⛔ سوپر ادمین حذف نمی‌شود.",
                reply_markup=back_admin(),
            )
            return

        remove_admin(target)

        await query.edit_message_text(
            "🗑 مدیر حذف شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 مدیران", callback_data="a_admins")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    # ---------- PAYMENT SETTINGS ----------
    if data == "a_payment":
        settings = get_payment_settings()

        card = settings.get("card_number") or "ثبت نشده"
        bank = settings.get("bank_name") or "ثبت نشده"
        holder = settings.get("card_holder") or "ثبت نشده"
        minimum = money(settings.get("min_amount") or 0)

        await query.edit_message_text(
            "💳 تنظیمات پرداخت\n\n"
            f"🏦 بانک: {bank}\n"
            f"💳 کارت: {card}\n"
            f"👤 صاحب حساب: {holder}\n"
            f"💰 حداقل شارژ: {minimum}\n\n"
            "ℹ️ روش کارت‌به‌کارت فعال است.\n"
            "درگاه آنلاین بعد از اتصال API درگاه فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data="pay_edit")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")],
            ]),
        )
        return

    if data == "pay_edit":
        if user_id != SUPER_ADMIN_ID:
            await query.edit_message_text(
                "⛔ فقط سوپر ادمین می‌تواند تنظیمات پرداخت را تغییر دهد.",
                reply_markup=back_admin(),
            )
            return

        clear_state(context)
        context.user_data["payment_edit_step"] = "card_number"

        await query.edit_message_text(
            "✏️ تنظیمات پرداخت\n\n"
            "1️⃣ شماره کارت را بفرستید.",
            reply_markup=back_admin(),
        )
        return

    # ---------- ADMIN TICKETS ----------
    if data == "a_tickets":
        tickets = get_all_tickets()
        lines = ["🎫 تیکت‌های کاربران\n"]
        buttons = []

        if not tickets:
            lines.append("تیکتی وجود ندارد.")
        else:
            for t in tickets[:40]:
                status = "🟢 باز" if t["status"] == "open" else "⚪ بسته"
                name = t.get("first_name") or str(t["user_id"])
                subject = t.get("subject") or "بدون موضوع"

                lines.append(
                    f"#{t['id']} — {status}\n"
                    f"👤 {name} | {subject}"
                )
                buttons.append([
                    InlineKeyboardButton(
                        f"🎫 باز کردن #{t['id']}",
                        callback_data=f"at_open_{t['id']}",
                    )
                ])

        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("at_open_"):
        ticket_id = int(data.split("_")[-1])
        ticket = get_ticket(ticket_id)

        if not ticket:
            await query.edit_message_text("❌ تیکت پیدا نشد.", reply_markup=back_admin())
            return

        messages = get_ticket_messages(ticket_id)
        lines = [
            f"🎫 تیکت #{ticket_id}",
            f"👤 کاربر: {ticket.get('first_name') or '-'}",
            f"🆔 ID: {ticket['user_id']}",
            f"📌 موضوع: {ticket.get('subject') or '-'}",
            f"📍 وضعیت: {ticket['status']}",
            "",
            "💬 پیام‌ها:",
        ]

        for m in messages[-15:]:
            role = "👤 کاربر" if m["sender_role"] == "user" else "👑 ادمین"
            lines.append(f"{role}: {m['message']}")

        buttons = [
            [InlineKeyboardButton("💬 پاسخ", callback_data=f"at_reply_{ticket_id}")],
        ]

        if ticket["status"] == "open":
            buttons.append([
                InlineKeyboardButton("🔒 بستن", callback_data=f"at_close_{ticket_id}")
            ])
        else:
            buttons.append([
                InlineKeyboardButton("🔓 باز کردن", callback_data=f"at_open_status_{ticket_id}")
            ])

        buttons.append([InlineKeyboardButton("🔙 تیکت‌ها", callback_data="a_tickets")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("at_reply_"):
        ticket_id = int(data.split("_")[-1])
        if not get_ticket(ticket_id):
            return

        clear_state(context)
        context.user_data["ticket_reply_mode"] = ticket_id

        await query.edit_message_text(
            f"💬 پاسخ به تیکت #{ticket_id}\n\n"
            "پیام خود را ارسال کنید.",
            reply_markup=back_admin(),
        )
        return

    if data.startswith("at_close_"):
        ticket_id = int(data.split("_")[-1])
        set_ticket_status(ticket_id, "closed")
        await query.edit_message_text(
            "🔒 تیکت بسته شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎫 تیکت‌ها", callback_data="a_tickets")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    if data.startswith("at_open_status_"):
        ticket_id = int(data.split("_")[-1])
        set_ticket_status(ticket_id, "open")
        await query.edit_message_text(
            "🔓 تیکت باز شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎫 تیکت‌ها", callback_data="a_tickets")],
                [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_home")],
            ]),
        )
        return

    # ---------- DEPOSIT APPROVAL ----------
    if data.startswith("dep_approve_") or data.startswith("dep_reject_"):
        action, transaction_id = data.rsplit("_", 1)
        transaction_id = int(transaction_id)
        transaction = get_transaction(transaction_id)

        if not transaction or transaction["status"] != "pending":
            await query.edit_message_text(
                "⚠️ این درخواست قبلاً بررسی شده یا وجود ندارد.",
                reply_markup=back_admin(),
            )
            return

        if action == "dep_approve":
            add_balance(transaction["user_id"], transaction["amount"])
            update_transaction_status(transaction_id, "approved")

            try:
                await context.bot.send_message(
                    transaction["user_id"],
                    "✅ شارژ کیف پول شما تأیید شد.\n\n"
                    f"💰 مبلغ: {money(transaction['amount'])}\n"
                    f"💳 موجودی جدید: {money(get_balance(transaction['user_id']))}",
                )
            except Exception:
                logger.exception("Could not notify user about approved deposit")

            await query.edit_message_text(
                f"✅ درخواست شارژ #{transaction_id} تأیید شد.\n"
                f"مبلغ: {money(transaction['amount'])}",
                reply_markup=back_admin(),
            )
        else:
            update_transaction_status(transaction_id, "rejected")

            try:
                await context.bot.send_message(
                    transaction["user_id"],
                    "❌ درخواست شارژ کیف پول شما رد شد.\n\n"
                    "در صورت نیاز با پشتیبانی تماس بگیرید.",
                )
            except Exception:
                logger.exception("Could not notify user about rejected deposit")

            await query.edit_message_text(
                f"❌ درخواست شارژ #{transaction_id} رد شد.",
                reply_markup=back_admin(),
            )
        return

    # =====================================================
    # USER ACCESS
    # =====================================================

    if not await require_membership(update, context):
        return

    # ---------- HOME ----------
    if data == "back_home":
        clear_state(context)
        await query.edit_message_text(
            "🔥 منوی اصلی VirangarVPN\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=user_menu(),
        )
        return

    # ---------- MY SERVICES ----------
    if data == "my_services":
        services = get_user_services(user_id)

        if not services:
            await query.edit_message_text(
                "🛡 سرویس‌های من\n\n"
                "هنوز سرویسی خریداری نکرده‌اید.",
                reply_markup=back_user(),
            )
            return

        lines = ["🛡 سرویس‌های من\n"]

        for s in services[:20]:
            status_map = {
                "pending": "⏳ در انتظار ساخت",
                "active": "🟢 فعال",
                "expired": "🔴 منقضی",
                "disabled": "⚪ غیرفعال",
            }
            status = status_map.get(s["status"], s["status"])

            lines.append(
                f"#{s['id']} — {s.get('panel_name') or '-'}\n"
                f"💰 {money(s['price'])}\n"
                f"⏱ {s.get('duration') or '-'} | 📦 {s.get('volume') or '-'}\n"
                f"📍 وضعیت: {status}"
            )

            if s.get("config"):
                lines.append(f"🔗 کانفیگ: {s['config']}")

            lines.append("")

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=back_user(),
        )
        return

    # ---------- BUY ----------
    if data == "buy_vpn":
        panels = get_panels(active_only=True)

        if not panels:
            await query.edit_message_text(
                "🛒 خرید VPN\n\n"
                "در حال حاضر پنل فعالی برای فروش وجود ندارد.",
                reply_markup=back_user(),
            )
            return

        buttons = []
        for p in panels:
            buttons.append([
                InlineKeyboardButton(
                    f"🛒 {p['name']} — {money(p['price'])}",
                    callback_data=f"buy_{p['id']}",
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")])

        await query.edit_message_text(
            "🛒 خرید VPN\n\n"
            "یک سرویس را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("buy_"):
        panel_id = int(data.split("_")[-1])
        panel = get_panel(panel_id)

        if not panel or not panel["is_active"]:
            await query.edit_message_text(
                "❌ این سرویس دیگر در دسترس نیست.",
                reply_markup=back_user(),
            )
            return

        await query.edit_message_text(
            f"📦 {panel['name']}\n\n"
            f"💰 قیمت: {money(panel['price'])}\n"
            f"⏱ مدت: {panel.get('duration') or '-'}\n"
            f"📦 حجم: {panel.get('volume') or '-'}\n"
            f"👥 ظرفیت: {panel.get('max_users') or '-'}\n\n"
            f"📝 {panel.get('description') or 'بدون توضیحات'}\n\n"
            "آیا خرید را تأیید می‌کنید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تأیید خرید", callback_data=f"buyok_{panel_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_vpn")],
            ]),
        )
        return

    if data.startswith("buyok_"):
        panel_id = int(data.split("_")[-1])
        panel = get_panel(panel_id)

        if not panel or not panel["is_active"]:
            await query.edit_message_text(
                "❌ سرویس دیگر موجود نیست.",
                reply_markup=back_user(),
            )
            return

        success, balance, service_id = purchase_service(user_id, panel)

        if not success:
            await query.edit_message_text(
                "❌ موجودی کیف پول کافی نیست.\n\n"
                f"💰 موجودی فعلی: {money(get_balance(user_id))}\n"
                f"💵 قیمت سرویس: {money(panel['price'])}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 شارژ کیف پول", callback_data="wallet_charge")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_vpn")],
                ]),
            )
            return

        await query.edit_message_text(
            "✅ خرید با موفقیت ثبت شد.\n\n"
            f"📦 سرویس: {panel['name']}\n"
            f"💰 مبلغ: {money(panel['price'])}\n"
            f"💳 موجودی باقی‌مانده: {money(balance)}\n\n"
            "⏳ سرویس در وضعیت «در انتظار ساخت» قرار گرفت.\n"
            "پس از اتصال API پنل VPN، ساخت کانفیگ به‌صورت خودکار انجام می‌شود.",
            reply_markup=back_user(),
        )
        return

    # ---------- PANELS ----------
    if data == "panels":
        panels = get_panels(active_only=True)

        if not panels:
            await query.edit_message_text(
                "📦 پنل فعالی وجود ندارد.",
                reply_markup=back_user(),
            )
            return

        lines = ["📦 پنل‌های VirangarVPN\n"]

        for p in panels:
            lines.append(
                f"🔹 {p['name']}\n"
                f"💰 {money(p['price'])}\n"
                f"⏱ {p.get('duration') or '-'} | 📦 {p.get('volume') or '-'}\n"
                f"📝 {p.get('description') or '-'}\n"
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 خرید VPN", callback_data="buy_vpn")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")],
            ]),
        )
        return

    # ---------- WALLET ----------
    if data == "wallet":
        balance = get_balance(user_id)

        await query.edit_message_text(
            "💰 کیف پول\n\n"
            f"💳 موجودی: {money(balance)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge")],
                [InlineKeyboardButton("📜 تراکنش‌ها", callback_data="wallet_tx")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")],
            ]),
        )
        return

    if data == "wallet_charge":
        settings = get_payment_settings()
        minimum = int(settings.get("min_amount") or 0)

        await query.edit_message_text(
            "➕ شارژ کیف پول\n\n"
            "💳 کارت‌به‌کارت:\n"
            f"🏦 بانک: {settings.get('bank_name') or 'ثبت نشده'}\n"
            f"💳 شماره کارت: {settings.get('card_number') or 'ثبت نشده'}\n"
            f"👤 صاحب حساب: {settings.get('card_holder') or 'ثبت نشده'}\n\n"
            f"💰 حداقل مبلغ: {money(minimum)}\n\n"
            f"{settings.get('payment_text') or 'مبلغ موردنظر را ارسال کنید.'}\n\n"
            "مبلغ شارژ را فقط به‌صورت عددی ارسال کنید.",
            reply_markup=back_user(),
        )

        clear_state(context)
        context.user_data["state"] = "deposit_amount"
        return

    if data == "wallet_tx":
        txs = get_transactions(user_id)

        if not txs:
            await query.edit_message_text(
                "📜 هنوز تراکنشی ثبت نشده است.",
                reply_markup=back_user(),
            )
            return

        lines = ["📜 آخرین تراکنش‌ها\n"]

        status_map = {
            "approved": "✅ تأیید",
            "pending": "⏳ در انتظار",
            "rejected": "❌ رد",
        }

        for tx in txs:
            status = status_map.get(tx["status"], tx["status"])
            sign = "+" if tx["type"] in ("deposit", "charge") else ""

            lines.append(
                f"#{tx['id']} | {sign}{money(tx['amount'])}\n"
                f"نوع: {tx['type']} | {status}\n"
                f"📝 {tx.get('description') or '-'}"
            )

        await query.edit_message_text(
            "\n\n".join(lines),
            reply_markup=back_user(),
        )
        return

    # ---------- HELP ----------
    if data == "help":
        await query.edit_message_text(
            "📚 راهنمای VirangarVPN\n\n"
            "🛒 خرید VPN:\n"
            "از بخش خرید، سرویس موردنظر را انتخاب کنید.\n\n"
            "💰 کیف پول:\n"
            "موجودی خود را مشاهده و با کارت‌به‌کارت شارژ کنید.\n\n"
            "🛡 سرویس‌های من:\n"
            "سرویس‌های خریداری‌شده و وضعیت آن‌ها را ببینید.\n\n"
            "🎫 پشتیبانی:\n"
            "برای ارتباط با پشتیبانی تیکت ایجاد کنید.",
            reply_markup=back_user(),
        )
        return

    # ---------- SUPPORT ----------
    if data == "support":
        await query.edit_message_text(
            "🎫 پشتیبانی\n\n"
            "اگر مشکلی دارید یک تیکت جدید ایجاد کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ تیکت جدید", callback_data="ticket_new")],
                [InlineKeyboardButton("📂 تیکت‌های من", callback_data="ticket_list")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")],
            ]),
        )
        return

    if data == "ticket_new":
        clear_state(context)
        context.user_data["state"] = "ticket_subject"

        await query.edit_message_text(
            "🎫 تیکت جدید\n\n"
            "موضوع تیکت را بفرستید.",
            reply_markup=back_user(),
        )
        return

    if data == "ticket_list":
        tickets = get_user_tickets(user_id)

        if not tickets:
            await query.edit_message_text(
                "📂 هنوز تیکتی ندارید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ تیکت جدید", callback_data="ticket_new")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="support")],
                ]),
            )
            return

        buttons = []
        for t in tickets[:30]:
            icon = "🟢" if t["status"] == "open" else "⚪"
            buttons.append([
                InlineKeyboardButton(
                    f"{icon} #{t['id']} {t.get('subject') or 'بدون موضوع'}",
                    callback_data=f"ticket_open_{t['id']}",
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="support")])

        await query.edit_message_text(
            "📂 تیکت‌های من\n\n"
            "تیکت موردنظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("ticket_open_"):
        ticket_id = int(data.split("_")[-1])
        ticket = get_ticket(ticket_id)

        if not ticket or int(ticket["user_id"]) != user_id:
            await query.edit_message_text(
                "❌ تیکت پیدا نشد.",
                reply_markup=back_user(),
            )
            return

        messages = get_ticket_messages(ticket_id)
        lines = [
            f"🎫 تیکت #{ticket_id}",
            f"📌 موضوع: {ticket.get('subject') or '-'}",
            f"📍 وضعیت: {ticket['status']}",
            "",
        ]

        for m in messages[-15:]:
            role = "شما" if m["sender_role"] == "user" else "پشتیبانی"
            lines.append(f"{role}: {m['message']}")

        buttons = []

        if ticket["status"] == "open":
            buttons.append([
                InlineKeyboardButton(
                    "💬 پاسخ",
                    callback_data=f"ticket_reply_{ticket_id}",
                ),
                InlineKeyboardButton(
                    "🔒 بستن",
                    callback_data=f"ticket_close_{ticket_id}",
                ),
            ])

        buttons.append([InlineKeyboardButton("🔙 تیکت‌ها", callback_data="ticket_list")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("ticket_reply_"):
        ticket_id = int(data.split("_")[-1])
        ticket = get_ticket(ticket_id)

        if not ticket or int(ticket["user_id"]) != user_id:
            return

        if ticket["status"] != "open":
            await query.edit_message_text(
                "⚪ این تیکت بسته است.",
                reply_markup=back_user(),
            )
            return

        clear_state(context)
        context.user_data["ticket_reply_mode"] = ticket_id

        await query.edit_message_text(
            f"💬 پاسخ به تیکت #{ticket_id}\n\n"
            "پیام خود را ارسال کنید.",
            reply_markup=back_user(),
        )
        return

    if data.startswith("ticket_close_"):
        ticket_id = int(data.split("_")[-1])
        ticket = get_ticket(ticket_id)

        if ticket and int(ticket["user_id"]) == user_id:
            set_ticket_status(ticket_id, "closed")

        await query.edit_message_text(
            "🔒 تیکت بسته شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 تیکت‌های من", callback_data="ticket_list")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="support")],
            ]),
        )
        return


# =========================================================
# MESSAGE ROUTER
# =========================================================

async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    # Always register user.
    add_user(user)

    # ---------------- BROADCAST ----------------
    if is_admin(user.id) and context.user_data.get("broadcast_mode"):
        context.user_data.pop("broadcast_mode", None)

        sent = 0
        failed = 0

        for target_id in get_all_users():
            try:
                await context.bot.copy_message(
                    chat_id=target_id,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id,
                )
                sent += 1
            except Exception:
                failed += 1

        await message.reply_text(
            "📢 ارسال همگانی تمام شد.\n\n"
            f"✅ موفق: {sent}\n"
            f"❌ ناموفق: {failed}",
            reply_markup=admin_menu(),
        )
        return

    # ---------------- ADMIN CHANNEL ADD ----------------
    if is_admin(user.id) and context.user_data.get("channel_add_mode"):
        if not message.text:
            await message.reply_text("❌ فقط متن/ID کانال را ارسال کنید.")
            return

        raw = message.text.strip()
        try:
            chat_id = int(raw)
        except ValueError:
            await message.reply_text(
                "❌ ID کانال باید عددی باشد.\nمثال: -1001234567890"
            )
            return

        try:
            chat = await context.bot.get_chat(chat_id)
            title = chat.title or ""
            username = chat.username or ""
            invite_link = ""

            if username:
                invite_link = f"https://t.me/{username}"

            db_execute(
                """
                INSERT OR REPLACE INTO channels
                (chat_id, title, username, invite_link, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    str(chat_id),
                    title,
                    username,
                    invite_link,
                    now(),
                ),
            )

            clear_state(context)

            await message.reply_text(
                "✅ کانال با موفقیت اضافه شد.\n\n"
                f"📢 {title or '-'}\n"
                f"🆔 {chat_id}",
                reply_markup=admin_menu(),
            )
        except Exception as exc:
            logger.exception("Channel add failed")
            await message.reply_text(
                "❌ نتوانستم کانال را دریافت کنم.\n\n"
                "مطمئن شوید ID درست است و ربات داخل کانال دسترسی لازم را دارد.\n\n"
                f"جزئیات: {exc}"
            )
        return

    # ---------------- ADMIN ADD ----------------
    if is_admin(user.id) and context.user_data.get("admin_add_mode"):
        if user.id != SUPER_ADMIN_ID:
            clear_state(context)
            await message.reply_text("⛔ فقط سوپر ادمین می‌تواند مدیر اضافه کند.")
            return

        if not message.text or not message.text.strip().isdigit():
            await message.reply_text("❌ User ID باید یک عدد باشد.")
            return

        target_id = int(message.text.strip())

        try:
            chat = await context.bot.get_chat(target_id)
            add_admin(
                target_id,
                chat.username or "",
                chat.first_name or chat.title or "",
            )
        except Exception:
            add_admin(target_id, "", "")

        clear_state(context)

        await message.reply_text(
            f"✅ کاربر {target_id} به مدیران اضافه شد.",
            reply_markup=admin_menu(),
        )
        return

    # ---------------- PANEL ADD ----------------
    if is_admin(user.id) and context.user_data.get("panel_add_step"):
        step = context.user_data["panel_add_step"]
        text = (message.text or "").strip()

        if step == "name":
            if not text:
                await message.reply_text("❌ نام پنل خالی نباشد.")
                return
            context.user_data["panel_name"] = text
            context.user_data["panel_add_step"] = "price"
            await message.reply_text("مرحله 2 از 6\n💰 قیمت را به تومان و فقط عدد ارسال کنید.")
            return

        if step == "price":
            if not text.isdigit():
                await message.reply_text("❌ قیمت باید عدد باشد.")
                return
            context.user_data["panel_price"] = int(text)
            context.user_data["panel_add_step"] = "duration"
            await message.reply_text("مرحله 3 از 6\n⏱ مدت سرویس را بنویسید. مثال: 30 روز")
            return

        if step == "duration":
            context.user_data["panel_duration"] = text
            context.user_data["panel_add_step"] = "volume"
            await message.reply_text("مرحله 4 از 6\n📦 حجم سرویس را بنویسید. مثال: 100GB")
            return

        if step == "volume":
            context.user_data["panel_volume"] = text
            context.user_data["panel_add_step"] = "max_users"
            await message.reply_text("مرحله 5 از 6\n👥 ظرفیت را فقط به‌صورت عدد ارسال کنید.")
            return

        if step == "max_users":
            if not text.isdigit():
                await message.reply_text("❌ ظرفیت باید عدد باشد.")
                return
            context.user_data["panel_max_users"] = int(text)
            context.user_data["panel_add_step"] = "description"
            await message.reply_text("مرحله 6 از 6\n📝 توضیحات پنل را ارسال کنید.")
            return

        if step == "description":
            add_panel(
                context.user_data["panel_name"],
                context.user_data["panel_price"],
                context.user_data["panel_duration"],
                context.user_data["panel_volume"],
                context.user_data["panel_max_users"],
                text,
            )

            clear_state(context)

            await message.reply_text(
                "✅ پنل با موفقیت ساخته شد.",
                reply_markup=admin_menu(),
            )
            return

    # ---------------- PANEL EDIT ----------------
    if is_admin(user.id) and context.user_data.get("panel_edit_id"):
        panel_id = context.user_data["panel_edit_id"]
        step = context.user_data.get("panel_edit_step")
        text = (message.text or "").strip()

        panel = get_panel(panel_id)
        if not panel:
            clear_state(context)
            await message.reply_text("❌ پنل پیدا نشد.")
            return

        if step == "name":
            context.user_data["edit_name"] = text
            context.user_data["panel_edit_step"] = "price"
            await message.reply_text("2/6 💰 قیمت جدید را ارسال کنید.")
            return

        if step == "price":
            if not text.isdigit():
                await message.reply_text("❌ قیمت باید عدد باشد.")
                return
            context.user_data["edit_price"] = int(text)
            context.user_data["panel_edit_step"] = "duration"
            await message.reply_text("3/6 ⏱ مدت جدید را ارسال کنید.")
            return

        if step == "duration":
            context.user_data["edit_duration"] = text
            context.user_data["panel_edit_step"] = "volume"
            await message.reply_text("4/6 📦 حجم جدید را ارسال کنید.")
            return

        if step == "volume":
            context.user_data["edit_volume"] = text
            context.user_data["panel_edit_step"] = "max_users"
            await message.reply_text("5/6 👥 ظرفیت جدید را ارسال کنید.")
            return

        if step == "max_users":
            if not text.isdigit():
                await message.reply_text("❌ ظرفیت باید عدد باشد.")
                return
            context.user_data["edit_max_users"] = int(text)
            context.user_data["panel_edit_step"] = "description"
            await message.reply_text("6/6 📝 توضیحات جدید را ارسال کنید.")
            return

        if step == "description":
            update_panel(
                panel_id,
                context.user_data["edit_name"],
                context.user_data["edit_price"],
                context.user_data["edit_duration"],
                context.user_data["edit_volume"],
                context.user_data["edit_max_users"],
                text,
            )
            clear_state(context)

            await message.reply_text(
                "✅ پنل ویرایش شد.",
                reply_markup=admin_menu(),
            )
            return

    # ---------------- PAYMENT SETTINGS ----------------
    if is_admin(user.id) and context.user_data.get("payment_edit_step"):
        if user.id != SUPER_ADMIN_ID:
            clear_state(context)
            await message.reply_text("⛔ دسترسی ندارید.")
            return

        step = context.user_data["payment_edit_step"]
        text = (message.text or "").strip()

        if step == "card_number":
            context.user_data["pay_card"] = text
            context.user_data["payment_edit_step"] = "bank"
            await message.reply_text("2/5 🏦 نام بانک را ارسال کنید.")
            return

        if step == "bank":
            context.user_data["pay_bank"] = text
            context.user_data["payment_edit_step"] = "holder"
            await message.reply_text("3/5 👤 نام صاحب کارت را ارسال کنید.")
            return

        if step == "holder":
            context.user_data["pay_holder"] = text
            context.user_data["payment_edit_step"] = "text"
            await message.reply_text("4/5 📝 متن راهنمای پرداخت را ارسال کنید.")
            return

        if step == "text":
            context.user_data["pay_text"] = text
            context.user_data["payment_edit_step"] = "min"
            await message.reply_text("5/5 💰 حداقل مبلغ شارژ را فقط عددی ارسال کنید.")
            return

        if step == "min":
            if not text.isdigit():
                await message.reply_text("❌ مبلغ باید عدد باشد.")
                return

            set_payment_settings(
                card_number=context.user_data["pay_card"],
                bank_name=context.user_data["pay_bank"],
                card_holder=context.user_data["pay_holder"],
                payment_text=context.user_data["pay_text"],
                min_amount=int(text),
            )

            clear_state(context)

            await message.reply_text(
                "✅ تنظیمات پرداخت ذخیره شد.",
                reply_markup=admin_menu(),
            )
            return

    # ---------------- TICKET SUBJECT ----------------
    if context.user_data.get("state") == "ticket_subject":
        subject = (message.text or "").strip()

        if not subject:
            await message.reply_text("❌ موضوع را وارد کنید.")
            return

        ticket_id = create_ticket(user.id, subject)

        context.user_data.pop("state", None)
        context.user_data["state"] = "ticket_message"
        context.user_data["ticket_id"] = ticket_id

        await message.reply_text(
            f"🎫 تیکت #{ticket_id} ساخته شد.\n\n"
            "حالا متن مشکل یا درخواست خود را ارسال کنید."
        )
        return

    # ---------------- TICKET FIRST MESSAGE ----------------
    if context.user_data.get("state") == "ticket_message":
        ticket_id = context.user_data.get("ticket_id")
        text = message.text or message.caption or ""

        if not text:
            await message.reply_text("❌ لطفاً متن پیام را ارسال کنید.")
            return

        add_ticket_message(ticket_id, user.id, "user", text)

        context.user_data.pop("state", None)
        context.user_data.pop("ticket_id", None)

        for admin_id in admin_ids():
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🎫 تیکت جدید #{ticket_id}\n\n"
                    f"👤 کاربر: {user.first_name or '-'}\n"
                    f"🆔 {user.id}\n"
                    f"📝 {text}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "🎫 مشاهده تیکت",
                            callback_data=f"at_open_{ticket_id}",
                        )]
                    ]),
                )
            except Exception:
                pass

        await message.reply_text(
            "✅ پیام شما ثبت شد.\n"
            "پشتیبانی در اولین فرصت پاسخ می‌دهد.",
            reply_markup=user_menu(),
        )
        return

    # ---------------- TICKET USER REPLY ----------------
    if context.user_data.get("ticket_reply_mode"):
        ticket_id = int(context.user_data["ticket_reply_mode"])
        ticket = get_ticket(ticket_id)

        if not ticket or int(ticket["user_id"]) != user.id:
            clear_state(context)
            await message.reply_text("❌ تیکت پیدا نشد.")
            return

        if ticket["status"] != "open":
            clear_state(context)
            await message.reply_text("⚪ این تیکت بسته شده است.")
            return

        text = message.text or message.caption or ""
        if not text:
            await message.reply_text("❌ فقط متن پیام را ارسال کنید.")
            return

        add_ticket_message(ticket_id, user.id, "user", text)
        clear_state(context)

        for admin_id in admin_ids():
            try:
                await context.bot.send_message(
                    admin_id,
                    f"💬 پاسخ جدید در تیکت #{ticket_id}\n\n"
                    f"👤 کاربر: {user.first_name or '-'}\n"
                    f"🆔 {user.id}\n\n"
                    f"{text}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "🎫 مشاهده تیکت",
                            callback_data=f"at_open_{ticket_id}",
                        )]
                    ]),
                )
            except Exception:
                pass

        await message.reply_text(
            "✅ پاسخ شما ثبت شد.",
            reply_markup=user_menu(),
        )
        return

    # ---------------- ADMIN TICKET REPLY ----------------
    if is_admin(user.id) and context.user_data.get("ticket_reply_mode"):
        # Kept for compatibility; admin reply uses the same state name.
        ticket_id = int(context.user_data["ticket_reply_mode"])
        ticket = get_ticket(ticket_id)

        if not ticket:
            clear_state(context)
            await message.reply_text("❌ تیکت پیدا نشد.")
            return

        text = message.text or message.caption or ""
        if not text:
            await message.reply_text("❌ متن پاسخ را ارسال کنید.")
            return

        add_ticket_message(ticket_id, user.id, "admin", text)
        clear_state(context)

        try:
            await context.bot.send_message(
                ticket["user_id"],
                f"💬 پاسخ پشتیبانی در تیکت #{ticket_id}\n\n"
                f"{text}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🎫 مشاهده تیکت",
                        callback_data=f"ticket_open_{ticket_id}",
                    )]
                ]),
            )
        except Exception:
            pass

        await message.reply_text(
            "✅ پاسخ ارسال شد.",
            reply_markup=admin_menu(),
        )
        return

    # ---------------- DEPOSIT AMOUNT ----------------
    if context.user_data.get("state") == "deposit_amount":
        text = (message.text or "").strip()

        if not text.isdigit():
            await message.reply_text("❌ مبلغ باید فقط عدد باشد.")
            return

        amount = int(text)
        settings = get_payment_settings()
        minimum = int(settings.get("min_amount") or 0)

        if amount <= 0:
            await message.reply_text("❌ مبلغ نامعتبر است.")
            return

        if amount < minimum:
            await message.reply_text(
                f"❌ حداقل مبلغ شارژ {money(minimum)} است."
            )
            return

        tx_id = add_transaction(
            user.id,
            amount,
            "deposit",
            "pending",
            "درخواست شارژ کارت‌به‌کارت",
        )

        context.user_data["deposit_transaction_id"] = tx_id
        context.user_data["deposit_amount"] = amount
        context.user_data["state"] = "deposit_receipt"

        await message.reply_text(
            "💳 درخواست شارژ ثبت شد.\n\n"
            f"💰 مبلغ: {money(amount)}\n"
            f"🧾 شماره درخواست: #{tx_id}\n\n"
            "حالا تصویر رسید پرداخت را ارسال کنید."
        )
        return

    # ---------------- DEPOSIT RECEIPT ----------------
    if context.user_data.get("state") == "deposit_receipt":
        tx_id = context.user_data.get("deposit_transaction_id")
        amount = context.user_data.get("deposit_amount")

        if not tx_id:
            clear_state(context)
            await message.reply_text("❌ درخواست شارژ پیدا نشد.")
            return

        # Send receipt to all admins with approval buttons.
        for admin_id in admin_ids():
            try:
                caption = (
                    "💳 درخواست شارژ جدید\n\n"
                    f"🧾 درخواست: #{tx_id}\n"
                    f"👤 کاربر: {user.first_name or '-'}\n"
                    f"🆔 ID: {user.id}\n"
                    f"💰 مبلغ: {money(amount)}\n\n"
                    "رسید بالا را بررسی کنید."
                )

                if message.photo:
                    await context.bot.send_photo(
                        admin_id,
                        message.photo[-1].file_id,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(
                                    "✅ تأیید",
                                    callback_data=f"dep_approve_{tx_id}",
                                ),
                                InlineKeyboardButton(
                                    "❌ رد",
                                    callback_data=f"dep_reject_{tx_id}",
                                ),
                            ]
                        ]),
                    )
                elif message.document:
                    await context.bot.send_document(
                        admin_id,
                        message.document.file_id,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(
                                    "✅ تأیید",
                                    callback_data=f"dep_approve_{tx_id}",
                                ),
                                InlineKeyboardButton(
                                    "❌ رد",
                                    callback_data=f"dep_reject_{tx_id}",
                                ),
                            ]
                        ]),
                    )
                else:
                    await context.bot.send_message(
                        admin_id,
                        caption + "\n\n"
                        "⚠️ کاربر فایل رسید نفرستاده است.",
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(
                                    "✅ تأیید",
                                    callback_data=f"dep_approve_{tx_id}",
                                ),
                                InlineKeyboardButton(
                                    "❌ رد",
                                    callback_data=f"dep_reject_{tx_id}",
                                ),
                            ]
                        ]),
                    )
            except Exception:
                logger.exception("Could not forward deposit receipt")

        clear_state(context)

        await message.reply_text(
            "✅ رسید شما برای مدیریت ارسال شد.\n\n"
            "⏳ بعد از بررسی، نتیجه از طریق ربات اعلام می‌شود.",
            reply_markup=user_menu(),
        )
        return

    # ---------------- ADMIN REPLY STATE ----------------
    # This is intentionally after user ticket states. Admin ticket reply
    # is set by callback using ticket_reply_mode.
    if is_admin(user.id) and context.user_data.get("ticket_reply_mode"):
        return

    # ---------------- BLOCKED USER ----------------
    row = get_user_row(user.id)
    if row and row["is_blocked"]:
        await message.reply_text("🚫 حساب شما توسط مدیریت مسدود شده است.")
        return

    # ---------------- DEFAULT ----------------
    if not await require_membership(update, context):
        return

    await message.reply_text(
        "لطفاً از دکمه‌های منو استفاده کنید.",
        reply_markup=admin_menu() if is_admin(user.id) else user_menu(),
    )


# =========================================================
# ERROR
# =========================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception(
        "Unhandled exception",
        exc_info=context.error,
    )


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Put it in .env")

    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    application.add_handler(CallbackQueryHandler(callback_handler))

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            message_router,
        )
    )

    application.add_error_handler(error_handler)

    logger.info("VirangarVPN bot starting...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
