#!/usr/bin/env python3
"""
Preview alerts for a given industry. Useful for testing and demos.

Usage:
    python scripts/query_alerts.py --industry restaurant_food_service
    python scripts/query_alerts.py --industry construction --severity high
    python scripts/query_alerts.py --all
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

from compliancewatch.database import SessionLocal
from compliancewatch.models import Regulation, RegulationAnalysis
from compliancewatch.config import INDUSTRIES
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from sqlalchemy import or_

console = Console()

SEVERITY_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "green",
    "informational": "dim",
}


def main():
    parser = argparse.ArgumentParser(description="Query processed compliance alerts")
    parser.add_argument("--industry", choices=INDUSTRIES, help="Filter by industry")
    parser.add_argument("--severity", choices=["critical", "high", "medium", "low", "informational"])
    parser.add_argument("--all", action="store_true", help="Show all analyzed regulations")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        query = (
            db.query(Regulation, RegulationAnalysis)
            .join(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
        )

        if args.industry:
            query = query.filter(
                RegulationAnalysis.affected_industries.contains([args.industry])
                | RegulationAnalysis.affected_industries.contains(["all_businesses"])
            )

        if args.severity:
            query = query.filter(RegulationAnalysis.severity == args.severity)

        query = query.order_by(RegulationAnalysis.processed_at.desc()).limit(args.limit)
        rows = query.all()

        if not rows:
            console.print("[yellow]No results found.[/yellow]")
            return

        console.print(f"\n[bold]Found {len(rows)} alert(s)[/bold]\n")

        for reg, analysis in rows:
            severity_color = SEVERITY_COLORS.get(analysis.severity, "white")
            header = Text()
            header.append(f"[{analysis.severity.upper()}] ", style=severity_color)
            header.append(reg.title)

            details = []
            details.append(f"Agency:     {reg.agency}")
            details.append(f"Type:       {reg.document_type}")
            details.append(f"Published:  {reg.published_date}")
            if reg.effective_date:
                details.append(f"Effective:  {reg.effective_date}")
            details.append(f"Industries: {', '.join(analysis.affected_industries)}")
            details.append("")
            details.append(analysis.plain_english_summary)

            if analysis.action_items:
                details.append("")
                details.append("Actions Required:")
                for item in analysis.action_items:
                    details.append(f"  • {item}")

            if analysis.penalty_exposure:
                details.append("")
                details.append(f"Penalty risk: {analysis.penalty_exposure}")

            if reg.html_url:
                details.append("")
                details.append(f"Source: {reg.html_url}")

            console.print(Panel("\n".join(details), title=str(header), border_style=severity_color))

    finally:
        db.close()


if __name__ == "__main__":
    main()
