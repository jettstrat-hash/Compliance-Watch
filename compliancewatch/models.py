from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, Boolean, Date, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from compliancewatch.database import Base


class Regulation(Base):
    __tablename__ = "regulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # federal_register | osha_rss | fda_rss
    agency: Mapped[str] = mapped_column(String(128), nullable=False)
    agency_slug: Mapped[Optional[str]] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)  # RULE | PRORULE | NOTICE
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    published_date: Mapped[date] = mapped_column(Date, nullable=False)
    comment_close_date: Mapped[Optional[date]] = mapped_column(Date)
    html_url: Mapped[Optional[str]] = mapped_column(String(512))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512))
    full_text_url: Mapped[Optional[str]] = mapped_column(String(512))
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped[Optional["RegulationAnalysis"]] = relationship(
        back_populates="regulation", uselist=False
    )


class RegulationAnalysis(Base):
    __tablename__ = "regulation_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regulations.id"), unique=True, nullable=False
    )
    plain_english_summary: Mapped[str] = mapped_column(Text, nullable=False)
    affected_industries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # informational|low|medium|high|critical
    action_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action_items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    relevant_cfr_sections: Mapped[list] = mapped_column(JSON, default=list)
    penalty_exposure: Mapped[Optional[str]] = mapped_column(Text)
    effective_date_note: Mapped[Optional[str]] = mapped_column(Text)
    batch_id: Mapped[Optional[str]] = mapped_column(String(128))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    regulation: Mapped["Regulation"] = relationship(back_populates="analysis")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    business_name: Mapped[Optional[str]] = mapped_column(String(256))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(64))
    subscription_status: Mapped[str] = mapped_column(String(32), default="trial")
    plan: Mapped[str] = mapped_column(String(16), default="basic")
    industries: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    alert_deliveries: Mapped[list["AlertDelivery"]] = relationship(back_populates="customer")


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    regulation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regulations.id"), nullable=False
    )
    delivery_type: Mapped[str] = mapped_column(String(16), nullable=False)  # urgent | weekly_digest
    email_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    delivered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="alert_deliveries")


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    documents_found: Mapped[int] = mapped_column(Integer, default=0)
    documents_new: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text)
