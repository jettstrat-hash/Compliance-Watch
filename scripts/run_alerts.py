#!/usr/bin/env python3
"""
Dispatches email alerts to customers.

Usage:
    python scripts/run_alerts.py --urgent            # send urgent alerts now
    python scripts/run_alerts.py --digest            # send weekly digest (Mondays only)
    python scripts/run_alerts.py --digest --force    # send digest regardless of day
    python scripts/run_alerts.py --preview EMAIL     # preview what a customer would receive
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from compliancewatch.database import SessionLocal
from compliancewatch.alerts import dispatcher
from rich.console import Console

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
console = Console()


def preview_mode(db, email: str):
    from compliancewatch.models import Customer, Regulation, RegulationAnalysis
    from compliancewatch.alerts import templates, sender
    from datetime import datetime, timedelta

    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        console.print(f"[red]Customer not found: {email}[/red]")
        return

    since = datetime.utcnow() - timedelta(days=7)
    regs = (
        db.query(Regulation)
        .join(RegulationAnalysis, Regulation.id == RegulationAnalysis.regulation_id)
        .filter(RegulationAnalysis.processed_at >= since)
        .filter(RegulationAnalysis.severity != "informational")
        .all()
    )

    if not regs:
        console.print("[yellow]No analyzed regulations found. Run run_processing.py first.[/yellow]")
        return

    # use all regs for preview regardless of industry match
    msg = sender.EmailMessage(
        to_email=customer.email,
        subject=templates.digest_subject(regs, customer),
        html_content=templates.digest_html(regs, customer),
        text_content=templates.digest_text(regs, customer),
    )

    # Write HTML preview to file
    preview_path = "/tmp/compliancewatch_preview.html"
    with open(preview_path, "w") as f:
        f.write(msg.html_content)

    console.print(f"\n[bold green]Preview written to:[/bold green] {preview_path}")
    console.print(f"[cyan]Subject:[/cyan] {msg.subject}")
    console.print(f"[cyan]To:[/cyan] {msg.to_email}")
    console.print(f"[cyan]Regulations included:[/cyan] {len(regs)}")
    console.print("\n[dim]Plain text version:[/dim]")
    console.print(msg.text_content)


def main():
    parser = argparse.ArgumentParser(description="Dispatch compliance email alerts")
    parser.add_argument("--urgent", action="store_true", help="Send urgent alerts")
    parser.add_argument("--digest", action="store_true", help="Send weekly digest")
    parser.add_argument("--force", action="store_true", help="Force digest even if not Monday")
    parser.add_argument("--preview", metavar="EMAIL", help="Preview email for a customer (no send)")
    args = parser.parse_args()

    if not any([args.urgent, args.digest, args.preview]):
        parser.print_help()
        return

    db = SessionLocal()
    try:
        if args.preview:
            preview_mode(db, args.preview)
            return

        if args.urgent:
            console.print("\n[bold cyan]Dispatching urgent alerts...[/bold cyan]")
            result = dispatcher.dispatch_urgent(db)
            console.print(f"  Sent:    {result['sent']}")
            console.print(f"  Skipped: {result['skipped']}")

        if args.digest:
            console.print("\n[bold cyan]Dispatching weekly digest...[/bold cyan]")
            result = dispatcher.dispatch_weekly_digest(db, force=args.force)
            console.print(f"  Sent:    {result['sent']}")
            console.print(f"  Skipped: {result['skipped']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
