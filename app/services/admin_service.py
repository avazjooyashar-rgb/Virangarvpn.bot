from sqlalchemy import select
from sqlalchemy.orm import Session

from config import SUPER_ADMIN_ID
from app.database.models import Admin, Permission, Role, RolePermission


# =========================
# DEFAULT PERMISSIONS
# =========================

DEFAULT_PERMISSIONS = [
    ("admin.panel", "دسترسی به پنل مدیریت"),
    ("users.view", "مشاهده کاربران"),
    ("users.manage", "مدیریت کاربران"),
    ("admins.view", "مشاهده ادمین‌ها"),
    ("admins.manage", "مدیریت ادمین‌ها"),
    ("roles.manage", "مدیریت نقش‌ها"),
    ("shop.view", "مشاهده فروشگاه"),
    ("shop.manage", "مدیریت فروشگاه"),
    ("orders.view", "مشاهده سفارش‌ها"),
    ("orders.manage", "مدیریت سفارش‌ها"),
    ("payments.view", "مشاهده پرداخت‌ها"),
    ("payments.manage", "مدیریت پرداخت‌ها"),
    ("panels.view", "مشاهده پنل‌ها"),
    ("panels.manage", "مدیریت پنل‌ها"),
    ("nodes.view", "مشاهده نودها"),
    ("nodes.manage", "مدیریت نودها"),
    ("coupons.manage", "مدیریت کدهای تخفیف"),
    ("referrals.view", "مشاهده دعوت‌ها"),
    ("broadcast.manage", "مدیریت پیام همگانی"),
    ("support.manage", "مدیریت پشتیبانی"),
    ("homepage.manage", "مدیریت صفحه اصلی"),
    ("analytics.view", "مشاهده آمار"),
    ("backups.manage", "مدیریت بکاپ‌ها"),
    ("settings.manage", "مدیریت تنظیمات"),
]


# =========================
# DEFAULT ROLES
# =========================

DEFAULT_ROLES = [
    (
        "super_admin",
        "دسترسی کامل سیستم",
        True,
    ),
    (
        "admin",
        "مدیر سیستم",
        True,
    ),
    (
        "support",
        "مدیر پشتیبانی",
        True,
    ),
]


# =========================
# SEED PERMISSIONS
# =========================

def seed_permissions(db: Session):
    for code, description in DEFAULT_PERMISSIONS:

        permission = db.scalar(
            select(Permission).where(
                Permission.code == code
            )
        )

        if permission:
            continue

        permission = Permission(
            code=code,
            description=description,
        )

        db.add(permission)

    db.commit()


# =========================
# SEED ROLES
# =========================

def seed_roles(db: Session):

    for name, description, is_system in DEFAULT_ROLES:

        role = db.scalar(
            select(Role).where(
                Role.name == name
            )
        )

        if role:
            continue

        role = Role(
            name=name,
            description=description,
            is_system=is_system,
        )

        db.add(role)

    db.commit()


# =========================
# SUPER ADMIN PERMISSIONS
# =========================

def grant_super_admin_permissions(db: Session):

    role = db.scalar(
        select(Role).where(
            Role.name == "super_admin"
        )
    )

    if not role:
        return

    permissions = db.scalars(
        select(Permission)
    ).all()

    existing_ids = {
        item.permission_id
        for item in db.scalars(
            select(RolePermission).where(
                RolePermission.role_id == role.id
            )
        ).all()
    }

    for permission in permissions:

        if permission.id in existing_ids:
            continue

        db.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )

    db.commit()


# =========================
# CREATE SUPER ADMIN
# =========================

def ensure_super_admin(db: Session):

    role = db.scalar(
        select(Role).where(
            Role.name == "super_admin"
        )
    )

    if not role:
        raise RuntimeError(
            "Super Admin role has not been created."
        )

    admin = db.scalar(
        select(Admin).where(
            Admin.telegram_id == SUPER_ADMIN_ID
        )
    )

    if admin:

        admin.role_id = role.id
        admin.role = "super_admin"
        admin.is_active = True

        db.commit()
        db.refresh(admin)

        return admin

    admin = Admin(
        telegram_id=SUPER_ADMIN_ID,
        role_id=role.id,
        role="super_admin",
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


# =========================
# FULL SYSTEM SEED
# =========================

def initialize_admin_system(db: Session):

    seed_permissions(db)

    seed_roles(db)

    grant_super_admin_permissions(db)

    ensure_super_admin(db)
