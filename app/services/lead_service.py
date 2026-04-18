from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DomainValidationError, NotFoundError
from app.core.normalization import build_whatsapp_url
from app.models.enums import LeadSource, LeadStatus
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.lead import AdminLeadRead, AdminLeadStatusUpdate, LeadCreate, LeadCreateResponse


class LeadService:
    def __init__(
        self,
        lead_repository: LeadRepository | None = None,
        product_repository: ProductRepository | None = None,
    ) -> None:
        self.lead_repository = lead_repository or LeadRepository()
        self.product_repository = product_repository or ProductRepository()

    def create_lead(self, db: Session, payload: LeadCreate) -> LeadCreateResponse:
        product = None
        variant = None

        if payload.product_id is not None:
            product = self.product_repository.get_by_id(db, payload.product_id)
            if product is None or not product.is_active:
                raise NotFoundError("Selected product was not found.")

        if payload.variant_id is not None:
            variant = self.product_repository.get_variant_by_id(db, payload.variant_id)
            if variant is None or not variant.is_active:
                raise NotFoundError("Selected variant was not found.")

            variant_product = variant.product
            if variant_product is None or not variant_product.is_active:
                raise NotFoundError("Selected product was not found.")

            if product is not None and variant.product_id != product.id:
                raise DomainValidationError("Selected variant does not belong to the selected product.")

            if product is None:
                product = variant_product

        lead = Lead(
            name=payload.name,
            phone=payload.phone,
            product_id=product.id if product else payload.product_id,
            variant_id=variant.id if variant else payload.variant_id,
            message=payload.message,
            source=payload.source,
            preferred_contact_time=payload.preferred_contact_time,
        )
        created_lead = self.lead_repository.create(db, lead)

        whatsapp_url = None
        detail = "Lead created successfully."
        if created_lead.source == LeadSource.WHATSAPP:
            detail = "Lead created successfully. Redirect the user to WhatsApp using the returned URL."
            if settings.whatsapp_number:
                whatsapp_url = build_whatsapp_url(
                    settings.whatsapp_number,
                    self._build_whatsapp_message(
                        customer_name=created_lead.name,
                        customer_phone=created_lead.phone,
                        product_name=product.name if product else None,
                        variant_name=variant.color_name if variant else None,
                        note=created_lead.message,
                    ),
                )

        return LeadCreateResponse(
            id=created_lead.id,
            source=created_lead.source,
            status=created_lead.status,
            whatsapp_url=whatsapp_url,
            detail=detail,
        )

    def list_admin_leads(
        self,
        db: Session,
        *,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AdminLeadRead], int]:
        total_count = self.lead_repository.count_all(db, status=status, source=source, search=search)
        leads = self.lead_repository.list_all(db, status=status, source=source, search=search, limit=limit, offset=offset)
        return [self._to_admin_lead_read(lead) for lead in leads], total_count

    def get_admin_lead(self, db: Session, lead_id: int) -> AdminLeadRead:
        lead = self.lead_repository.get_by_id(db, lead_id)
        if lead is None:
            raise NotFoundError(f"Lead with id '{lead_id}' was not found.")
        return self._to_admin_lead_read(lead)

    def update_admin_lead_status(
        self,
        db: Session,
        lead_id: int,
        payload: AdminLeadStatusUpdate,
    ) -> AdminLeadRead:
        lead = self.lead_repository.get_by_id(db, lead_id)
        if lead is None:
            raise NotFoundError(f"Lead with id '{lead_id}' was not found.")
            
        old_status = lead.status
        lead.status = payload.status
        
        from app.models.enums import LeadStatus
        if old_status != payload.status:
            if payload.status == LeadStatus.CONTACTED and not lead.contacted_at:
                lead.contacted_at = datetime.now(timezone.utc)
            elif payload.status == LeadStatus.CLOSED and not lead.closed_at:
                lead.closed_at = datetime.now(timezone.utc)

        saved = self.lead_repository.save(db, lead)
        return self._to_admin_lead_read(saved)

    def delete_admin_lead(self, db: Session, lead_id: int) -> bool:
        lead = self.lead_repository.get_by_id(db, lead_id)
        if lead is None:
            raise NotFoundError(f"Lead with id '{lead_id}' was not found.")
        return self.lead_repository.delete(db, lead_id)

    def _build_whatsapp_message(
        self,
        customer_name: str,
        customer_phone: str,
        product_name: str | None,
        variant_name: str | None,
        note: str | None,
    ) -> str:
        parts = [f"Hello EV Nation, I am {customer_name}."]
        if product_name:
            parts.append(f"I am interested in {product_name}.")
        if variant_name:
            parts.append(f"Preferred color: {variant_name}.")
        if note:
            parts.append(f"Message: {note}.")
        parts.append(f"My phone number is {customer_phone}.")
        return " ".join(parts)

    def _to_admin_lead_read(self, lead: Lead) -> AdminLeadRead:
        return AdminLeadRead(
            id=lead.id,
            name=lead.name,
            phone=lead.phone,
            product_id=lead.product_id,
            product_name=lead.product.name if lead.product else None,
            variant_id=lead.variant_id,
            variant_name=lead.variant.color_name if lead.variant else None,
            message=lead.message,
            source=lead.source,
            status=lead.status,
            preferred_contact_time=lead.preferred_contact_time,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            contacted_at=lead.contacted_at,
            closed_at=lead.closed_at,
        )
