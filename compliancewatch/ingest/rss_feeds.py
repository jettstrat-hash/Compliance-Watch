"""
Parses OSHA and FDA RSS feeds for enforcement notices and guidance updates
that don't always appear in the Federal Register feed.
"""
import hashlib
import logging
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from xml.etree import ElementTree as ET

import httpx
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from compliancewatch.models import Regulation, IngestRun

logger = logging.getLogger(__name__)

FEEDS = {
    "osha_standards": {
        "url": "https://www.osha.gov/rss/standards.xml",
        "agency": "Occupational Safety and Health Administration",
        "agency_slug": "occupational-safety-and-health-administration",
        "source": "osha_rss",
    },
    "osha_news": {
        "url": "https://www.osha.gov/rss/news.xml",
        "agency": "Occupational Safety and Health Administration",
        "agency_slug": "occupational-safety-and-health-administration",
        "source": "osha_rss",
    },
    "fda_news": {
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
        "agency": "Food and Drug Administration",
        "agency_slug": "food-and-drug-administration",
        "source": "fda_rss",
    },
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8))
def _fetch_xml(url: str) -> ET.Element:
    response = httpx.get(url, timeout=20, follow_redirects=True)
    response.raise_for_status()
    return ET.fromstring(response.content)


def _text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _parse_rss_date(raw: str) -> Optional[date]:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date()
    except Exception:
        return None


def _parse_items(root: ET.Element) -> list[dict]:
    items = []
    channel = root.find("channel") or root
    for item in channel.findall("item"):
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        description = _text(item.find("description"))
        pub_date = _parse_rss_date(_text(item.find("pubDate")))
        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date or date.today(),
        })
    return items


def _doc_number(feed_name: str, item: dict) -> str:
    uid = item["link"] or item["title"]
    return f"rss-{feed_name}-{hashlib.sha1(uid.encode()).hexdigest()[:16]}"


def run_ingest(db: Session) -> list[IngestRun]:
    runs = []

    for feed_name, feed_config in FEEDS.items():
        run = IngestRun(source=feed_config["source"])
        db.add(run)
        db.commit()

        logger.info("RSS ingest: %s", feed_name)

        try:
            root = _fetch_xml(feed_config["url"])
            items = _parse_items(root)

            found = len(items)
            new_count = 0

            for item in items:
                doc_number = _doc_number(feed_name, item)
                existing = (
                    db.query(Regulation)
                    .filter(Regulation.document_number == doc_number)
                    .first()
                )
                if existing:
                    continue

                reg = Regulation(
                    document_number=doc_number,
                    source=feed_config["source"],
                    agency=feed_config["agency"],
                    agency_slug=feed_config["agency_slug"],
                    title=item["title"] or "Untitled",
                    document_type="NOTICE",
                    abstract=item["description"][:2000] if item["description"] else "",
                    published_date=item["pub_date"],
                    html_url=item["link"] or None,
                    raw_data={
                        "feed": feed_name,
                        "title": item["title"],
                        "link": item["link"],
                        "description": item["description"],
                    },
                )
                db.add(reg)
                new_count += 1

            db.commit()

            run.documents_found = found
            run.documents_new = new_count
            run.completed_at = datetime.utcnow()
            db.commit()

            logger.info("%s: %d found, %d new", feed_name, found, new_count)

        except Exception as exc:
            logger.exception("RSS ingest failed for %s", feed_name)
            run.error = str(exc)
            run.completed_at = datetime.utcnow()
            db.commit()

        runs.append(run)

    return runs
