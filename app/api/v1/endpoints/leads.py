from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadCreateResponse
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads")
service = LeadService()


@router.post("", response_model=LeadCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create a lead")
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadCreateResponse:
    if payload.bot_check:
        from app.models.enums import LeadStatus
        return LeadCreateResponse(
            id=99999,
            source=payload.source,
            status=LeadStatus.NEW,
            whatsapp_url=None,
            detail="Lead created successfully."
        )

    try:
        return service.create_lead(db, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
