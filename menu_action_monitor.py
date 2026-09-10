# =========================
# MENU ACTION MONITOR
# =========================

from menu_action_metrics import (
    get_global_metrics,
    get_user_metrics,
    get_item_metrics,
)


def get_global_monitor(limit=500):
    metrics = get_global_metrics(limit=limit)

    return {
        "success": True,
        "scope": "global",
        "metrics": metrics,
    }


def get_user_monitor(user_id, limit=500):
    metrics = get_user_metrics(
        user_id=user_id,
        limit=limit,
    )

    return {
        "success": True,
        "scope": "user",
        "user_id": user_id,
        "metrics": metrics,
    }


def get_item_monitor(item_id, limit=500):
    metrics = get_item_metrics(
        item_id=item_id,
        limit=limit,
    )

    return {
        "success": True,
        "scope": "item",
        "item_id": item_id,
        "metrics": metrics,
    }


def is_monitor_healthy(metrics):
    if not metrics:
        return False

    total = metrics.get("total", 0)
    failed = metrics.get("failed", 0)

    if total == 0:
        return True

    failure_rate = (failed / total) * 100

    return failure_rate < 20


def get_monitor_health(metrics):
    if not metrics:
        return {
            "healthy": False,
            "status": "🔴 بدون داده",
        }

    if is_monitor_healthy(metrics):
        return {
            "healthy": True,
            "status": "🟢 سالم",
        }

    return {
        "healthy": False,
        "status": "🔴 خطای بالا",
    }


def get_monitor_report(limit=500):
    result = get_global_monitor(limit=limit)

    metrics = result["metrics"]
    health = get_monitor_health(metrics)

    return {
        "success": True,
        "metrics": metrics,
        "health": health,
    }


def get_monitor_status():
    return {
        "module": "menu_action_monitor",
        "status": "ready",
        "global_monitor": True,
        "user_monitor": True,
        "item_monitor": True,
        "health_check": True,
        "failure_detection": True,
    }
