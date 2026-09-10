from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


def get_or_create_user(
    db: Session,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> User:

    user = db.scalar(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

    if user:
        user.username = username
        user.first_name = first_name
        db.commit()
        db.refresh(user)
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
