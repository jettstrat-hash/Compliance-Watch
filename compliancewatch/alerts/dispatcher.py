"""
Matches analyzed regulations to customers and dispatches email alerts.

Two delivery modes:
  - Urgent: fires as soon as a critical/high regulation is processed
  - Weekly digest: groups all new alerts from the past 7 days, sent Monday mornings

Deduplication: AlertDelivery records prevent the same regulation from being
sent to the same customer twice regardless of how many times the job runs.
"""
import logging
from datetime import datetime, timedelta, date
from typing import Literal

from sqlalchemy.orm import Session

from compliancewatch.models import (
    Regulation, RegulationAnalysis, Customer, AlertDelivery
)
from compliancewatch.alerts import templates, sender

logger = logging.getLogger(__name__)

URGENT_SEVERITIES = {"critical", "high"}
DAYS_LOOKBACK_DIGEST = 7


def _industries_match(customer_industries: list[str], alert_industries: list[str]) -> bool:
    if "all_businesses" in alert_industries:
        return True
    return bool(set(customer_industries) & set(alert_industries))


def _already_delivered(db: Session, customer_id: int, regulation_id: int) -> bool:
    return (
        db.query(AlertDelivery)
        .filter(
            AlertDelivery.customer_id == customer_id,
            AlertDelivery.regulation_id == regulation_id,
        )
        .first()
    ) is not None


def _record_delivery(
    db: Session,
    customer_id: int,
    regulation_id: int,
    delivery_type: str,
    message_id: str = "",
) -> None:
    delivery = AlertDelivery(
        customer_id=customer_id,
        regulation_id=regulation_id,
        delivery_type=delivery_type,
        email_message_id=message_id,
        delivered_at=datetime.utcnow(),
    )
    db.add(delivery)
    db.commit()


def _active_customers(db: Session) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.subscription_status.in_(["active", "trial"]))
        .all()
    )


# ---------------------------------------------------------------------------
# Urgent alerts
# ---------------------------------------------------------------------------

def dispatch_urgent(db: Session) -> dict:
    """
    Finds all undelivered critical/high regulations and sends one batched
    email per customer containing all their relevant alerts. This avoids
    flooding customers with separate emails when multiple rules drop at once.
    """
    customers = _active_customers(db)
    if not customers:
        logger.info("No active customers — skipping urgent dispatch")
        return {"sent": 0, "skipped": 0}

    urgent_regs = (
        db.query(Regulation)
        .join(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
        .filter(RegulationAnalysis.severity.in_(URGENT_SEVERITIES))
        .all()
    )

    sent = 0
    skipped = 0

    for customer in customers:
        if not customer.industries:
            skipped += 1
            continue

        new_regs = [
            r for r in urgent_regs
            if _industries_match(customer.industries, r.analysis.affected_industries)
            and not _already_delivered(db, customer.id, r.id)
        ]

        if not new_regs:
            skipped += 1
            continue

        # Sort: critical first, then by effective date proximity
        new_regs.sort(key=lambda r: (
            0 if r.analysis.severity == "critical" else 1,
            r.effective_date or date.max,
        ))

        msg = sender.EmailMessage(
            to_email=customer.email,
            subject=templates.urgent_batch_subject(new_regs),
            html_content=templates.urgent_batch_html(new_regs, customer),
            text_content=templates.urgent_batch_text(new_regs, customer),
        )
        success = sender.send_email(msg)
        if success:
            for reg in new_regs:
                _record_delivery(db, customer.id, reg.id, "urgent")
            sent += 1
        else:
            logger.error("Failed urgent batch delivery for customer %d", customer.id)

    logger.info("Urgent dispatch: %d sent, %d skipped", sent, skipped)
    return {"sent": sent, "skipped": skipped}


# ---------------------------------------------------------------------------
# Weekly digest
# ---------------------------------------------------------------------------

def dispatch_weekly_digest(db: Session, force: bool = False) -> dict:
    """
    Sends a weekly digest of all new alerts to each customer.
    By default only runs on Mondays; pass force=True to run any day (for testing).
    """
    if not force and datetime.utcnow().weekday() != 0:
        logger.info("Weekly digest skipped — not Monday (use force=True to override)")
        return {"sent": 0, "skipped": 0}

    customers = _active_customers(db)
    since = datetime.utcnow() - timedelta(days=DAYS_LOOKBACK_DIGEST)

    sent = 0
    skipped = 0

    for customer in customers:
        if not customer.industries:
            skipped += 1
            continue

        candidate_regs = (
            db.query(Regulation)
            .join(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
            .filter(RegulationAnalysis.processed_at >= since)
            .filter(RegulationAnalysis.severity != "informational")
            .all()
        )

        new_regs = [
            r for r in candidate_regs
            if _industries_match(customer.industries, r.analysis.affected_industries)
            and not _already_delivered(db, customer.id, r.id)
        ]

        if not new_regs:
            skipped += 1
            continue

        new_regs.sort(
            key=lambda r: (
                list(URGENT_SEVERITIES).index(r.analysis.severity)
                if r.analysis.severity in URGENT_SEVERITIES else 99
            )
        )

        msg = sender.EmailMessage(
            to_email=customer.email,
            subject=templates.digest_subject(new_regs, customer),
            html_content=templates.digest_html(new_regs, customer),
            text_content=templates.digest_text(new_regs, customer),
        )
        success = sender.send_email(msg)
        if success:
            for reg in new_regs:
                _record_delivery(db, customer.id, reg.id, "weekly_digest")
            sent += 1
        else:
            logger.error("Failed weekly digest for customer %d", customer.id)

    logger.info("Weekly digest: %d sent, %d skipped", sent, skipped)
    return {"sent": sent, "skipped": skipped}
