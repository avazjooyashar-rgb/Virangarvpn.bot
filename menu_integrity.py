# =========================
# MENU INTEGRITY
# =========================

from user_menu_manager import (
    get_menu_item,
    get_all_menu_items,
    get_main_menu_items,
    get_submenu_items,
    normalize_menu_order,
)


def get_parent_chain(item_id):
    """
    مسیر والدهای یک آیتم را برمی‌گرداند.
    مثال:
    item 5 -> parent 3 -> parent 1
    نتیجه: [5, 3, 1]
    """
    chain = []
    visited = set()
    current_id = item_id

    while current_id is not None:
        if current_id in visited:
            break

        visited.add(current_id)
        chain.append(current_id)

        item = get_menu_item(current_id)

        if not item:
            break

        current_id = item.get("parent_id")

    return chain


def has_parent_cycle(item_id, parent_id):
    """
    بررسی می‌کند آیا قرار دادن parent_id برای item_id
    باعث ایجاد حلقه در ساختار منو می‌شود یا نه.
    """

    if parent_id is None:
        return False

    try:
        item_id = int(item_id)
        parent_id = int(parent_id)
    except (TypeError, ValueError):
        return True

    if item_id == parent_id:
        return True

    visited = set()
    current_id = parent_id

    while current_id is not None:

        if current_id in visited:
            return True

        visited.add(current_id)

        if current_id == item_id:
            return True

        item = get_menu_item(current_id)

        if not item:
            return False

        current_id = item.get("parent_id")

    return False


def find_invalid_parent_items():
    """
    آیتم‌هایی که parent_id نامعتبر دارند را پیدا می‌کند.
    """

    items = get_all_menu_items(include_disabled=True)

    item_ids = {
        item["id"]
        for item in items
    }

    invalid = []

    for item in items:
        parent_id = item.get("parent_id")

        if parent_id is None:
            continue

        if parent_id not in item_ids:
            invalid.append({
                "id": item["id"],
                "title": item.get("title") or "",
                "parent_id": parent_id,
                "reason": "والد پیدا نشد",
            })

    return invalid


def find_cycle_items():
    """
    تمام آیتم‌هایی که در ساختار والد/فرزند حلقه ایجاد کرده‌اند
    را پیدا می‌کند.
    """

    items = get_all_menu_items(include_disabled=True)
    cycle_items = []

    for item in items:
        item_id = item["id"]
        parent_id = item.get("parent_id")

        if parent_id is None:
            continue

        if has_parent_cycle(item_id, parent_id):
            cycle_items.append({
                "id": item_id,
                "title": item.get("title") or "",
                "parent_id": parent_id,
            })

    return cycle_items


def find_duplicate_orders(parent_id=None):
    """
    بررسی می‌کند آیا دو آیتم در یک سطح order یکسان دارند یا نه.
    """

    if parent_id is None:
        items = get_main_menu_items(include_disabled=True)
    else:
        items = get_submenu_items(
            parent_id,
            include_disabled=True
        )

    orders = {}
    duplicates = []

    for item in items:
        order = item.get("sort_order", 0)

        if order in orders:
            duplicates.append({
                "order": order,
                "item_ids": [
                    orders[order],
                    item["id"],
                ],
            })
        else:
            orders[order] = item["id"]

    return duplicates


def find_invalid_orders():
    """
    تمام سطوح منو را برای orderهای تکراری بررسی می‌کند.
    """

    items = get_all_menu_items(include_disabled=True)

    parent_ids = {None}

    for item in items:
        parent_ids.add(item.get("parent_id"))

    invalid = []

    for parent_id in parent_ids:
        duplicates = find_duplicate_orders(parent_id)

        if duplicates:
            invalid.append({
                "parent_id": parent_id,
                "duplicates": duplicates,
            })

    return invalid


def validate_menu_integrity():
    """
    گزارش کامل سلامت ساختار منو.
    """

    invalid_parents = find_invalid_parent_items()
    cycle_items = find_cycle_items()
    invalid_orders = find_invalid_orders()

    errors = []

    for item in invalid_parents:
        errors.append({
            "type": "invalid_parent",
            "item_id": item["id"],
            "message": (
                f"آیتم {item['id']} والد نامعتبر دارد."
            ),
        })

    for item in cycle_items:
        errors.append({
            "type": "cycle",
            "item_id": item["id"],
            "message": (
                f"آیتم {item['id']} باعث ایجاد حلقه شده است."
            ),
        })

    for group in invalid_orders:
        errors.append({
            "type": "duplicate_order",
            "parent_id": group["parent_id"],
            "message": (
                "ترتیب چند آیتم در یک سطح تکراری است."
            ),
        })

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors),
        "invalid_parents": invalid_parents,
        "cycle_items": cycle_items,
        "invalid_orders": invalid_orders,
    }


def repair_menu_orders():
    """
    ترتیب تمام سطوح منو را مرتب می‌کند.
    """

    result = normalize_menu_order(parent_id=None)

    items = get_all_menu_items(include_disabled=True)

    parent_ids = set()

    for item in items:
        parent_id = item.get("parent_id")

        if parent_id is not None:
            parent_ids.add(parent_id)

    repaired = 1 if result else 0

    for parent_id in parent_ids:
        if normalize_menu_order(parent_id):
            repaired += 1

    return repaired


def get_menu_integrity_summary():
    """
    خلاصه وضعیت سلامت منو برای پنل مدیریت.
    """

    report = validate_menu_integrity()

    return {
        "healthy": report["valid"],
        "error_count": report["error_count"],
        "invalid_parents": len(
            report["invalid_parents"]
        ),
        "cycles": len(
            report["cycle_items"]
        ),
        "duplicate_orders": len(
            report["invalid_orders"]
        ),
    }


def repair_menu():
    """
    عملیات تعمیر منو.

    فعلاً فقط ترتیب‌ها را اصلاح می‌کند.
    آیتم‌های دارای parent خراب یا cycle
    به صورت خودکار حذف نمی‌شوند.
    """

    repaired_orders = repair_menu_orders()

    report = validate_menu_integrity()

    return {
        "success": report["valid"],
        "repaired_order_groups": repaired_orders,
        "report": report,
    }


def is_menu_healthy():
    """
    بررسی سریع سلامت منو.
    """

    return validate_menu_integrity()["valid"]
