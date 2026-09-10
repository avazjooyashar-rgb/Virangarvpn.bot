# =========================
# MENU ACTION ALERTS
# =========================

from menu_action_metrics import get_global_metrics


DEFAULT_FAILURE_THRESHOLD = 20


def calculate_failure_rate(metrics):
    total = int(metrics.get("total", 0) or 0)
    failed = int(metrics.get("failed", 0) or 0)

    if total <= 0:
        return 0.0

    return round((failed / total) * 100, 2)


def check_failure_alert(
    limit=500,
    threshold=DEFAULT_FAILURE_THRESHOLD,
):
    metrics = get_global_metrics(limit=limit)

    failure_rate = calculate_failure_rate(metrics)

    alert = failure_rate >= float(threshold)

    return {
        "alert": alert,
        "failure_rate": failure_rate,
        "threshold": float(threshold),
        "total": metrics.get("total", 0),
        "failed": metrics.get("failed", 0),
        "successful": metrics.get("successful", 0),
    }


def get_alert_message(
    limit=500,
    threshold=DEFAULT_FAILURE_THRESHOLD,
):
    result = check_failure_alert(
        limit=limit,
        threshold=threshold,
    )

    if result["total"] == 0:
        return "ℹ️ هنوز اطلاعات کافی برای بررسی وجود ندارد."

    if result["alert"]:
        return (
            "🚨 هشدار سیستم منو\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ عملیات ناموفق: {result['failed']}\n"
            f"📊 کل عملیات: {result['total']}\n"
            f"📉 نرخ خطا: {result['failure_rate']}%\n"
            f"⚠️ حد هشدار: {result['threshold']}%"
        )

    return (
        "🟢 وضعیت سیستم منو عادی است.\n\n"
        f"📊 کل عملیات: {result['total']}\n"
        f"❌ ناموفق: {result['failed']}\n"
        f"📈 نرخ خطا: {result['failure_rate']}%"
    )


def get_alert_status():
    return {
        "module": "menu_action_alerts",
        "status": "ready",
        "failure_alert": True,
        "threshold_check": True,
        "message_generation": True,
    }
