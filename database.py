import sqlite3
from datetime import datetime


DATABASE = "virangar.db"


def connect():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def now():
    return datetime.utcnow().isoformat()


# =========================
# INIT DATABASE
# =========================

def init_db():
    db = connect()
    cursor = db.cursor()

    # کاربران
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            is_blocked INTEGER DEFAULT 0
        )
        """
    )

    # ادمین‌ها
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            added_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        """
    )

    # دسترسی ادمین‌ها
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            permission TEXT NOT NULL,
            UNIQUE(admin_id, permission)
        )
        """
    )

    # کانال‌های اجباری
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL UNIQUE,
            title TEXT,
            username TEXT,
            invite_link TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    # پنل‌های فروش
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS panels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            duration TEXT,
            volume TEXT,
            max_users INTEGER DEFAULT 1,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    # کیف پول
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # تراکنش‌ها
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # تنظیمات پرداخت
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            card_number TEXT,
            bank_name TEXT,
            card_holder TEXT,
            payment_text TEXT,
            min_amount INTEGER DEFAULT 0
        )
        """
    )

    # تیکت‌ها
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # پیام‌های تیکت
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # سرویس‌های خریداری‌شده
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            panel_id INTEGER,
            panel_name TEXT,
            price INTEGER DEFAULT 0,
            duration TEXT,
            volume TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            config TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT
        )
        """
    )

    db.commit()
    db.close()


# =========================
# USERS
# =========================

def add_user(user):
    current_time = now()

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO users (
            id,
            username,
            first_name,
            joined_at,
            last_seen
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_seen = excluded.last_seen
        """,
        (
            user.id,
            user.username,
            user.first_name,
            current_time,
            current_time,
        ),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO wallets (
            user_id,
            balance
        )
        VALUES (?, 0)
        """,
        (user.id,),
    )

    db.commit()
    db.close()


def get_all_users():
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE is_blocked = 0
        """
    )

    users = [row["id"] for row in cursor.fetchall()]

    db.close()

    return users


def get_stats():
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS count FROM users"
    )
    total = cursor.fetchone()["count"]

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE is_blocked = 0
        """
    )
    active = cursor.fetchone()["count"]

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE date(joined_at) = date('now')
        """
    )
    today = cursor.fetchone()["count"]

    db.close()

    return {
        "total": total,
        "active": active,
        "today": today,
    }


# =========================
# PANELS
# =========================

def get_panels(active_only=True):
    db = connect()
    cursor = db.cursor()

    if active_only:
        cursor.execute(
            """
            SELECT *
            FROM panels
            WHERE is_active = 1
            ORDER BY id
            """
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM panels
            ORDER BY id
            """
        )

    panels = [dict(row) for row in cursor.fetchall()]

    db.close()

    return panels


def get_panel(panel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM panels
        WHERE id = ?
        """,
        (panel_id,),
    )

    row = cursor.fetchone()

    db.close()

    return dict(row) if row else None


# =========================
# WALLET
# =========================

def get_balance(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT balance
        FROM wallets
        WHERE user_id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    db.close()

    return row["balance"] if row else 0


def set_balance(user_id, balance):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO wallets (user_id, balance)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET balance = excluded.balance
        """,
        (user_id, balance),
    )

    db.commit()
    db.close()


def add_balance(user_id, amount):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO wallets (user_id, balance)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET balance = balance + excluded.balance
        """,
        (user_id, amount),
    )

    db.commit()
    db.close()


# =========================
# CHANNELS
# =========================

def get_channels(active_only=True):
    db = connect()
    cursor = db.cursor()

    if active_only:
        cursor.execute(
            """
            SELECT *
            FROM channels
            WHERE is_active = 1
            ORDER BY id
            """
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM channels
            ORDER BY id
            """
        )

    channels = [dict(row) for row in cursor.fetchall()]

    db.close()

    return channels


def add_channel(
    chat_id,
    title="",
    username="",
    invite_link="",
):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO channels (
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
            str(chat_id),
            title,
            username,
            invite_link,
            now(),
        ),
    )

    db.commit()
    db.close()


def delete_channel(channel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM channels
        WHERE id = ?
        """,
        (channel_id,),
    )

    db.commit()
    db.close()


# =========================
# PAYMENT SETTINGS
# =========================

def get_payment_settings():
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM payment_settings
        WHERE id = 1
        """
    )

    row = cursor.fetchone()

    db.close()

    if not row:
        return {
            "card_number": "",
            "bank_name": "",
            "card_holder": "",
            "payment_text": "",
            "min_amount": 0,
        }

    return dict(row)


def set_payment_settings(
    card_number="",
    bank_name="",
    card_holder="",
    payment_text="",
    min_amount=0,
):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO payment_settings (
            id,
            card_number,
            bank_name,
            card_holder,
            payment_text,
            min_amount
        )
        VALUES (1, ?, ?, ?, ?, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            card_number = excluded.card_number,
            bank_name = excluded.bank_name,
            card_holder = excluded.card_holder,
            payment_text = excluded.payment_text,
            min_amount = excluded.min_amount
        """,
        (
            card_number,
            bank_name,
            card_holder,
            payment_text,
            min_amount,
        ),
    )

    db.commit()
    db.close()


# =========================
# ADMINS
# =========================

def add_admin(
    user_id,
    username="",
    first_name="",
):
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
            user_id,
            username,
            first_name,
            now(),
        ),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO admin_permissions (
            admin_id,
            permission
        )
        VALUES (?, 'all')
        """,
        (user_id,),
    )

    db.commit()
    db.close()


def remove_admin(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM admins
        WHERE user_id = ?
        """,
        (user_id,),
    )

    cursor.execute(
        """
        DELETE FROM admin_permissions
        WHERE admin_id = ?
        """,
        (user_id,),
    )

    db.commit()
    db.close()


def get_admins():
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM admins
        WHERE is_active = 1
        ORDER BY added_at
        """
    )

    admins = [dict(row) for row in cursor.fetchall()]

    db.close()

    return admins


def is_admin_db(user_id):
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
# TRANSACTIONS
# =========================

def add_transaction(
    user_id,
    amount,
    transaction_type,
    status,
    description="",
):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO transactions (
            user_id,
            amount,
            type,
            status,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            amount,
            transaction_type,
            status,
            description,
            now(),
        ),
    )

    transaction_id = cursor.lastrowid

    db.commit()
    db.close()

    return transaction_id


def get_transactions(user_id, limit=20):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )

    transactions = [dict(row) for row in cursor.fetchall()]

    db.close()

    return transactions


# =========================
# SERVICES
# =========================

def get_user_services(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM services
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    services = [dict(row) for row in cursor.fetchall()]

    db.close()

    return services


def add_service(
    user_id,
    panel_id,
    panel_name,
    price,
    duration,
    volume,
    status="pending",
    config="",
    expires_at=None,
):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO services (
            user_id,
            panel_id,
            panel_name,
            price,
            duration,
            volume,
            status,
            config,
            created_at,
            expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            panel_id,
            panel_name,
            price,
            duration,
            volume,
            status,
            config,
            now(),
            expires_at,
        ),
    )

    service_id = cursor.lastrowid

    db.commit()
    db.close()

    return service_id


# =========================
# TICKETS
# =========================

def create_ticket(
    user_id,
    subject="",
):
    current_time = now()

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (
            user_id,
            subject,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, 'open', ?, ?)
        """,
        (
            user_id,
            subject,
            current_time,
            current_time,
        ),
    )

    ticket_id = cursor.lastrowid

    db.commit()
    db.close()

    return ticket_id


def get_user_tickets(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tickets
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    tickets = [dict(row) for row in cursor.fetchall()]

    db.close()

    return tickets


def add_ticket_message(
    ticket_id,
    sender_id,
    sender_role,
    message,
):
    db = connect()
    cursor = db.cursor()

    current_time = now()

    cursor.execute(
        """
        INSERT INTO ticket_messages (
            ticket_id,
            sender_id,
            sender_role,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            sender_id,
            sender_role,
            message,
            current_time,
        ),
    )

    cursor.execute(
        """
        UPDATE tickets
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            current_time,
            ticket_id,
        ),
    )

    db.commit()
    db.close()


def get_ticket_messages(ticket_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM ticket_messages
        WHERE ticket_id = ?
        ORDER BY id
        """,
        (ticket_id,),
    )

    messages = [dict(row) for row in cursor.fetchall()]

    db.close()

    return messages


# =========================
# STARTUP
# =========================

if __name__ == "__main__":
    init_db()
    print("VirangarVPN database initialized successfully.")
