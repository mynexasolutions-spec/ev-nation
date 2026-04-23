from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/auth")
service = UserService()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return service.register_user(db, payload)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login")
def login(response: Response, payload: UserLogin, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, payload)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(subject=str(user.id))
    
    # Set secure cookie for web storefront
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800, # 30 minutes
        samesite="lax",
        secure=False, # Set to True in production with HTTPS
    )
    
    return {"detail": "Successfully logged in"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Successfully logged out"}
