from sqlalchemy import select
from sqlalchemy.orm import Session
import telebot

from app.database.models import RequiredChannel


def get_active_channels(db: Session):
    return db.scalars(
        select(RequiredChannel)
        .where(RequiredChannel.is_active.is_(True))
        .order_by(RequiredChannel.id)
    ).all()


def is_user_member(
    bot: telebot.TeleBot,
    user_id: int,
    channel_username: str,
) -> bool:

    try:
        member = bot.get_chat_member(
            chat_id=channel_username,
            user_id=user_id,
        )

        return member.status in (
            "creator",
            "administrator",
            "member",
        )

    except Exception:
        return False


def check_required_membership(
    bot: telebot.TeleBot,
    db: Session,
    user_id: int,
) -> tuple[bool, list]:

    channels = get_active_channels(db)

    if not channels:
        return True, []

    missing_channels = []

    for channel in channels:

        if not is_user_member(
            bot=bot,
            user_id=user_id,
            channel_username=channel.username,
        ):
            missing_channels.append(channel)

    return (
        len(missing_channels) == 0,
        missing_channels,
    )
