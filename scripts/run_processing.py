#!/usr/bin/env python3
"""
Runs Claude Batch API processing on all unanalyzed regulations.

Designed to run nightly after ingest. Processes up to 500 documents per run.
50% cost reduction vs real-time via Batch API.

Usage:
    python scripts/run_processing.py
    python scripts/run_processing.py --batch-size 100
    python scripts/run_processing.py --dry-run     # show what would be processed
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.models import Regulation, RegulationAnalysis
from compliancewatch.processing import claude_processor
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Process regulations with Claude")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without running")
    args = parser.parse_args()

    create_tables()
    db = SessionLocal()

    try:
        unprocessed_count = (
            db.query(Regulation)
            .outerjoin(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
            .filter(RegulationAnalysis.id == None)  # noqa: E711
            .count()
        )

        console.print(f"\n[bold cyan]Unprocessed regulations: {unprocessed_count}[/bold cyan]")

        if unprocessed_count == 0:
            console.print("[yellow]Nothing to process.[/yellow]")
            return

        if args.dry_run:
            sample = (
                db.query(Regulation)
                .outerjoin(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
                .filter(RegulationAnalysis.id == None)  # noqa: E711
                .limit(10)
                .all()
            )
            table = Table(title="Sample (dry run)", show_header=True)
            table.add_column("ID", justify="right")
            table.add_column("Agency", style="cyan")
            table.add_column("Type")
            table.add_column("Title")
            for reg in sample:
                table.add_row(str(reg.id), reg.agency[:30], reg.document_type, reg.title[:60])
            console.print(table)
            console.print(f"\n[yellow]Dry run — would process up to {args.batch_size} of {unprocessed_count} regulations[/yellow]")
            return

        console.print(f"[green]Submitting up to {args.batch_size} to Claude Batch API...[/green]")
        result = claude_processor.run_processing(db, batch_size=args.batch_size)

        console.print("\n[bold green]Processing complete![/bold green]")
        console.print(f"  Submitted: {result['submitted']}")
        console.print(f"  Succeeded: {result['succeeded']}")
        console.print(f"  Errored:   {result['errored']}")
        if "batch_id" in result:
            console.print(f"  Batch ID:  {result['batch_id']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
