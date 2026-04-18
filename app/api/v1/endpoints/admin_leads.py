from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.models.enums import LeadSource, LeadStatus
from app.schemas.lead import AdminLeadRead, AdminLeadStatusUpdate
from app.services.lead_service import LeadService

router = APIRouter(prefix="/admin/leads")
service = LeadService()


@router.get("", response_model=list[AdminLeadRead], summary="List leads for admin")
def list_admin_leads(
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    source_filter: LeadSource | None = Query(default=None, alias="source"),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> list[AdminLeadRead]:
    return service.list_admin_leads(db, status=status_filter, source=source_filter)


@router.get("/{lead_id}", response_model=AdminLeadRead, summary="Get lead for admin")
def get_admin_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminLeadRead:
    try:
        return service.get_admin_lead(db, lead_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{lead_id}/status", response_model=AdminLeadRead, summary="Update lead status")
def update_admin_lead_status(
    lead_id: int,
    payload: AdminLeadStatusUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminLeadRead:
    try:
        return service.update_admin_lead_status(db, lead_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
