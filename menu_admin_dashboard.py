# =========================
# MENU ADMIN DASHBOARD
# =========================

from menu_admin_service import (
    admin_get_menu_items,
    admin_get_menu_tree,
    admin_get_menu_preview,
    admin_validate_menu,
    admin_repair_menu,
    get_admin_menu_service_status,
)


def get_dashboard(user_id):
    """
    دریافت اطلاعات کامل داشبورد مدیریت منو.
    """

    status = get_admin_menu_service_status(user_id)

    if not status.get("success"):
        return status

    items_result = admin_get_menu_items(
        user_id,
        include_disabled=True,
    )

    tree_result = admin_get_menu_tree(user_id)

    preview_result = admin_get_menu_preview(user_id)

    return {
        "success": True,
        "status": status,
        "items": items_result.get("items", []),
        "tree": tree_result.get("tree", []),
        "preview": preview_result.get("preview", []),
    }


def get_dashboard_text(user_id):
    """
    متن خلاصه داشبورد مدیریت منو.
    """

    dashboard = get_dashboard(user_id)

    if not dashboard.get("success"):
        return dashboard.get(
            "message",
            "⛔ دسترسی ندارید.",
        )

    status = dashboard["status"]

    health = (
        "🟢 سالم"
        if status.get("healthy")
        else "🔴 نیازمند بررسی"
    )

    return (
        "🎛 داشبورد مدیریت منوی کاربران\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 کل آیتم‌ها: {status.get('total_items', 0)}\n"
        f"🟢 فعال: {status.get('active_items', 0)}\n"
        f"🔴 غیرفعال: {status.get('disabled_items', 0)}\n"
        f"❤️ سلامت سیستم: {health}\n"
        f"⚠️ خطاها: {status.get('error_count', 0)}\n"
    )


def get_menu_items_text(user_id):
    """
    نمایش لیست آیتم‌های منو برای ادمین.
    """

    result = admin_get_menu_items(
        user_id,
        include_disabled=True,
    )

    if not result.get("success"):
        return result.get(
            "message",
            "⛔ دسترسی ندارید.",
        )

    items = result.get("items", [])

    if not items:
        return "📭 هنوز هیچ آیتمی در منو وجود ندارد."

    lines = [
        "📋 لیست منوی کاربران",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for item in items:
        item_id = item.get("id")
        title = item.get("title") or "بدون عنوان"
        icon = item.get("icon") or "🔘"

        active = (
            "🟢 فعال"
            if int(item.get("is_active", 0)) == 1
            else "🔴 غیرفعال"
        )

        action_type = item.get("action_type") or "—"
        order = item.get("sort_order", 0)

        lines.append(
            f"{icon} {title}\n"
            f"   🆔 {item_id} | 🔢 {order} | "
            f"⚙️ {action_type} | {active}"
        )

    return "\n\n".join(lines)


def validate_dashboard(user_id):
    """
    بررسی سلامت منو.
    """

    result = admin_validate_menu(user_id)

    if not result.get("success"):
        return result

    report = result.get("report", {})

    return {
        "success": True,
        "healthy": result.get("healthy", False),
        "error_count": report.get("error_count", 0),
        "errors": report.get("errors", []),
    }


def repair_dashboard(user_id):
    """
    تعمیر ساختار منو.
    """

    result = admin_repair_menu(user_id)

    if not result.get("success"):
        return result

    return {
        "success": True,
        "message": "🛠 ساختار منو با موفقیت تعمیر شد.",
        "result": result.get("result"),
    }


def get_dashboard_summary(user_id):
    """
    خلاصه‌ی عددی داشبورد.
    """

    result = get_admin_menu_service_status(user_id)

    if not result.get("success"):
        return result

    return {
        "success": True,
        "total": result.get("total_items", 0),
        "active": result.get("active_items", 0),
        "disabled": result.get("disabled_items", 0),
        "healthy": result.get("healthy", False),
        "errors": result.get("error_count", 0),
    }
