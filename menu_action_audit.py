# =========================
# MENU ACTION AUDIT
# =========================

from menu_action_logger import (
    log_menu_action,
    get_menu_action_logs,
    count_menu_action_logs,
    get_menu_action_log_summary,
)


def audit_action_attempt(
    user_id,
    item_id,
    action_type,
    action_value="",
):
    log_menu_action(
        user_id=user_id,
        item_id=item_id,
        action_type=action_type,
        action_value=action_value,
        success=True,
        message="action_attempt",
    )

    return {
        "success": True,
        "event": "action_attempt",
    }


def audit_action_success(
    user_id,
    item_id,
    action_type,
    action_value="",
    message="",
):
    log_menu_action(
        user_id=user_id,
        item_id=item_id,
        action_type=action_type,
        action_value=action_value,
        success=True,
        message=message or "action_success",
    )

    return {
        "success": True,
        "event": "action_success",
    }


def audit_action_failure(
    user_id,
    item_id,
    action_type,
    action_value="",
    message="",
):
    log_menu_action(
        user_id=user_id,
        item_id=item_id,
        action_type=action_type,
        action_value=action_value,
        success=False,
        message=message or "action_failed",
    )

    return {
        "success": True,
        "event": "action_failure",
    }


def get_user_audit_logs(user_id, limit=100):
    return get_menu_action_logs(
        limit=limit,
        user_id=user_id,
    )


def get_item_audit_logs(item_id, limit=100):
    return get_menu_action_logs(
        limit=limit,
        item_id=item_id,
    )


def get_audit_count(user_id=None, item_id=None):
    return count_menu_action_logs(
        user_id=user_id,
        item_id=item_id,
    )


def get_audit_summary():
    return get_menu_action_log_summary()


def get_audit_status():
    return {
        "module": "menu_action_audit",
        "status": "ready",
        "attempt_logging": True,
        "success_logging": True,
        "failure_logging": True,
        "user_logs": True,
        "item_logs": True,
    }
