# =========================
# MENU ACTION TYPES
# =========================

ACTION_CALLBACK = "callback"
ACTION_URL = "url"
ACTION_SUBMENU = "submenu"

ACTION_TYPES = {
    ACTION_CALLBACK: {
        "title": "🔘 دکمه داخلی",
        "description": "اجرای یک callback داخلی در ربات",
    },
    ACTION_URL: {
        "title": "🔗 لینک",
        "description": "باز کردن یک لینک خارجی",
    },
    ACTION_SUBMENU: {
        "title": "📂 زیرمنو",
        "description": "نمایش آیتم‌های زیرمجموعه",
    },
}


def get_action_types():
    return ACTION_TYPES.copy()


def get_action_type_label(action_type):
    data = ACTION_TYPES.get(action_type)

    if not data:
        return "❓ نامشخص"

    return data["title"]


def get_action_type_description(action_type):
    data = ACTION_TYPES.get(action_type)

    if not data:
        return ""

    return data["description"]


def is_valid_action_type(action_type):
    return action_type in ACTION_TYPES


def normalize_action_type(action_type):
    if action_type is None:
        return None

    value = str(action_type).strip().lower()

    aliases = {
        "button": ACTION_CALLBACK,
        "internal": ACTION_CALLBACK,
        "callback": ACTION_CALLBACK,

        "link": ACTION_URL,
        "url": ACTION_URL,

        "menu": ACTION_SUBMENU,
        "sub": ACTION_SUBMENU,
        "submenu": ACTION_SUBMENU,
    }

    return aliases.get(value)


def get_action_type_choices():
    return [
        {
            "value": action_type,
            "title": data["title"],
            "description": data["description"],
        }
        for action_type, data in ACTION_TYPES.items()
    ]


def format_action_type(action_type):
    normalized = normalize_action_type(action_type)

    if not normalized:
        return "❓ نامشخص"

    return get_action_type_label(normalized)


def format_action_type_choices():
    lines = ["⚙️ نوع عملکرد دکمه:", ""]

    for index, item in enumerate(
        get_action_type_choices(),
        start=1,
    ):
        lines.append(
            f"{index}. {item['title']}\n"
            f"   {item['description']}"
        )

    return "\n\n".join(lines)


def parse_action_type(value):
    if value is None:
        return None

    value = str(value).strip()

    if value in ACTION_TYPES:
        return value

    try:
        index = int(value)
    except ValueError:
        return normalize_action_type(value)

    choices = get_action_type_choices()

    if 1 <= index <= len(choices):
        return choices[index - 1]["value"]

    return None
