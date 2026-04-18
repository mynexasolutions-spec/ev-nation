from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.errors import DomainValidationError
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_auth import AdminLoginRequest, AdminTokenResponse, AdminUserRead
from app.services.admin_auth_service import AdminAuthService

router = APIRouter(prefix="/admin/auth")
service = AdminAuthService()


@router.post("/login", response_model=AdminTokenResponse, summary="Admin login")
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminTokenResponse:
    try:
        return service.login(db, payload)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=AdminUserRead, summary="Get current admin user")
def read_current_admin(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUserRead:
    return AdminUserRead.model_validate(current_admin)
