import sqlite3
from datetime import datetime


DATABASE = "virangar.db"


def connect():
    return sqlite3.connect(DATABASE)


def init_db():
    db = connect()
    cursor = db.cursor()

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

    db.commit()
    db.close()


def add_user(user):
    now = datetime.utcnow().isoformat()

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
            now,
            now,
        ),
    )

    db.commit()
    db.close()


def get_stats():
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE is_blocked = 0
        """
    )
    active = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE date(joined_at) = date('now')
        """
    )
    today = cursor.fetchone()[0]

    db.close()

    return {
        "total": total,
        "active": active,
        "today": today,
    }


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

    users = [
        row[0]
        for row in cursor.fetchall()
    ]

    db.close()

    return users
