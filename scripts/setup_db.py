#!/usr/bin/env python3
"""Creates database tables and optionally seeds a test customer."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.models import Customer
from rich.console import Console

console = Console()


def main():
    console.print("[bold green]Creating database tables...[/bold green]")
    create_tables()
    console.print("[green]✓ Tables created[/green]")

    if "--seed" in sys.argv:
        db = SessionLocal()
        try:
            existing = db.query(Customer).filter(Customer.email == "demo@example.com").first()
            if not existing:
                customer = Customer(
                    email="demo@example.com",
                    business_name="Demo Restaurant LLC",
                    industries=["restaurant_food_service", "retail"],
                    subscription_status="trial",
                    plan="basic",
                )
                db.add(customer)
                db.commit()
                console.print("[green]✓ Seeded demo customer: demo@example.com[/green]")
            else:
                console.print("[yellow]Demo customer already exists[/yellow]")
        finally:
            db.close()

    console.print("[bold green]Database setup complete![/bold green]")


if __name__ == "__main__":
    main()
