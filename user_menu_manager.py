# =========================================================
# VIRANGAR VPN
# USER MENU MANAGER
# =========================================================
#
# مدیریت داینامیک منوی کاربر
#
# امکانات:
#   - افزودن دکمه
#   - ویرایش دکمه
#   - حذف دکمه
#   - فعال / غیرفعال کردن
#   - تغییر ترتیب
#   - پشتیبانی از زیرمنو
#   - ذخیره کامل در SQLite
#
# این فایل هنوز به bot.py متصل نمی‌شود.
# اتصال به bot.py را در مرحله بعد انجام می‌دهیم.
# =========================================================

from database import connect


# =========================================================
# DATABASE INIT
# =========================================================

def init_user_menu_table():
    """
    ساخت جدول منوی کاربر در صورت نبودن.
    """

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,
            icon TEXT DEFAULT '',

            action_type TEXT NOT NULL DEFAULT 'callback',
            action_value TEXT DEFAULT '',

            parent_id INTEGER DEFAULT NULL,

            sort_order INTEGER NOT NULL DEFAULT 0,

            is_active INTEGER NOT NULL DEFAULT 1,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (parent_id)
                REFERENCES user_menu(id)
                ON DELETE CASCADE
        )
        """
    )

    db.commit()
    db.close()


# =========================================================
# CREATE
# =========================================================

def add_menu_item(
    title,
    action_value="",
    icon="",
    action_type="callback",
    parent_id=None,
    sort_order=None,
    is_active=True,
):
    """
    افزودن یک دکمه جدید به منوی کاربر.

    مثال:

    add_menu_item(
        title="خرید VPN",
        icon="🛒",
        action_value="buy_vpn"
    )
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    # اگر ترتیب مشخص نشده، آخر لیست قرار بگیرد
    if sort_order is None:
        if parent_id is None:
            cur.execute(
                """
                SELECT COALESCE(MAX(sort_order), 0) + 1
                FROM user_menu
                WHERE parent_id IS NULL
                """
            )
        else:
            cur.execute(
                """
                SELECT COALESCE(MAX(sort_order), 0) + 1
                FROM user_menu
                WHERE parent_id = ?
                """,
                (parent_id,),
            )

        sort_order = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO user_menu
        (
            title,
            icon,
            action_type,
            action_value,
            parent_id,
            sort_order,
            is_active,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            title,
            icon,
            action_type,
            action_value,
            parent_id,
            sort_order,
            1 if is_active else 0,
        ),
    )

    item_id = cur.lastrowid

    db.commit()
    db.close()

    return item_id


# =========================================================
# READ
# =========================================================

def get_menu_item(item_id):
    """
    دریافت یک دکمه بر اساس ID.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT *
        FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    )

    row = cur.fetchone()

    db.close()

    if not row:
        return None

    return dict(row)


def get_all_menu_items(include_disabled=True):
    """
    دریافت تمام دکمه‌های منو.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    if include_disabled:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            ORDER BY
                CASE
                    WHEN parent_id IS NULL THEN 0
                    ELSE 1
                END,
                parent_id,
                sort_order,
                id
            """
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE is_active = 1
            ORDER BY
                CASE
                    WHEN parent_id IS NULL THEN 0
                    ELSE 1
                END,
                parent_id,
                sort_order,
                id
            """
        )

    rows = cur.fetchall()

    db.close()

    return [dict(row) for row in rows]


def get_main_menu_items(include_disabled=False):
    """
    دریافت دکمه‌های اصلی منوی کاربر.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    if include_disabled:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id IS NULL
            ORDER BY sort_order, id
            """
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id IS NULL
              AND is_active = 1
            ORDER BY sort_order, id
            """
        )

    rows = cur.fetchall()

    db.close()

    return [dict(row) for row in rows]


def get_submenu_items(parent_id, include_disabled=False):
    """
    دریافت دکمه‌های یک زیرمنو.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    if include_disabled:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id = ?
            ORDER BY sort_order, id
            """,
            (parent_id,),
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id = ?
              AND is_active = 1
            ORDER BY sort_order, id
            """,
            (parent_id,),
        )

    rows = cur.fetchall()

    db.close()

    return [dict(row) for row in rows]


# =========================================================
# UPDATE
# =========================================================

def update_menu_item(
    item_id,
    title=None,
    icon=None,
    action_type=None,
    action_value=None,
    parent_id=None,
    sort_order=None,
    is_active=None,
):
    """
    ویرایش دکمه.

    فقط فیلدهایی که مقدار دارند تغییر می‌کنند.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    current = cur.execute(
        """
        SELECT *
        FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()

    if not current:
        db.close()
        return False

    current = dict(current)

    new_title = current["title"] if title is None else title
    new_icon = current["icon"] if icon is None else icon
    new_action_type = (
        current["action_type"]
        if action_type is None
        else action_type
    )
    new_action_value = (
        current["action_value"]
        if action_value is None
        else action_value
    )

    # نکته:
    # None در parent_id یعنی مقدار فعلی حفظ شود.
    # برای حذف parent باید parent_id=False ارسال شود.
    if parent_id is False:
        new_parent_id = None
    elif parent_id is None:
        new_parent_id = current["parent_id"]
    else:
        new_parent_id = parent_id

    new_sort_order = (
        current["sort_order"]
        if sort_order is None
        else sort_order
    )

    new_is_active = (
        current["is_active"]
        if is_active is None
        else (1 if is_active else 0)
    )

    cur.execute(
        """
        UPDATE user_menu
        SET
            title = ?,
            icon = ?,
            action_type = ?,
            action_value = ?,
            parent_id = ?,
            sort_order = ?,
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            new_title,
            new_icon,
            new_action_type,
            new_action_value,
            new_parent_id,
            new_sort_order,
            new_is_active,
            item_id,
        ),
    )

    db.commit()
    db.close()

    return True


# =========================================================
# DELETE
# =========================================================

def delete_menu_item(item_id):
    """
    حذف یک دکمه.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        DELETE FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    )

    deleted = cur.rowcount > 0

    db.commit()
    db.close()

    return deleted


# =========================================================
# ENABLE / DISABLE
# =========================================================

def set_menu_item_active(item_id, active):
    """
    فعال یا غیرفعال کردن دکمه.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        UPDATE user_menu
        SET
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            1 if active else 0,
            item_id,
        ),
    )

    changed = cur.rowcount > 0

    db.commit()
    db.close()

    return changed


def toggle_menu_item(item_id):
    """
    تغییر وضعیت فعال/غیرفعال.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    row = cur.execute(
        """
        SELECT is_active
        FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()

    if not row:
        db.close()
        return None

    new_status = 0 if row["is_active"] else 1

    cur.execute(
        """
        UPDATE user_menu
        SET
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            new_status,
            item_id,
        ),
    )

    db.commit()
    db.close()

    return bool(new_status)


# =========================================================
# SORT / ORDER
# =========================================================

def set_menu_item_order(item_id, new_order):
    """
    تغییر ترتیب یک دکمه.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        UPDATE user_menu
        SET
            sort_order = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            new_order,
            item_id,
        ),
    )

    changed = cur.rowcount > 0

    db.commit()
    db.close()

    return changed


def move_menu_item_up(item_id):
    """
    انتقال یک دکمه یک مرحله به بالا.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    current = cur.execute(
        """
        SELECT *
        FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()

    if not current:
        db.close()
        return False

    current = dict(current)

    parent_id = current["parent_id"]
    current_order = current["sort_order"]

    if parent_id is None:
        row = cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id IS NULL
              AND sort_order < ?
            ORDER BY sort_order DESC
            LIMIT 1
            """,
            (current_order,),
        ).fetchone()
    else:
        row = cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id = ?
              AND sort_order < ?
            ORDER BY sort_order DESC
            LIMIT 1
            """,
            (
                parent_id,
                current_order,
            ),
        ).fetchone()

    if not row:
        db.close()
        return False

    other = dict(row)

    cur.execute(
        """
        UPDATE user_menu
        SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            other["sort_order"],
            item_id,
        ),
    )

    cur.execute(
        """
        UPDATE user_menu
        SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            current_order,
            other["id"],
        ),
    )

    db.commit()
    db.close()

    return True


def move_menu_item_down(item_id):
    """
    انتقال یک دکمه یک مرحله به پایین.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    current = cur.execute(
        """
        SELECT *
        FROM user_menu
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()

    if not current:
        db.close()
        return False

    current = dict(current)

    parent_id = current["parent_id"]
    current_order = current["sort_order"]

    if parent_id is None:
        row = cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id IS NULL
              AND sort_order > ?
            ORDER BY sort_order ASC
            LIMIT 1
            """,
            (current_order,),
        ).fetchone()
    else:
        row = cur.execute(
            """
            SELECT *
            FROM user_menu
            WHERE parent_id = ?
              AND sort_order > ?
            ORDER BY sort_order ASC
            LIMIT 1
            """,
            (
                parent_id,
                current_order,
            ),
        ).fetchone()

    if not row:
        db.close()
        return False

    other = dict(row)

    cur.execute(
        """
        UPDATE user_menu
        SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            other["sort_order"],
            item_id,
        ),
    )

    cur.execute(
        """
        UPDATE user_menu
        SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            current_order,
            other["id"],
        ),
    )

    db.commit()
    db.close()

    return True


# =========================================================
# RESET ORDER
# =========================================================

def normalize_menu_order(parent_id=None):
    """
    مرتب‌سازی مجدد ترتیب دکمه‌ها از 1 به بعد.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    if parent_id is None:
        rows = cur.execute(
            """
            SELECT id
            FROM user_menu
            WHERE parent_id IS NULL
            ORDER BY sort_order, id
            """
        ).fetchall()
    else:
        rows = cur.execute(
            """
            SELECT id
            FROM user_menu
            WHERE parent_id = ?
            ORDER BY sort_order, id
            """,
            (parent_id,),
        ).fetchall()

    for index, row in enumerate(rows, start=1):
        cur.execute(
            """
            UPDATE user_menu
            SET
                sort_order = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                index,
                row["id"],
            ),
        )

    db.commit()
    db.close()


# =========================================================
# SEED DEFAULT MENU
# =========================================================

def seed_default_menu():
    """
    فقط در صورتی که منوی کاربر خالی باشد،
    منوی پایه پروژه را ایجاد می‌کند.

    اگر قبلاً دکمه وجود داشته باشد،
    هیچ چیزی را تغییر نمی‌دهد.
    """

    init_user_menu_table()

    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM user_menu
        """
    )

    count = cur.fetchone()[0]

    db.close()

    if count > 0:
        return False

    default_items = [
        ("🛒", "خرید VPN", "buy_vpn"),
        ("🎁", "تست رایگان", "free_trial"),
        ("💰", "کیف پول", "wallet"),
        ("📜", "تراکنش‌های من", "transactions"),
        ("🤝", "پنل نمایندگی", "reseller"),
        ("🔑", "لایسنس ربات", "license"),
        ("🆘", "پشتیبانی", "support"),
        ("📚", "راهنما", "help"),
    ]

    for order, (icon, title, action) in enumerate(
        default_items,
        start=1,
    ):
        add_menu_item(
            title=title,
            icon=icon,
            action_type="callback",
            action_value=action,
            parent_id=None,
            sort_order=order,
            is_active=True,
        )

    return True


# =========================================================
# DISPLAY HELPERS
# =========================================================

def get_menu_tree():
    """
    منوی کامل را به شکل درختی برمی‌گرداند.

    خروجی:

    [
        {
            "item": {...},
            "children": [...]
        }
    ]
    """

    init_user_menu_table()

    main_items = get_main_menu_items(
        include_disabled=False
    )

    tree = []

    for item in main_items:
        children = get_submenu_items(
            item["id"],
            include_disabled=False,
        )

        tree.append(
            {
                "item": item,
                "children": children,
            }
        )

    return tree


# =========================================================
# INITIALIZATION
# =========================================================

def initialize_user_menu():
    """
    راه‌اندازی کامل سیستم منوی کاربر.
    """

    init_user_menu_table()
    seed_default_menu()


# =========================================================
# AUTO INIT
# =========================================================

# جدول هنگام import شدن فایل ساخته می‌شود.
initialize_user_menu()
