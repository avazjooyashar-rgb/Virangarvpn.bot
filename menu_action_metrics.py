# =========================
# MENU ACTION METRICS
# =========================

from menu_action_logger import get_menu_action_logs


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_action_metrics(item_id=None, user_id=None, limit=500):
    logs = get_menu_action_logs(
        limit=limit,
        user_id=user_id,
        item_id=item_id,
    )

    total = len(logs)
    successful = sum(
        1 for log in logs
        if _safe_int(log.get("success")) == 1
    )
    failed = total - successful

    by_type = {}

    for log in logs:
        action_type = log.get("action_type") or "unknown"
        by_type[action_type] = by_type.get(action_type, 0) + 1

    success_rate = 0

    if total > 0:
        success_rate = round(
            (successful / total) * 100,
            2,
        )

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "by_type": by_type,
    }


def get_user_metrics(user_id, limit=500):
    return get_action_metrics(
        user_id=user_id,
        limit=limit,
    )


def get_item_metrics(item_id, limit=500):
    return get_action_metrics(
        item_id=item_id,
        limit=limit,
    )


def get_global_metrics(limit=500):
    return get_action_metrics(
        limit=limit,
    )


def format_metrics(metrics):
    by_type = metrics.get("by_type", {})

    callback_count = by_type.get("callback", 0)
    url_count = by_type.get("url", 0)
    submenu_count = by_type.get("submenu", 0)

    return (
        "📊 آمار اجرای منو\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 کل عملیات: {metrics.get('total', 0)}\n"
        f"✅ موفق: {metrics.get('successful', 0)}\n"
        f"❌ ناموفق: {metrics.get('failed', 0)}\n"
        f"📈 نرخ موفقیت: {metrics.get('success_rate', 0)}%\n\n"
        "⚙️ بر اساس نوع:\n"
        f"🔘 Callback: {callback_count}\n"
        f"🔗 URL: {url_count}\n"
        f"📂 Submenu: {submenu_count}"
    )


def get_metrics_status():
    return {
        "module": "menu_action_metrics",
        "status": "ready",
        "success_rate": True,
        "action_type_stats": True,
        "user_metrics": True,
        "item_metrics": True,
        "global_metrics": True,
    }
