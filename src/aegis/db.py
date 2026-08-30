"""Database models and manager with connection pooling and soft deletes."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, create_engine, not_
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class InvestigationRecord(Base):
    """SQLAlchemy model for investigation records with soft deletes."""
    __tablename__ = "investigations"

    trace_id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), nullable=False, index=True)
    question = Column(Text, nullable=False)
    conclusion = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)  # JSON string
    confidence = Column(Float, nullable=False)
    review_required = Column(Boolean, nullable=False, default=True)
    generated_at = Column(DateTime, nullable=False)
    agent_results = Column(Text, nullable=False)  # JSON string

    # HITL review fields
    reviewed = Column(Boolean, default=False)
    review_decision = Column(String(20), nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Soft delete and timestamps
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "patient_id": self.patient_id,
            "question": self.question,
            "conclusion": self.conclusion,
            "evidence": json.loads(self.evidence) if self.evidence else [],
            "confidence": self.confidence,
            "review_required": self.review_required,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "agent_results": json.loads(self.agent_results) if self.agent_results else [],
            "reviewed": self.reviewed,
            "review_decision": self.review_decision,
            "reviewer_id": self.reviewer_id,
            "review_notes": self.review_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseManager:
    """Database manager with connection pooling and soft deletes."""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite:///./aegis.db"
        )

        # Configure connection pooling
        if "postgresql" in self.database_url:
            # PostgreSQL with connection pooling
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )
        elif "sqlite" in self.database_url:
            # SQLite with thread-safe settings
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(self.database_url)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def save_investigation(self, report: Any) -> None:
        """Save an investigation report to the database."""
        session = self.get_session()
        try:
            record = InvestigationRecord(
                trace_id=report.trace_id,
                patient_id=report.patient_id,
                question=report.question,
                conclusion=report.conclusion,
                evidence=json.dumps(report.evidence),
                confidence=report.confidence,
                review_required=report.review_required,
                generated_at=report.generated_at,
                agent_results=json.dumps([ar.model_dump() for ar in report.agent_results]),
                reviewed=report.reviewed,
                review_decision=report.review_decision.value if report.review_decision else None,
                reviewer_id=report.reviewer_id,
                review_notes=report.review_notes,
                reviewed_at=report.reviewed_at,
            )
            session.merge(record)  # Upsert
            session.commit()
        finally:
            session.close()

    def get_investigation(self, trace_id: str, include_deleted: bool = False) -> InvestigationRecord | None:
        """Get an investigation record by trace_id."""
        session = self.get_session()
        try:
            query = session.query(InvestigationRecord).filter(
                InvestigationRecord.trace_id == trace_id
            )
            if not include_deleted:
                query = query.filter(not_(InvestigationRecord.is_deleted))
            return query.first()
        finally:
            session.close()

    def list_investigations(
        self,
        patient_id: str | None = None,
        reviewed: bool | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[list[InvestigationRecord], int]:
        """List investigation records with optional filtering and pagination.

        Returns:
            Tuple of (list of records, total count)
        """
        session = self.get_session()
        try:
            query = session.query(InvestigationRecord)

            # Filter out soft-deleted records by default
            if not include_deleted:
                query = query.filter(not_(InvestigationRecord.is_deleted))

            if patient_id is not None:
                query = query.filter(InvestigationRecord.patient_id == patient_id)

            if reviewed is not None:
                query = query.filter(InvestigationRecord.reviewed == reviewed)

            # Get total count before pagination
            total = query.count()

            query = query.order_by(InvestigationRecord.generated_at.desc())
            records = query.offset(offset).limit(limit).all()

            return records, total
        finally:
            session.close()

    def soft_delete(self, trace_id: str) -> bool:
        """Soft delete an investigation record.

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        try:
            record = session.query(InvestigationRecord).filter(
                InvestigationRecord.trace_id == trace_id,
                not_(InvestigationRecord.is_deleted),
            ).first()

            if record is None:
                return False

            record.is_deleted = True
            record.deleted_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            session.commit()
            return True
        finally:
            session.close()

    def restore(self, trace_id: str) -> bool:
        """Restore a soft-deleted investigation record.

        Returns:
            True if restored, False if not found or not deleted
        """
        session = self.get_session()
        try:
            record = session.query(InvestigationRecord).filter(
                InvestigationRecord.trace_id == trace_id,
                InvestigationRecord.is_deleted,
            ).first()

            if record is None:
                return False

            record.is_deleted = False
            record.deleted_at = None
            record.updated_at = datetime.utcnow()
            session.commit()
            return True
        finally:
            session.close()

    def get_all_investigations(
        self,
        include_deleted: bool = False,
    ) -> list[InvestigationRecord]:
        """Get all investigation records."""
        session = self.get_session()
        try:
            query = session.query(InvestigationRecord)
            if not include_deleted:
                query = query.filter(not_(InvestigationRecord.is_deleted))
            return query.all()
        finally:
            session.close()

    def count_investigations(self, include_deleted: bool = False) -> int:
        """Count all investigation records."""
        session = self.get_session()
        try:
            query = session.query(InvestigationRecord)
            if not include_deleted:
                query = query.filter(not_(InvestigationRecord.is_deleted))
            return query.count()
        finally:
            session.close()

    def export_investigations(
        self,
        format: str = "json",
        include_deleted: bool = False,
    ) -> str | bytes:
        """Export all investigations in the specified format.

        Args:
            format: Export format ('json' or 'csv')
            include_deleted: Whether to include soft-deleted records

        Returns:
            Exported data as string (JSON) or bytes (CSV)
        """
        records = self.get_all_investigations(include_deleted=include_deleted)

        if format == "json":
            data = [record.to_dict() for record in records]
            return json.dumps(data, indent=2, default=str)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if not records:
                return ""

            # Get field names from first record
            fieldnames = list(records[0].to_dict().keys())

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for record in records:
                writer.writerow(record.to_dict())

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_db(database_url: str | None = None) -> DatabaseManager:
    """Initialize the database."""
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    _db_manager.create_tables()
    return _db_manager
