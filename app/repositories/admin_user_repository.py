from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser


class AdminUserRepository:
    def get_by_email(self, db: Session, email: str) -> AdminUser | None:
        statement = select(AdminUser).where(AdminUser.email == email)
        return db.scalar(statement)

    def get_by_id(self, db: Session, admin_user_id: int) -> AdminUser | None:
        statement = select(AdminUser).where(AdminUser.id == admin_user_id)
        return db.scalar(statement)

    def update_last_login(self, db: Session, admin_user: AdminUser) -> AdminUser:
        admin_user.last_login_at = datetime.now(timezone.utc)
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
