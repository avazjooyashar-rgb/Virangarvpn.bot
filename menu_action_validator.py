# =========================
# MENU ACTION VALIDATOR
# =========================

from menu_action_types import (
    ACTION_CALLBACK,
    ACTION_URL,
    ACTION_SUBMENU,
    normalize_action_type,
    is_valid_action_type,
)


MAX_CALLBACK_LENGTH = 200
MAX_URL_LENGTH = 500


def validate_action_type(action_type):
    normalized = normalize_action_type(action_type)

    if not normalized or not is_valid_action_type(normalized):
        return {
            "valid": False,
            "value": normalized,
            "message": "❌ نوع عملیات نامعتبر است.",
        }

    return {
        "valid": True,
        "value": normalized,
        "message": "",
    }


def validate_callback_value(value):
    value = "" if value is None else str(value).strip()

    if not value:
        return {
            "valid": False,
            "value": value,
            "message": "❌ مقدار callback نمی‌تواند خالی باشد.",
        }

    if len(value) > MAX_CALLBACK_LENGTH:
        return {
            "valid": False,
            "value": value,
            "message": f"❌ مقدار callback نباید بیشتر از {MAX_CALLBACK_LENGTH} کاراکتر باشد.",
        }

    return {
        "valid": True,
        "value": value,
        "message": "",
    }


def validate_url_value(value):
    value = "" if value is None else str(value).strip()

    if not value:
        return {
            "valid": False,
            "value": value,
            "message": "❌ لینک نمی‌تواند خالی باشد.",
        }

    if not (
        value.startswith("https://")
        or value.startswith("http://")
    ):
        return {
            "valid": False,
            "value": value,
            "message": "❌ لینک باید با http:// یا https:// شروع شود.",
        }

    if len(value) > MAX_URL_LENGTH:
        return {
            "valid": False,
            "value": value,
            "message": f"❌ لینک نباید بیشتر از {MAX_URL_LENGTH} کاراکتر باشد.",
        }

    return {
        "valid": True,
        "value": value,
        "message": "",
    }


def validate_submenu_value(value):
    value = "" if value is None else str(value).strip()

    # برای submenu مقدار action_value الزامی نیست.
    return {
        "valid": True,
        "value": value,
        "message": "",
    }


def validate_action(action_type, value):
    type_result = validate_action_type(action_type)

    if not type_result["valid"]:
        return type_result

    normalized_type = type_result["value"]

    if normalized_type == ACTION_CALLBACK:
        value_result = validate_callback_value(value)

    elif normalized_type == ACTION_URL:
        value_result = validate_url_value(value)

    elif normalized_type == ACTION_SUBMENU:
        value_result = validate_submenu_value(value)

    else:
        return {
            "valid": False,
            "value": value,
            "message": "❌ نوع عملیات پشتیبانی نمی‌شود.",
        }

    return {
        "valid": value_result["valid"],
        "type": normalized_type,
        "value": value_result["value"],
        "message": value_result["message"],
    }


def normalize_action(action_type, value):
    result = validate_action(action_type, value)

    if not result["valid"]:
        return result

    return {
        "valid": True,
        "type": result["type"],
        "value": result["value"],
        "message": "",
    }


def is_action_valid(action_type, value):
    return bool(
        validate_action(action_type, value).get("valid")
    )


def get_action_validation_error(action_type, value):
    result = validate_action(action_type, value)

    if result.get("valid"):
        return ""

    return result.get(
        "message",
        "❌ عملیات نامعتبر است.",
    )


def get_validator_status():
    return {
        "module": "menu_action_validator",
        "status": "ready",
        "callback": True,
        "url": True,
        "submenu": True,
    }
