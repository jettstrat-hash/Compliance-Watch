"""
Sends emails via the SendGrid v3 API using raw httpx — no SDK dependency.

SendGrid free tier: 100 emails/day, sufficient for early customers.
Upgrade path: Postmark (better deliverability) or AWS SES (cheapest at scale).
"""
import logging
from dataclasses import dataclass

import httpx

from compliancewatch.config import settings

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    html_content: str
    text_content: str


def send_email(message: EmailMessage) -> bool:
    """
    Sends a single email via SendGrid.
    Returns True on success, False on failure (logs the error).
    """
    if not settings.sendgrid_api_key:
        logger.warning("SENDGRID_API_KEY not set — printing email to stdout instead")
        _print_to_stdout(message)
        return True

    payload = {
        "personalizations": [
            {"to": [{"email": message.to_email}]}
        ],
        "from": {
            "email": settings.sendgrid_from_email,
            "name": settings.sendgrid_from_name,
        },
        "subject": message.subject,
        "content": [
            {"type": "text/plain", "value": message.text_content},
            {"type": "text/html", "value": message.html_content},
        ],
        "tracking_settings": {
            "click_tracking": {"enable": False},
            "open_tracking": {"enable": True},
        },
    }

    try:
        response = httpx.post(
            SENDGRID_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if response.status_code == 202:
            logger.info("Email sent to %s: %s", message.to_email, message.subject)
            return True
        else:
            logger.error(
                "SendGrid error %d for %s: %s",
                response.status_code, message.to_email, response.text[:300],
            )
            return False
    except Exception:
        logger.exception("Failed to send email to %s", message.to_email)
        return False


def _print_to_stdout(message: EmailMessage) -> None:
    print("\n" + "=" * 70)
    print(f"  TO:      {message.to_email}")
    print(f"  SUBJECT: {message.subject}")
    print("=" * 70)
    print(message.text_content)
    print("=" * 70 + "\n")
