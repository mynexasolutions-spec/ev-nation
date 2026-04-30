from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.admin_auth_service import AdminAuthService

bearer_scheme = HTTPBearer()
auth_service = AdminAuthService()
user_repo = UserRepository()


def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> AdminUser:
    try:
        return auth_service.get_current_admin(db, credentials.credentials)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def get_current_user_web(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return user_repo.get_by_id(db, int(user_id))
    except Exception:
        return None


def get_current_user_required(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Like get_current_user_web, but raises 401 if not authenticated."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
            )
        user = user_repo.get_by_id(db, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
