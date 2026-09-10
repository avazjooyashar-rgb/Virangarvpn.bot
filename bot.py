import telebot

from config import BOT_TOKEN
from app.database.session import Base, SessionLocal, engine
from app.database import models
from app.handlers.start import register_start_handler
from app.utils.logger import setup_logging


def create_database():
    Base.metadata.create_all(bind=engine)


def main():
    setup_logging()

    create_database()

    bot = telebot.TeleBot(
        BOT_TOKEN,
        parse_mode="HTML",
    )

    register_start_handler(
        bot=bot,
        db_factory=SessionLocal,
    )

    print("VirangarVPN Bot is running...")

    bot.infinity_polling(
        skip_pending=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
