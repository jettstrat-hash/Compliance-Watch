#!/usr/bin/env python3
"""
Runs all data ingestion sources: Federal Register API + OSHA/FDA RSS feeds.

Usage:
    python scripts/run_ingest.py
    python scripts/run_ingest.py --lookback 7      # fetch last 7 days
    python scripts/run_ingest.py --source federal   # only Federal Register
    python scripts/run_ingest.py --source rss       # only RSS feeds
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.ingest import federal_register, rss_feeds
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ingest regulatory data")
    parser.add_argument("--lookback", type=int, default=1, help="Days to look back (default: 1)")
    parser.add_argument("--source", choices=["federal", "rss", "all"], default="all")
    args = parser.parse_args()

    create_tables()
    db = SessionLocal()

    try:
        results = []

        if args.source in ("federal", "all"):
            console.print("\n[bold cyan]Fetching Federal Register...[/bold cyan]")
            run = federal_register.run_ingest(db, lookback_days=args.lookback)
            results.append({
                "source": "Federal Register",
                "found": run.documents_found,
                "new": run.documents_new,
                "error": run.error or "",
            })

        if args.source in ("rss", "all"):
            console.print("\n[bold cyan]Fetching RSS feeds...[/bold cyan]")
            runs = rss_feeds.run_ingest(db)
            for run in runs:
                results.append({
                    "source": f"RSS: {run.source}",
                    "found": run.documents_found,
                    "new": run.documents_new,
                    "error": run.error or "",
                })

        table = Table(title="\nIngest Results", show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Found", justify="right")
        table.add_column("New", justify="right", style="green")
        table.add_column("Error", style="red")

        for r in results:
            table.add_row(r["source"], str(r["found"]), str(r["new"]), r["error"])

        console.print(table)

    finally:
        db.close()


if __name__ == "__main__":
    main()
