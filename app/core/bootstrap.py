from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.models.admin_user import AdminUser
from app.repositories.admin_user_repository import AdminUserRepository


def bootstrap_application() -> None:
    try:
        Base.metadata.create_all(bind=get_engine())
        _ensure_bootstrap_admin()
    except OperationalError as exc:
        raise RuntimeError(
            "Database connection failed during startup. "
            "Check DATABASE_URL or start your database server."
        ) from exc


def _ensure_bootstrap_admin() -> None:
    session_factory = get_session_factory()
    repository = AdminUserRepository()

    with session_factory() as db:
        email = settings.bootstrap_admin_email.strip().lower()
        admin_user = repository.get_by_email(db, email)
        if admin_user is None:
            admin_user = AdminUser(
                email=email,
                password_hash=hash_password(settings.bootstrap_admin_password),
                full_name=settings.bootstrap_admin_full_name,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            return

        changed = False
        if not admin_user.is_active:
            admin_user.is_active = True
            changed = True
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            changed = True
        if settings.bootstrap_admin_full_name != admin_user.full_name:
            admin_user.full_name = settings.bootstrap_admin_full_name
            changed = True

        if changed:
            db.add(admin_user)
            db.commit()
