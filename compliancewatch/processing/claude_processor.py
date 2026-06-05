"""
Uses the Claude Batch API to analyze unprocessed regulations overnight.

Each regulation gets a structured analysis: plain-English summary, affected industries,
severity, action items, and citations — all extracted via forced tool use.

Batch API gives 50% cost reduction vs real-time calls.
Prompt caching on the system prompt saves ~90% on the shared regulatory context.
"""
import json
import logging
import time
from datetime import datetime
from typing import Optional

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from sqlalchemy.orm import Session

from compliancewatch.config import settings, CLAUDE_MODEL, INDUSTRIES
from compliancewatch.models import Regulation, RegulationAnalysis

logger = logging.getLogger(__name__)

EXTRACT_TOOL = {
    "name": "extract_compliance_data",
    "description": (
        "Extract structured compliance information from a US federal regulatory document "
        "for a small business owner audience."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "plain_english_summary": {
                "type": "string",
                "description": (
                    "2-3 sentence plain English summary of what this regulation does. "
                    "Written for a small business owner with no legal background. "
                    "No jargon. Start with the practical impact."
                ),
            },
            "affected_industries": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": INDUSTRIES,
                },
                "description": "List of industries materially affected by this regulation.",
            },
            "severity": {
                "type": "string",
                "enum": ["informational", "low", "medium", "high", "critical"],
                "description": (
                    "How urgently a small business needs to act. "
                    "critical=immediate action required (effective date < 30 days or significant penalties). "
                    "high=action within 30-90 days. "
                    "medium=action within 90-180 days. "
                    "low=good to know but no near-term action. "
                    "informational=proposed rule, no action yet."
                ),
            },
            "action_required": {
                "type": "boolean",
                "description": "True if the business owner needs to take any concrete action.",
            },
            "action_items": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Specific, concrete actions a small business should take. "
                    "Each item is a complete sentence starting with a verb. "
                    "Empty array if no action required."
                ),
            },
            "relevant_cfr_sections": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Specific CFR sections affected, e.g. '29 CFR 1910.1200' for OSHA Hazard Communication. "
                    "Empty array if not applicable."
                ),
            },
            "penalty_exposure": {
                "type": "string",
                "description": (
                    "Plain English description of potential fines or penalties for non-compliance "
                    "if mentioned in the document. Empty string if not mentioned."
                ),
            },
            "effective_date_note": {
                "type": "string",
                "description": (
                    "Plain English note about when this takes effect and any compliance deadlines. "
                    "Empty string if no effective date."
                ),
            },
        },
        "required": [
            "plain_english_summary",
            "affected_industries",
            "severity",
            "action_required",
            "action_items",
            "relevant_cfr_sections",
            "penalty_exposure",
            "effective_date_note",
        ],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = (
    "You are a regulatory compliance expert specializing in US federal regulations "
    "that affect small businesses (1-50 employees). "
    "Your job is to analyze federal regulatory documents and extract structured information "
    "that helps small business owners understand what changed, whether it affects them, "
    "and exactly what they need to do. "
    "Be accurate, practical, and use plain language. "
    "If a regulation does not materially affect small businesses, mark it as informational with no action required. "
    "Focus on the practical impact, not legal theory."
)


def _build_user_message(reg: Regulation) -> str:
    parts = [
        f"Agency: {reg.agency}",
        f"Document Type: {reg.document_type}",
        f"Title: {reg.title}",
    ]
    if reg.published_date:
        parts.append(f"Published: {reg.published_date}")
    if reg.effective_date:
        parts.append(f"Effective Date: {reg.effective_date}")
    if reg.comment_close_date:
        parts.append(f"Comment Period Closes: {reg.comment_close_date}")
    if reg.abstract:
        parts.append(f"\nSummary:\n{reg.abstract}")

    return "\n".join(parts)


def _build_batch_requests(regulations: list[Regulation]) -> list[Request]:
    requests = []
    for reg in regulations:
        requests.append(
            Request(
                custom_id=str(reg.id),
                params=MessageCreateParamsNonStreaming(
                    model=CLAUDE_MODEL,
                    max_tokens=1024,
                    thinking={"type": "disabled"},
                    system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    tools=[EXTRACT_TOOL],
                    tool_choice={"type": "tool", "name": "extract_compliance_data"},
                    messages=[
                        {
                            "role": "user",
                            "content": _build_user_message(reg),
                        }
                    ],
                ),
            )
        )
    return requests


def _extract_tool_input(message) -> Optional[dict]:
    for block in message.content:
        if block.type == "tool_use" and block.name == "extract_compliance_data":
            return block.input
    return None


def run_processing(db: Session, batch_size: int = 500) -> dict:
    """
    Processes unanalyzed regulations using the Claude Batch API.
    Returns a summary dict with counts.
    """
    unprocessed = (
        db.query(Regulation)
        .outerjoin(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
        .filter(RegulationAnalysis.id == None)  # noqa: E711
        .limit(batch_size)
        .all()
    )

    if not unprocessed:
        logger.info("No unprocessed regulations found")
        return {"submitted": 0, "succeeded": 0, "errored": 0}

    logger.info("Processing %d regulations via Claude Batch API", len(unprocessed))

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    requests = _build_batch_requests(unprocessed)

    batch = client.messages.batches.create(requests=requests)
    logger.info("Batch created: %s", batch.id)

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        logger.info(
            "Batch %s: %d processing, %d succeeded so far",
            batch.id,
            batch.request_counts.processing,
            batch.request_counts.succeeded,
        )
        time.sleep(60)

    succeeded = 0
    errored = 0

    for result in client.messages.batches.results(batch.id):
        reg_id = int(result.custom_id)

        if result.result.type == "succeeded":
            tool_input = _extract_tool_input(result.result.message)
            if not tool_input:
                logger.warning("No tool use block in result for regulation %d", reg_id)
                errored += 1
                continue

            analysis = RegulationAnalysis(
                regulation_id=reg_id,
                plain_english_summary=tool_input["plain_english_summary"],
                affected_industries=tool_input["affected_industries"],
                severity=tool_input["severity"],
                action_required=tool_input["action_required"],
                action_items=tool_input["action_items"],
                relevant_cfr_sections=tool_input.get("relevant_cfr_sections", []),
                penalty_exposure=tool_input.get("penalty_exposure", ""),
                effective_date_note=tool_input.get("effective_date_note", ""),
                batch_id=batch.id,
                processed_at=datetime.utcnow(),
            )
            db.add(analysis)
            succeeded += 1

        elif result.result.type == "errored":
            logger.error(
                "Batch error for regulation %d: %s",
                reg_id,
                result.result.error.type,
            )
            errored += 1

    db.commit()

    logger.info(
        "Batch processing complete: %d succeeded, %d errored",
        succeeded, errored,
    )

    return {
        "submitted": len(unprocessed),
        "succeeded": succeeded,
        "errored": errored,
        "batch_id": batch.id,
    }
