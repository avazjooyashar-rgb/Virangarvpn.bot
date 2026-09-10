# =========================
# MENU ACTION LOGGER
# =========================

from datetime import datetime

from database import connect


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def init_menu_action_logs():
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER,
            action_type TEXT,
            action_value TEXT,
            success INTEGER DEFAULT 1,
            message TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    db.commit()
    db.close()


def log_menu_action(
    user_id,
    item_id,
    action_type,
    action_value="",
    success=True,
    message="",
):
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        INSERT INTO menu_action_logs (
            user_id,
            item_id,
            action_type,
            action_value,
            success,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            item_id,
            action_type,
            action_value or "",
            1 if success else 0,
            message or "",
            _now(),
        ),
    )

    db.commit()
    db.close()


def get_menu_action_logs(
    limit=100,
    user_id=None,
    item_id=None,
):
    db = connect()
    cur = db.cursor()

    query = """
        SELECT *
        FROM menu_action_logs
        WHERE 1=1
    """

    params = []

    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    if item_id is not None:
        query += " AND item_id = ?"
        params.append(item_id)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))

    cur.execute(query, params)

    rows = cur.fetchall()
    db.close()

    return [dict(row) for row in rows]


def count_menu_action_logs(
    user_id=None,
    item_id=None,
):
    db = connect()
    cur = db.cursor()

    query = """
        SELECT COUNT(*)
        FROM menu_action_logs
        WHERE 1=1
    """

    params = []

    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    if item_id is not None:
        query += " AND item_id = ?"
        params.append(item_id)

    cur.execute(query, params)

    result = cur.fetchone()
    db.close()

    return int(result[0] or 0)


def clear_menu_action_logs():
    db = connect()
    cur = db.cursor()

    cur.execute("DELETE FROM menu_action_logs")

    db.commit()
    deleted = cur.rowcount

    db.close()

    return deleted


def get_menu_action_log_summary():
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS successful,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failed
        FROM menu_action_logs
        """
    )

    row = cur.fetchone()
    db.close()

    return {
        "total": int(row["total"] or 0),
        "successful": int(row["successful"] or 0),
        "failed": int(row["failed"] or 0),
    }


def get_menu_action_logger_status():
    return {
        "module": "menu_action_logger",
        "status": "ready",
        "database_logging": True,
        "supports_user_filter": True,
        "supports_item_filter": True,
    }


init_menu_action_logs()
