import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# 👑 Super Admin
SUPER_ADMIN_ID = 691651240

# 👥 Admins
ADMIN_IDS = {
    int(user_id.strip())
    for user_id in os.getenv(
        "ADMIN_IDS",
        "",
    ).split(",")
    if user_id.strip().isdigit()
}

# Super Admin همیشه ادمین است
ADMIN_IDS.add(SUPER_ADMIN_ID)
