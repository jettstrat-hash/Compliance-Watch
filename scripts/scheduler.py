#!/usr/bin/env python3
"""
ComplianceWatch nightly scheduler.

Runs as a persistent process (Railway worker / Render background job).
All times are UTC.

Schedule:
  02:00 daily  — ingest Federal Register + RSS feeds
  03:00 daily  — process unanalyzed regulations with Claude Batch API
  04:00 daily  — dispatch urgent alerts (critical / high severity)
  09:00 Monday — dispatch weekly digest to all subscribers

Usage:
  python scripts/scheduler.py            # run scheduler loop (production)
  python scripts/scheduler.py --run-now  # run full pipeline once immediately (testing)
"""
import sys
import os
import time
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

import schedule
from rich.console import Console

from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.ingest import federal_register, rss_feeds
from compliancewatch.processing import claude_processor
from compliancewatch.alerts import dispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler")
console = Console()


# ── Pipeline steps ────────────────────────────────────────────────────────────

def step_ingest():
    logger.info("=== INGEST START ===")
    db = SessionLocal()
    try:
        fr_run = federal_register.run_ingest(db, lookback_days=1)
        logger.info("Federal Register: found=%s new=%s error=%s",
                    fr_run.documents_found, fr_run.documents_new, fr_run.error or "none")

        rss_runs = rss_feeds.run_ingest(db)
        for run in rss_runs:
            logger.info("RSS %s: found=%s new=%s error=%s",
                        run.source, run.documents_found, run.documents_new, run.error or "none")
    except Exception:
        logger.exception("Ingest failed")
    finally:
        db.close()
    logger.info("=== INGEST DONE ===")


def step_process():
    logger.info("=== PROCESSING START ===")
    db = SessionLocal()
    try:
        result = claude_processor.run_processing(db, batch_size=500)
        logger.info("Processing: submitted=%s succeeded=%s errored=%s",
                    result.get("submitted"), result.get("succeeded"), result.get("errored"))
    except Exception:
        logger.exception("Processing failed")
    finally:
        db.close()
    logger.info("=== PROCESSING DONE ===")


def step_urgent_alerts():
    logger.info("=== URGENT ALERTS START ===")
    db = SessionLocal()
    try:
        sent = dispatcher.dispatch_urgent(db)
        logger.info("Urgent alerts sent: %s", sent)
    except Exception:
        logger.exception("Urgent alert dispatch failed")
    finally:
        db.close()
    logger.info("=== URGENT ALERTS DONE ===")


def step_weekly_digest():
    logger.info("=== WEEKLY DIGEST START ===")
    db = SessionLocal()
    try:
        sent = dispatcher.dispatch_weekly_digest(db)
        logger.info("Weekly digest sent: %s", sent)
    except Exception:
        logger.exception("Weekly digest dispatch failed")
    finally:
        db.close()
    logger.info("=== WEEKLY DIGEST DONE ===")


def run_full_pipeline(force_digest: bool = False):
    """Run all four steps in sequence — used for --run-now and manual testing."""
    console.print(f"\n[bold cyan]Pipeline start — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}[/bold cyan]")
    step_ingest()
    step_process()
    step_urgent_alerts()
    if force_digest:
        step_weekly_digest()
    console.print("[bold green]Pipeline complete.[/bold green]\n")


# ── Scheduler loop ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ComplianceWatch scheduler")
    parser.add_argument("--run-now", action="store_true",
                        help="Run the full pipeline immediately then exit")
    parser.add_argument("--force-digest", action="store_true",
                        help="Include weekly digest in --run-now (regardless of day)")
    args = parser.parse_args()

    create_tables()

    if args.run_now:
        run_full_pipeline(force_digest=args.force_digest)
        return

    # ── Production schedule (all UTC) ─────────────────────────────────────────
    schedule.every().day.at("02:00").do(step_ingest)
    schedule.every().day.at("03:00").do(step_process)
    schedule.every().day.at("04:00").do(step_urgent_alerts)
    schedule.every().monday.at("09:00").do(step_weekly_digest)

    console.print("[bold green]ComplianceWatch scheduler running.[/bold green]")
    console.print("  02:00 UTC daily  — ingest")
    console.print("  03:00 UTC daily  — process")
    console.print("  04:00 UTC daily  — urgent alerts")
    console.print("  09:00 UTC Monday — weekly digest")
    console.print("\nPress Ctrl+C to stop.\n")

    logger.info("Scheduler started. Waiting for next job...")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
