from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import AdminAuthService

bearer_scheme = HTTPBearer()
auth_service = AdminAuthService()


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
