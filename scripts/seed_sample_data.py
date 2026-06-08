#!/usr/bin/env python3
"""
Seeds realistic sample regulatory documents to demo the Claude processing pipeline.
Use this to test processing without needing live API access.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.models import Regulation
from rich.console import Console

console = Console()

SAMPLE_REGULATIONS = [
    {
        "document_number": "2026-09801",
        "source": "federal_register",
        "agency": "Occupational Safety and Health Administration",
        "agency_slug": "occupational-safety-and-health-administration",
        "title": "Walking-Working Surfaces and Personal Protective Equipment (Fall Protection Systems) for General Industry",
        "document_type": "RULE",
        "abstract": (
            "OSHA is amending its general industry standards for walking-working surfaces and personal "
            "protective equipment (PPE) to update fall protection requirements. The final rule requires "
            "employers to ensure that workers are protected from falls by providing and ensuring the use "
            "of fall protection systems. Employers with open-sided floors or platforms 4 feet or more "
            "above the adjacent floor level must guard every open side and edge with a standard railing, "
            "or equivalent protection. Employers must ensure that workers use personal fall arrest systems "
            "when exposed to fall hazards of more than 4 feet in general industry settings. "
            "Violations can result in citations of up to $16,550 per violation."
        ),
        "effective_date": date(2026, 9, 1),
        "published_date": date(2026, 6, 5),
        "comment_close_date": None,
        "html_url": "https://www.federalregister.gov/documents/2026/06/05/2026-09801/walking-working-surfaces",
        "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2026-06-05/pdf/2026-09801.pdf",
    },
    {
        "document_number": "2026-08342",
        "source": "federal_register",
        "agency": "Food and Drug Administration",
        "agency_slug": "food-and-drug-administration",
        "title": "Food Safety Modernization Act: Sanitary Transportation of Human and Animal Food; Final Rule Amendments",
        "document_type": "RULE",
        "abstract": (
            "FDA is amending the sanitary transportation rule to clarify requirements for vehicles and "
            "transportation equipment used to transport food for human consumption. "
            "The rule now explicitly requires that all food transporters maintain written sanitation "
            "procedures, maintain temperature logs for refrigerated foods, and ensure that vehicles "
            "used for food transport are not used to transport materials that could contaminate food. "
            "Small businesses with fewer than $1 million in food sales have an additional 12 months "
            "to comply. Businesses that fail to comply may be subject to FDA warning letters, "
            "import alerts, and mandatory recalls. Penalties for serious violations may include "
            "civil monetary penalties of up to $500,000 per year."
        ),
        "effective_date": date(2026, 8, 15),
        "published_date": date(2026, 6, 4),
        "comment_close_date": None,
        "html_url": "https://www.federalregister.gov/documents/2026/06/04/2026-08342/fda-food-safety-sanitary-transportation",
        "pdf_url": None,
    },
    {
        "document_number": "2026-07901",
        "source": "federal_register",
        "agency": "Wage and Hour Division",
        "agency_slug": "wage-and-hour-division",
        "title": "Defining and Delimiting the Exemptions for Executive, Administrative, Professional, Outside Sales, and Computer Employees",
        "document_type": "RULE",
        "abstract": (
            "The Department of Labor is issuing a final rule to update the salary level thresholds "
            "for the white-collar overtime exemptions under the Fair Labor Standards Act (FLSA). "
            "Effective January 1, 2027, the standard salary level for the executive, administrative, "
            "and professional employee exemptions increases from $684 per week ($35,568 per year) "
            "to $1,128 per week ($58,656 per year). The highly compensated employee (HCE) threshold "
            "increases from $107,432 to $151,164 annually. Employers must either pay affected employees "
            "overtime for hours worked over 40 per week, increase their salaries to meet the new threshold, "
            "or reclassify them as non-exempt. The rule includes automatic updates every three years."
        ),
        "effective_date": date(2027, 1, 1),
        "published_date": date(2026, 6, 3),
        "comment_close_date": None,
        "html_url": "https://www.federalregister.gov/documents/2026/06/03/2026-07901/flsa-overtime-rule",
        "pdf_url": None,
    },
    {
        "document_number": "2026-06512",
        "source": "federal_register",
        "agency": "Federal Trade Commission",
        "agency_slug": "federal-trade-commission",
        "title": "Negative Option Marketing Rule Amendments",
        "document_type": "RULE",
        "abstract": (
            "The FTC is amending its Negative Option Rule to address unfair or deceptive practices "
            "in subscription services and negative option marketing programs. The final rule requires "
            "businesses to clearly disclose all material terms before obtaining consumers' billing "
            "information, obtain express informed consent before charging, and provide simple cancellation "
            "mechanisms. Businesses must allow consumers to cancel subscriptions through the same medium "
            "used to sign up (e.g., if they can subscribe online, they must be able to cancel online). "
            "Violations are subject to civil penalties up to $51,744 per violation. "
            "This rule applies to all businesses offering subscription services, memberships, or "
            "any other negative option marketing program, including small businesses."
        ),
        "effective_date": date(2026, 7, 15),
        "published_date": date(2026, 5, 30),
        "comment_close_date": None,
        "html_url": "https://www.federalregister.gov/documents/2026/05/30/2026-06512/ftc-negative-option-rule",
        "pdf_url": None,
    },
    {
        "document_number": "2026-05123",
        "source": "federal_register",
        "agency": "Environmental Protection Agency",
        "agency_slug": "environmental-protection-agency",
        "title": "National Emission Standards for Hazardous Air Pollutants: Small Business Applicability",
        "document_type": "PRORULE",
        "abstract": (
            "EPA is proposing to update the national emission standards for hazardous air pollutants "
            "(NESHAP) to clarify applicability requirements for small businesses classified as area sources. "
            "The proposed rule would establish new record-keeping requirements for small manufacturers, "
            "auto body shops, dry cleaners, and other area source categories using perchloroethylene, "
            "chromium compounds, or other listed hazardous air pollutants. "
            "Area source facilities that use more than specified threshold quantities must implement "
            "management practices, conduct annual inspections, and maintain records for five years. "
            "EPA requests public comment on compliance costs for small businesses and whether additional "
            "exemptions are warranted for businesses with fewer than 10 employees."
        ),
        "effective_date": None,
        "published_date": date(2026, 5, 28),
        "comment_close_date": date(2026, 7, 28),
        "html_url": "https://www.federalregister.gov/documents/2026/05/28/2026-05123/neshap-small-business",
        "pdf_url": None,
    },
    {
        "document_number": "rss-osha_standards-a1b2c3d4e5f6",
        "source": "osha_rss",
        "agency": "Occupational Safety and Health Administration",
        "agency_slug": "occupational-safety-and-health-administration",
        "title": "OSHA Enforcement Memo: Increased Inspections for Restaurant Industry During Summer Season",
        "document_type": "NOTICE",
        "abstract": (
            "OSHA has issued an enforcement directive increasing targeted inspections for food service "
            "establishments during summer months (June-September). Inspections will focus on heat illness "
            "prevention, slip and fall hazards, chemical hazards (cleaning agents), and recordkeeping "
            "compliance under 29 CFR Part 1904. Restaurants found to have inadequate written hazard "
            "communication programs, missing OSHA 300 logs, or improper chemical storage may face "
            "serious citations of up to $16,550 per violation."
        ),
        "effective_date": date(2026, 6, 1),
        "published_date": date(2026, 6, 1),
        "comment_close_date": None,
        "html_url": "https://www.osha.gov/news/newsreleases/osha-national-news-release/20260601",
        "pdf_url": None,
    },
]


def main():
    create_tables()
    db = SessionLocal()

    try:
        added = 0
        for reg_data in SAMPLE_REGULATIONS:
            existing = (
                db.query(Regulation)
                .filter(Regulation.document_number == reg_data["document_number"])
                .first()
            )
            if existing:
                console.print(f"[yellow]Already exists: {reg_data['document_number']}[/yellow]")
                continue

            reg = Regulation(**reg_data)
            db.add(reg)
            added += 1

        db.commit()
        console.print(f"[green]✓ Seeded {added} sample regulations[/green]")

        total = db.query(Regulation).count()
        console.print(f"[cyan]Total regulations in DB: {total}[/cyan]")

    finally:
        db.close()


if __name__ == "__main__":
    main()
