from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from app.models.lead import Lead


class LeadRepository:
    def _load_options(self):
        return (
            selectinload(Lead.product),
            selectinload(Lead.variant),
        )

    def create(self, db: Session, lead: Lead) -> Lead:
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    def _build_list_statement(self, status=None, source=None, search=None):
        statement = select(Lead)
        if status is not None:
            statement = statement.where(Lead.status == status)
        if source is not None:
            statement = statement.where(Lead.source == source)
        if search:
            search_clause = f"%{search}%"
            statement = statement.where(
                or_(
                    Lead.name.ilike(search_clause),
                    Lead.phone.ilike(search_clause),
                    Lead.message.ilike(search_clause)
                )
            )
        return statement

    def count_all(
        self,
        db: Session,
        *,
        status=None,
        source=None,
        search=None,
    ) -> int:
        statement = self._build_list_statement(status=status, source=source, search=search)
        statement = statement.with_only_columns(func.count(Lead.id)).order_by(None)
        return db.scalar(statement) or 0

    def list_all(
        self,
        db: Session,
        *,
        status=None,
        source=None,
        search=None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Lead]:
        statement = self._build_list_statement(status=status, source=source, search=search)
        statement = statement.options(*self._load_options()).order_by(Lead.created_at.desc(), Lead.id.desc())
        statement = statement.limit(limit).offset(offset)
        return list(db.scalars(statement).unique())

    def get_by_id(self, db: Session, lead_id: int) -> Lead | None:
        statement = select(Lead).where(Lead.id == lead_id).options(*self._load_options())
        return db.scalar(statement)

    def save(self, db: Session, lead: Lead) -> Lead:
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return self.get_by_id(db, lead.id) or lead

    def delete(self, db: Session, lead_id: int) -> bool:
        lead = db.scalar(select(Lead).where(Lead.id == lead_id))
        if lead:
            db.delete(lead)
            db.commit()
            return True
        return False
