import sqlite3
from datetime import datetime

DATABASE = "virangar.db"


# =========================
# DATABASE CONNECTION
# =========================

def connect():
    db = sqlite3.connect(DATABASE, timeout=30)
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

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    # ADMINS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            added_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    # ADMIN PERMISSIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            permission TEXT NOT NULL,
            UNIQUE(admin_id, permission)
        )
    """)

    # CHANNELS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL UNIQUE,
            title TEXT,
            username TEXT,
            invite_link TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    # PANELS
    cursor.execute("""
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
    """)

    # WALLETS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
        )
    """)

    # TRANSACTIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # PAYMENT SETTINGS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            card_number TEXT,
            bank_name TEXT,
            card_holder TEXT,
            payment_text TEXT,
            min_amount INTEGER DEFAULT 0
        )
    """)

    # TICKETS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # TICKET MESSAGES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # SERVICES
    cursor.execute("""
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
    """)

    # =========================
    # FREE TRIAL SETTINGS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS free_trial_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            is_active INTEGER NOT NULL DEFAULT 1,
            volume_mb INTEGER NOT NULL DEFAULT 200,
            duration_hours INTEGER NOT NULL DEFAULT 24,
            panel_id INTEGER,
            updated_at TEXT NOT NULL
        )
    """)

    # =========================
    # FREE TRIALS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS free_trials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            service_id INTEGER,
            panel_id INTEGER,
            volume_mb INTEGER NOT NULL,
            duration_hours INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            expires_at TEXT
        )
    """)

    # INDEX
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_free_trials_user
        ON free_trials(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_services_user
        ON services(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user
        ON transactions(user_id)
    """)

    # ایجاد تنظیمات اولیه تست رایگان
    cursor.execute("""
        INSERT OR IGNORE INTO free_trial_settings (
            id,
            is_active,
            volume_mb,
            duration_hours,
            panel_id,
            updated_at
        )
        VALUES (1, 1, 200, 24, NULL, ?)
    """, (now(),))

    db.commit()
    db.close()


# =========================
# USERS
# =========================

def add_user(user):
    current_time = now()

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
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
    """, (
        user.id,
        user.username,
        user.first_name,
        current_time,
        current_time
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO wallets (
            user_id,
            balance
        )
        VALUES (?, 0)
    """, (user.id,))

    db.commit()
    db.close()


def get_all_users():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        WHERE is_blocked = 0
    """)

    users = [row["id"] for row in cursor.fetchall()]

    db.close()
    return users


def get_stats():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM users
    """)
    total = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE is_blocked = 0
    """)
    active = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE date(joined_at) = date('now')
    """)
    today = cursor.fetchone()["count"]

    db.close()

    return {
        "total": total,
        "active": active,
        "today": today
    }


# =========================
# PANELS
# =========================

def get_panels(active_only=True):
    db = connect()
    cursor = db.cursor()

    if active_only:
        cursor.execute("""
            SELECT *
            FROM panels
            WHERE is_active = 1
            ORDER BY id
        """)
    else:
        cursor.execute("""
            SELECT *
            FROM panels
            ORDER BY id
        """)

    panels = [dict(row) for row in cursor.fetchall()]

    db.close()
    return panels


def get_panel(panel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM panels
        WHERE id = ?
    """, (panel_id,))

    row = cursor.fetchone()

    db.close()

    return dict(row) if row else None


# =========================
# WALLET
# =========================

def get_balance(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT balance
        FROM wallets
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()

    db.close()

    return row["balance"] if row else 0


def set_balance(user_id, balance):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO wallets (
            user_id,
            balance
        )
        VALUES (?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            balance = excluded.balance
    """, (user_id, balance))

    db.commit()
    db.close()


def add_balance(user_id, amount):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO wallets (
            user_id,
            balance
        )
        VALUES (?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            balance = balance + excluded.balance
    """, (user_id, amount))

    db.commit()
    db.close()


# =========================
# CHANNELS
# =========================

def get_channels(active_only=True):
    db = connect()
    cursor = db.cursor()

    if active_only:
        cursor.execute("""
            SELECT *
            FROM channels
            WHERE is_active = 1
            ORDER BY id
        """)
    else:
        cursor.execute("""
            SELECT *
            FROM channels
            ORDER BY id
        """)

    channels = [dict(row) for row in cursor.fetchall()]

    db.close()
    return channels


def add_channel(
    chat_id,
    title="",
    username="",
    invite_link=""
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO channels (
            chat_id,
            title,
            username,
            invite_link,
            is_active,
            created_at
        )
        VALUES (?, ?, ?, ?, 1, ?)
    """, (
        str(chat_id),
        title,
        username,
        invite_link,
        now()
    ))

    db.commit()
    db.close()


def delete_channel(channel_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM channels
        WHERE id = ?
    """, (channel_id,))

    db.commit()
    db.close()


# =========================
# PAYMENT SETTINGS
# =========================

def get_payment_settings():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM payment_settings
        WHERE id = 1
    """)

    row = cursor.fetchone()

    db.close()

    if not row:
        return {
            "card_number": "",
            "bank_name": "",
            "card_holder": "",
            "payment_text": "",
            "min_amount": 0
        }

    return dict(row)


def set_payment_settings(
    card_number="",
    bank_name="",
    card_holder="",
    payment_text="",
    min_amount=0
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
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
    """, (
        card_number,
        bank_name,
        card_holder,
        payment_text,
        min_amount
    ))

    db.commit()
    db.close()


# =========================
# ADMINS
# =========================

def add_admin(
    user_id,
    username="",
    first_name=""
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO admins (
            user_id,
            username,
            first_name,
            added_at,
            is_active
        )
        VALUES (?, ?, ?, ?, 1)
    """, (
        user_id,
        username,
        first_name,
        now()
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO admin_permissions (
            admin_id,
            permission
        )
        VALUES (?, 'all')
    """, (user_id,))

    db.commit()
    db.close()


def remove_admin(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM admins
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("""
        DELETE FROM admin_permissions
        WHERE admin_id = ?
    """, (user_id,))

    db.commit()
    db.close()


def get_admins():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM admins
        WHERE is_active = 1
        ORDER BY added_at
    """)

    admins = [dict(row) for row in cursor.fetchall()]

    db.close()
    return admins


def is_admin_db(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT user_id
        FROM admins
        WHERE user_id = ?
        AND is_active = 1
    """, (user_id,))

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
    description=""
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO transactions (
            user_id,
            amount,
            type,
            status,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        amount,
        transaction_type,
        status,
        description,
        now()
    ))

    transaction_id = cursor.lastrowid

    db.commit()
    db.close()

    return transaction_id


def get_transactions(user_id, limit=20):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        user_id,
        limit
    ))

    transactions = [dict(row) for row in cursor.fetchall()]

    db.close()

    return transactions


# =========================
# SERVICES
# =========================

def get_user_services(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM services
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

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
    expires_at=None
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
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
    """, (
        user_id,
        panel_id,
        panel_name,
        price,
        duration,
        volume,
        status,
        config,
        now(),
        expires_at
    ))

    service_id = cursor.lastrowid

    db.commit()
    db.close()

    return service_id


# =========================
# TICKETS
# =========================

def create_ticket(
    user_id,
    subject=""
):
    current_time = now()

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO tickets (
            user_id,
            subject,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, 'open', ?, ?)
    """, (
        user_id,
        subject,
        current_time,
        current_time
    ))

    ticket_id = cursor.lastrowid

    db.commit()
    db.close()

    return ticket_id


def get_user_tickets(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    tickets = [dict(row) for row in cursor.fetchall()]

    db.close()

    return tickets


def add_ticket_message(
    ticket_id,
    sender_id,
    sender_role,
    message
):
    db = connect()
    cursor = db.cursor()

    current_time = now()

    cursor.execute("""
        INSERT INTO ticket_messages (
            ticket_id,
            sender_id,
            sender_role,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        ticket_id,
        sender_id,
        sender_role,
        message,
        current_time
    ))

    cursor.execute("""
        UPDATE tickets
        SET updated_at = ?
        WHERE id = ?
    """, (
        current_time,
        ticket_id
    ))

    db.commit()
    db.close()


def get_ticket_messages(ticket_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM ticket_messages
        WHERE ticket_id = ?
        ORDER BY id ASC
    """, (ticket_id,))

    messages = [dict(row) for row in cursor.fetchall()]

    db.close()

    return messages


# =========================
# FREE TRIAL
# =========================

def get_free_trial_settings():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM free_trial_settings
        WHERE id = 1
    """)

    row = cursor.fetchone()

    db.close()

    if not row:
        return {
            "id": 1,
            "is_active": 1,
            "volume_mb": 200,
            "duration_hours": 24,
            "panel_id": None,
            "updated_at": now()
        }

    return dict(row)


def update_free_trial_settings(
    is_active=None,
    volume_mb=None,
    duration_hours=None,
    panel_id=None
):
    current = get_free_trial_settings()

    if is_active is None:
        is_active = current["is_active"]

    if volume_mb is None:
        volume_mb = current["volume_mb"]

    if duration_hours is None:
        duration_hours = current["duration_hours"]

    if panel_id is None:
        panel_id = current["panel_id"]

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE free_trial_settings
        SET
            is_active = ?,
            volume_mb = ?,
            duration_hours = ?,
            panel_id = ?,
            updated_at = ?
        WHERE id = 1
    """, (
        int(is_active),
        int(volume_mb),
        int(duration_hours),
        panel_id,
        now()
    ))

    db.commit()
    db.close()


def has_free_trial(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id
        FROM free_trials
        WHERE user_id = ?
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()

    db.close()

    return row is not None


def get_free_trial(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM free_trials
        WHERE user_id = ?
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()

    db.close()

    return dict(row) if row else None


def claim_free_trial(user_id):
    """
    Atomic claim.
    هر کاربر فقط یک بار می‌تواند تست بگیرد.
    """

    db = connect()
    cursor = db.cursor()

    try:
        db.execute("BEGIN IMMEDIATE")

        # تنظیمات
        cursor.execute("""
            SELECT *
            FROM free_trial_settings
            WHERE id = 1
        """)

        settings = cursor.fetchone()

        if not settings:
            db.rollback()
            return None

        if int(settings["is_active"]) != 1:
            db.rollback()
            return None

        # قبلاً تست گرفته؟
        cursor.execute("""
            SELECT id
            FROM free_trials
            WHERE user_id = ?
            LIMIT 1
        """, (user_id,))

        existing = cursor.fetchone()

        if existing:
            db.rollback()
            return None

        current_time = datetime.utcnow()

        # ثبت تست
        cursor.execute("""
            INSERT INTO free_trials (
                user_id,
                service_id,
                panel_id,
                volume_mb,
                duration_hours,
                status,
                created_at,
                expires_at
            )
            VALUES (?, NULL, ?, ?, ?, 'pending', ?, ?)
        """, (
            user_id,
            settings["panel_id"],
            settings["volume_mb"],
            settings["duration_hours"],
            current_time.isoformat(),
            (
                current_time.replace(
                    microsecond=0
                )
            ).isoformat()
        ))

        trial_id = cursor.lastrowid

        db.commit()

        return {
            "id": trial_id,
            "user_id": user_id,
            "panel_id": settings["panel_id"],
            "volume_mb": settings["volume_mb"],
            "duration_hours": settings["duration_hours"],
            "status": "pending"
        }

    except sqlite3.IntegrityError:
        db.rollback()
        return None

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_free_trial_service(
    trial_id,
    service_id,
    status="active",
    expires_at=None
):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE free_trials
        SET
            service_id = ?,
            status = ?,
            expires_at = ?
        WHERE id = ?
    """, (
        service_id,
        status,
        expires_at,
        trial_id
    ))

    db.commit()
    db.close()
