# =========================
# MENU ACTION ROUTER
# =========================

from menu_service import get_menu_item_safe


# =========================
# ACTION TYPES
# =========================

ACTION_CALLBACK = "callback"
ACTION_URL = "url"
ACTION_SUBMENU = "submenu"


# =========================
# GET ACTION
# =========================

def get_menu_action(item_id):
    item = get_menu_item_safe(item_id)

    if not item:
        return None

    return {
        "item_id": item["id"],
        "title": item.get("title") or "",
        "action_type": item.get("action_type") or "",
        "action_value": item.get("action_value") or "",
        "parent_id": item.get("parent_id"),
    }


# =========================
# ROUTE ACTION
# =========================

def route_menu_action(item_id):
    action = get_menu_action(item_id)

    if not action:
        return {
            "success": False,
            "type": "error",
            "value": "",
            "item": None,
        }

    action_type = action["action_type"]
    action_value = action["action_value"]

    if action_type == ACTION_CALLBACK:
        return {
            "success": True,
            "type": ACTION_CALLBACK,
            "value": action_value,
            "item": action,
        }

    if action_type == ACTION_URL:
        return {
            "success": True,
            "type": ACTION_URL,
            "value": action_value,
            "item": action,
        }

    if action_type == ACTION_SUBMENU:
        return {
            "success": True,
            "type": ACTION_SUBMENU,
            "value": action_value,
            "item": action,
        }

    return {
        "success": False,
        "type": "error",
        "value": "",
        "item": action,
    }


# =========================
# VALID ACTION
# =========================

def is_valid_action_type(action_type):
    return action_type in {
        ACTION_CALLBACK,
        ACTION_URL,
        ACTION_SUBMENU,
    }


# =========================
# ACTION DESCRIPTION
# =========================

def get_action_type_label(action_type):
    labels = {
        ACTION_CALLBACK: "🔘 دکمه داخلی",
        ACTION_URL: "🔗 لینک",
        ACTION_SUBMENU: "📂 زیرمنو",
    }

    return labels.get(
        action_type,
        "❓ نامشخص",
    )


# =========================
# ACTION SUMMARY
# =========================

def get_action_summary(item_id):
    action = get_menu_action(item_id)

    if not action:
        return "❌ آیتم پیدا نشد."

    return (
        f"📌 {action['title']}\n"
        f"⚙️ نوع: {get_action_type_label(action['action_type'])}\n"
        f"🎯 مقدار: {action['action_value'] or '—'}"
    )
