# =========================
# MENU ACTION HEALTH
# =========================

from menu_action_metrics import get_global_metrics
from menu_action_security import get_security_status
from menu_action_validator import get_validator_status
from menu_action_cache import get_cache_status
from menu_action_rate_limiter import get_rate_limiter_status


def check_metrics():
    try:
        metrics = get_global_metrics()

        return {
            "healthy": True,
            "metrics": metrics,
            "message": "🟢 Metrics سالم است.",
        }

    except Exception as exc:
        return {
            "healthy": False,
            "metrics": {},
            "message": f"🔴 خطا در Metrics: {exc}",
        }


def check_security():
    try:
        status = get_security_status()

        return {
            "healthy": status.get("status") == "ready",
            "status": status,
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": {},
            "message": f"🔴 خطا در Security: {exc}",
        }


def check_validator():
    try:
        status = get_validator_status()

        return {
            "healthy": status.get("status") == "ready",
            "status": status,
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": {},
            "message": f"🔴 خطا در Validator: {exc}",
        }


def check_cache():
    try:
        status = get_cache_status()

        return {
            "healthy": status.get("status") == "ready",
            "status": status,
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": {},
            "message": f"🔴 خطا در Cache: {exc}",
        }


def check_rate_limiter():
    try:
        status = get_rate_limiter_status()

        return {
            "healthy": status.get("status") == "ready",
            "status": status,
        }

    except Exception as exc:
        return {
            "healthy": False,
            "status": {},
            "message": f"🔴 خطا در Rate Limiter: {exc}",
        }


def run_health_check():
    checks = {
        "metrics": check_metrics(),
        "security": check_security(),
        "validator": check_validator(),
        "cache": check_cache(),
        "rate_limiter": check_rate_limiter(),
    }

    healthy = all(
        result.get("healthy", False)
        for result in checks.values()
    )

    return {
        "healthy": healthy,
        "checks": checks,
        "status": "🟢 سالم" if healthy else "🔴 مشکل دارد",
    }


def get_health_report():
    result = run_health_check()

    lines = [
        "🏥 سلامت سیستم اکشن منو",
        "━━━━━━━━━━━━━━━━━━",
        "",
        f"📌 وضعیت کلی: {result['status']}",
        "",
    ]

    for name, check in result["checks"].items():
        status = "🟢 سالم" if check.get("healthy") else "🔴 خطا"
        lines.append(f"• {name}: {status}")

    return "\n".join(lines)


def get_health_status():
    result = run_health_check()

    return {
        "module": "menu_action_health",
        "status": "ready",
        "healthy": result["healthy"],
        "checks": result["checks"],
    }
