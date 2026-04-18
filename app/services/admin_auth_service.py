from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.core.security import create_access_token, decode_access_token, verify_password
from app.repositories.admin_user_repository import AdminUserRepository
from app.schemas.admin_auth import AdminLoginRequest, AdminTokenResponse


class AdminAuthService:
    def __init__(self, repository: AdminUserRepository | None = None) -> None:
        self.repository = repository or AdminUserRepository()

    def login(self, db: Session, payload: AdminLoginRequest) -> AdminTokenResponse:
        admin_user = self.repository.get_by_email(db, payload.email.lower())
        if admin_user is None or not verify_password(payload.password, admin_user.password_hash):
            raise DomainValidationError("Invalid email or password.")
        if not admin_user.is_active:
            raise DomainValidationError("Admin account is inactive.")

        self.repository.update_last_login(db, admin_user)
        token = create_access_token(str(admin_user.id))
        return AdminTokenResponse(access_token=token)

    def get_current_admin(self, db: Session, token: str):
        try:
            payload = decode_access_token(token)
        except ValueError as exc:
            raise DomainValidationError("Invalid or expired access token.") from exc

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise DomainValidationError("Invalid access token subject.")

        admin_user = self.repository.get_by_id(db, int(subject))
        if admin_user is None:
            raise NotFoundError("Admin user was not found.")
        if not admin_user.is_active:
            raise DomainValidationError("Admin account is inactive.")
        return admin_user
