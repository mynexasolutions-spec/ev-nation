from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin


class UserService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def register_user(self, db: Session, payload: UserCreate) -> User:
        if self.user_repository.get_by_email(db, payload.email):
            raise DomainValidationError("A user with this email already exists.")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        return self.user_repository.create(db, user)

    def authenticate_user(self, db: Session, payload: UserLogin) -> User | None:
        user = self.user_repository.get_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            return None
        
        if not user.is_active:
            return None

        user.last_login_at = datetime.now(timezone.utc)
        self.user_repository.save(db, user)
        return user
