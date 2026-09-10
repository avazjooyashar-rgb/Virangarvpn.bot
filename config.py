import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def get_required(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


BOT_TOKEN = get_required("BOT_TOKEN")

DATABASE_URL = get_required("DATABASE_URL")

SUPER_ADMIN_ID = int(get_required("SUPER_ADMIN_ID"))

BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
