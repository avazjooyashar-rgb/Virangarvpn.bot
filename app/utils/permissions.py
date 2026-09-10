from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Admin, Permission, RolePermission


def get_admin(
    db: Session,
    telegram_id: int,
) -> Admin | None:

    return db.scalar(
        select(Admin).where(
            Admin.telegram_id == telegram_id,
            Admin.is_active.is_(True),
        )
    )


def is_admin(
    db: Session,
    telegram_id: int,
) -> bool:

    return get_admin(db, telegram_id) is not None


def has_permission(
    db: Session,
    telegram_id: int,
    permission_code: str,
) -> bool:

    admin = get_admin(db, telegram_id)

    if not admin or not admin.role_id:
        return False

    permission = db.scalar(
        select(Permission).where(
            Permission.code == permission_code
        )
    )

    if not permission:
        return False

    role_permission = db.scalar(
        select(RolePermission).where(
            RolePermission.role_id == admin.role_id,
            RolePermission.permission_id == permission.id,
        )
    )

    return role_permission is not None


def is_super_admin(
    db: Session,
    telegram_id: int,
) -> bool:

    admin = get_admin(db, telegram_id)

    if not admin:
        return False

    return admin.role == "super_admin"


def require_permission(
    db: Session,
    telegram_id: int,
    permission_code: str,
) -> bool:

    if is_super_admin(db, telegram_id):
        return True

    return has_permission(
        db,
        telegram_id,
        permission_code,
    )
