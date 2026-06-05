"""
Polls the Federal Register API for new rules and proposed rules.

Free, no auth required. Covers every federal agency from 1994 onward.
API docs: https://www.federalregister.gov/reader-aids/developer-resources/rest-api
"""
import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from compliancewatch.config import settings, TRACKED_AGENCIES
from compliancewatch.models import Regulation, IngestRun

logger = logging.getLogger(__name__)

BASE_URL = "https://www.federalregister.gov/api/v1"
DOCUMENT_TYPES = ["RULE", "PRORULE"]
FIELDS = [
    "document_number",
    "title",
    "abstract",
    "agency_names",
    "agencies",
    "type",
    "effective_on",
    "publication_date",
    "pdf_url",
    "full_text_xml_url",
    "html_url",
    "action",
    "comment_close_date",
]


HEADERS = {
    "User-Agent": "ComplianceWatch/1.0 (regulatory monitoring; contact@compliancewatch.app)",
    "Accept": "application/json",
}


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=16))
def _fetch_page(client: httpx.Client, params: dict) -> dict:
    response = client.get(
        f"{BASE_URL}/documents.json", params=params, timeout=30, headers=HEADERS
    )
    response.raise_for_status()
    return response.json()


def _build_params(since_date: date, page: int) -> dict:
    params = {
        "conditions[publication_date][gte]": since_date.isoformat(),
        "per_page": "100",
        "page": str(page),
        "order": "newest",
    }
    for doc_type in DOCUMENT_TYPES:
        params.setdefault("conditions[type][]", [])
        if isinstance(params["conditions[type][]"], list):
            params["conditions[type][]"].append(doc_type)

    for agency in TRACKED_AGENCIES:
        params.setdefault("conditions[agencies][]", [])
        if isinstance(params["conditions[agencies][]"], list):
            params["conditions[agencies][]"].append(agency)

    for field in FIELDS:
        params.setdefault("fields[]", [])
        if isinstance(params["fields[]"], list):
            params["fields[]"].append(field)

    return params


def _doc_to_regulation(doc: dict) -> dict:
    agency_names = doc.get("agency_names", [])
    agencies = doc.get("agencies", [])
    agency_slug = agencies[0].get("slug", "") if agencies else ""

    return {
        "document_number": doc["document_number"],
        "source": "federal_register",
        "agency": ", ".join(agency_names) if agency_names else "Unknown",
        "agency_slug": agency_slug,
        "title": doc.get("title", ""),
        "document_type": doc.get("type", ""),
        "abstract": doc.get("abstract") or "",
        "effective_date": _parse_date(doc.get("effective_on")),
        "published_date": _parse_date(doc.get("publication_date")) or date.today(),
        "comment_close_date": _parse_date(doc.get("comment_close_date")),
        "html_url": doc.get("html_url"),
        "pdf_url": doc.get("pdf_url"),
        "full_text_url": doc.get("full_text_xml_url"),
        "raw_data": doc,
    }


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def run_ingest(db: Session, lookback_days: Optional[int] = None) -> IngestRun:
    days = lookback_days or settings.ingest_lookback_days
    since = date.today() - timedelta(days=days)

    run = IngestRun(source="federal_register")
    db.add(run)
    db.commit()

    logger.info("Federal Register ingest: fetching documents since %s", since)

    try:
        total_found = 0
        total_new = 0
        page = 1

        with httpx.Client() as client:
            while True:
                params = _build_params(since, page)
                data = _fetch_page(client, params)

                docs = data.get("results", [])
                total_count = data.get("count", 0)

                if not docs:
                    break

                for doc in docs:
                    total_found += 1
                    doc_number = doc.get("document_number", "")
                    if not doc_number:
                        continue

                    existing = (
                        db.query(Regulation)
                        .filter(Regulation.document_number == doc_number)
                        .first()
                    )
                    if existing:
                        continue

                    reg_data = _doc_to_regulation(doc)
                    regulation = Regulation(**reg_data)
                    db.add(regulation)
                    total_new += 1

                db.commit()
                logger.info(
                    "Page %d: %d docs fetched, %d new (total count: %d)",
                    page, len(docs), total_new, total_count,
                )

                fetched_so_far = page * 100
                if fetched_so_far >= total_count or len(docs) < 100:
                    break

                page += 1

        run.documents_found = total_found
        run.documents_new = total_new
        from datetime import datetime
        run.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            "Federal Register ingest complete: %d found, %d new",
            total_found, total_new,
        )

    except Exception as exc:
        logger.exception("Federal Register ingest failed")
        run.error = str(exc)
        from datetime import datetime
        run.completed_at = datetime.utcnow()
        db.commit()
        raise

    return run
