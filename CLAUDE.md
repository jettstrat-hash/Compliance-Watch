# ComplianceWatch

US federal regulatory compliance tracker for small businesses. Monitors OSHA, FDA, FTC, DOL, EPA and 10 other agencies. Sends plain-English email alerts when rules change. Target price: $30-80/mo per business.

## Session Start Checklist

**Every new session must do this first:**

1. Verify the keys are available as environment variables (set once in Claude Code environment settings — never stored in the repo):
```bash
printenv ANTHROPIC_API_KEY SENDGRID_API_KEY
```
If both print values, write `.env` (gitignored):
```bash
cat > .env <<EOF
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
SENDGRID_API_KEY=$SENDGRID_API_KEY
SENDGRID_FROM_EMAIL=jett.strat@gmail.com
SENDGRID_FROM_NAME=ComplianceWatch
DATABASE_URL=sqlite:///./compliancewatch.db
APP_ENV=development
EOF
```
If the vars are empty, ask the user to add them in **Claude Code → Settings → Environments → Compliance Watch**.

2. Install dependencies:
```bash
pip install -q anthropic httpx sqlalchemy python-dotenv "pydantic>=2.7.0" pydantic-settings sendgrid tenacity rich schedule "mjml==0.12.0" --ignore-installed cryptography
```

3. Verify network access is working:
```bash
curl -s https://api.ipify.org
```
If this returns "Host not in allowlist", the session is running under Limited networking. The user must start a new session with the **Compliance Watch** environment selected (Unrestricted networking).

## Architecture

```
Federal Register API ──┐
RSS Feeds (OSHA/FDA) ──┼─→ ingest/ ──→ Regulation DB ──→ processing/ ──→ RegulationAnalysis DB
                        │                                    (Claude Batch API)
                        │                                         │
                        └─────────────────────────────────────────┴──→ alerts/ ──→ SendGrid ──→ Customer inbox
```

## Project Structure

```
compliancewatch/
  config.py          — settings (pydantic-settings), TRACKED_AGENCIES, INDUSTRIES, CLAUDE_MODEL
  models.py          — SQLAlchemy models: Regulation, RegulationAnalysis, Customer, AlertDelivery, IngestRun
  database.py        — SessionLocal, create_tables()
  ingest/
    federal_register.py  — polls FR API, deduplicates by document_number
    rss_feeds.py         — OSHA + FDA RSS via stdlib xml.etree + httpx
  processing/
    claude_processor.py  — Claude Batch API, forced tool use, prompt caching
  alerts/
    templates.py     — MJML email templates (Federal Gazette design)
    sender.py        — SendGrid v3 raw httpx POST
    dispatcher.py    — urgent alerts + weekly digest, deduplication via AlertDelivery

scripts/
  scheduler.py       — persistent process, runs full pipeline on schedule
  run_ingest.py      — manual ingest trigger
  run_processing.py  — manual Claude processing trigger
  run_alerts.py      — manual alert dispatch + --preview mode
  seed_sample_data.py — 6 sample regulations for testing
  setup_db.py        — create tables
  query_alerts.py    — inspect delivered alerts in DB
```

## Key Design Decisions

- **Claude Batch API** — 50% cost reduction vs real-time; `run_processing.py` polls until batch completes
- **MJML templates** — `pip install mjml` (pure Python); Federal Gazette aesthetic (warm cream, Georgia serif, amber accent)
- **SQLite for dev** — `DATABASE_URL=sqlite:///./compliancewatch.db`; swap to PostgreSQL for production
- **SendGrid raw httpx** — no SDK, direct POST to `https://api.sendgrid.com/v3/mail/send`
- **Severity levels** — critical / high / medium / low / informational; only critical+high trigger urgent alerts

## Scheduler (scripts/scheduler.py)

```
02:00 UTC daily  — ingest (Federal Register + RSS)
03:00 UTC daily  — Claude batch processing
04:00 UTC daily  — urgent alert dispatch
09:00 UTC Monday — weekly digest dispatch
```

Run immediately for testing:
```bash
python scripts/scheduler.py --run-now --force-digest
```

## Pipeline Test (Step 2 — in progress)

This is the current work item. Steps to complete the end-to-end test:

```bash
# 1. Seed sample data
python scripts/seed_sample_data.py

# 2. Process with Claude
python scripts/run_processing.py

# 3. Add yourself as a test customer (run once)
python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from dotenv import load_dotenv; load_dotenv(".env")
from compliancewatch.database import create_tables, SessionLocal
from compliancewatch.models import Customer
create_tables()
db = SessionLocal()
if not db.query(Customer).filter(Customer.email == "jett.strat@gmail.com").first():
    db.add(Customer(email="jett.strat@gmail.com", business_name="Jett's Test Business",
                    subscription_status="active", plan="pro",
                    industries=["all_businesses","restaurant_food_service","construction","retail"]))
    db.commit()
    print("Customer created.")
db.close()
EOF

# 4. Send urgent alerts
python scripts/run_alerts.py --urgent

# 5. Send weekly digest
python scripts/run_alerts.py --digest --force
```

## Roadmap (in order)

- [x] 1. Automated scheduler
- [ ] 2. End-to-end pipeline test (current — blocked on Unrestricted networking in environment)
- [ ] 3. Landing page
- [ ] 4. Customer signup + industry selection
- [ ] 5. Stripe billing

## Environment Setup

- **Claude Code environment**: "Compliance Watch" — must be set to **Unrestricted** networking
- **API keys**: pre-filled above — write `.env` at session start (gitignored, never committed)
- **Federal Register API**: free, no auth; returns 403 from cloud IPs with Limited networking
- **SendGrid**: sender `jett.strat@gmail.com` verified via Single Sender Verification

## Git

- **Branch**: `claude/remote-control-0GRnz`
- **Remote**: `jettstrat-hash/Compliance-Watch` (repo was renamed from bookish-umbrella)
