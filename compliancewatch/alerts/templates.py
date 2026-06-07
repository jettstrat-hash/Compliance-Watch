"""
HTML and plain-text email templates for ComplianceWatch alerts.

Two email types:
  - Urgent alert: one email per high/critical regulation, sent as soon as processed
  - Weekly digest: grouped summary of all new alerts, sent every Monday morning
"""
from datetime import date
from typing import Optional


SEVERITY_COLOR = {
    "critical": "#C0392B",
    "high":     "#E67E22",
    "medium":   "#F1C40F",
    "low":      "#27AE60",
    "informational": "#7F8C8D",
}

SEVERITY_LABEL = {
    "critical": "CRITICAL — Action Required Immediately",
    "high":     "HIGH — Action Required Within 30 Days",
    "medium":   "MEDIUM — Action Required Within 90 Days",
    "low":      "LOW — Good to Know",
    "informational": "INFORMATIONAL — Proposed Rule",
}

DOC_TYPE_LABEL = {
    "RULE":    "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE":  "Enforcement Notice",
}


def _days_until(d: Optional[date]) -> Optional[int]:
    if not d:
        return None
    delta = (d - date.today()).days
    return delta if delta >= 0 else None


def _severity_badge(severity: str) -> str:
    color = SEVERITY_COLOR.get(severity, "#7F8C8D")
    label = SEVERITY_LABEL.get(severity, severity.upper())
    return (
        f'<span style="display:inline-block;background:{color};color:#ffffff;'
        f'font-size:11px;font-weight:700;letter-spacing:0.5px;padding:4px 10px;'
        f'border-radius:3px;text-transform:uppercase;">{label}</span>'
    )


def _action_items_html(items: list[str]) -> str:
    if not items:
        return ""
    rows = "".join(
        f'<tr><td style="padding:6px 0 6px 0;vertical-align:top;color:#2C3E50;">'
        f'<span style="color:#E67E22;font-weight:700;margin-right:8px;">&#10003;</span>'
        f'{item}</td></tr>'
        for item in items
    )
    return f"""
    <tr><td style="padding-top:20px;">
      <p style="margin:0 0 10px 0;font-size:13px;font-weight:700;color:#2C3E50;
                text-transform:uppercase;letter-spacing:0.5px;">What You Need to Do</p>
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#FFF8F0;border-left:3px solid #E67E22;padding:12px 16px;">
        {rows}
      </table>
    </td></tr>"""


def _cfr_sections_html(sections: list[str]) -> str:
    if not sections:
        return ""
    text = " &nbsp;·&nbsp; ".join(sections)
    return (
        f'<tr><td style="padding-top:12px;font-size:12px;color:#7F8C8D;">'
        f'<strong>CFR Reference:</strong> {text}</td></tr>'
    )


def _penalty_html(penalty: str) -> str:
    if not penalty:
        return ""
    return (
        f'<tr><td style="padding-top:12px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="background:#FEF9F9;border-left:3px solid #C0392B;padding:10px 14px;">'
        f'<tr><td style="font-size:12px;color:#C0392B;">'
        f'<strong>Penalty Exposure:</strong> {penalty}</td></tr>'
        f'</table></td></tr>'
    )


def _regulation_card_html(reg) -> str:
    """Renders a single regulation as an HTML card block."""
    analysis = reg.analysis
    days = _days_until(reg.effective_date)
    doc_type = DOC_TYPE_LABEL.get(reg.document_type, reg.document_type)

    deadline_html = ""
    if days is not None:
        if days == 0:
            deadline_html = '<span style="color:#C0392B;font-weight:700;">Effective TODAY</span>'
        elif days <= 30:
            deadline_html = f'<span style="color:#C0392B;font-weight:700;">Effective in {days} days ({reg.effective_date})</span>'
        else:
            deadline_html = f'<span style="color:#555;">Effective {reg.effective_date} ({days} days away)</span>'
    elif analysis.effective_date_note:
        deadline_html = f'<span style="color:#555;">{analysis.effective_date_note}</span>'

    source_link = ""
    if reg.html_url:
        source_link = (
            f'<tr><td style="padding-top:14px;">'
            f'<a href="{reg.html_url}" style="font-size:12px;color:#2980B9;text-decoration:none;">'
            f'View full regulation on Federal Register &#8594;</a></td></tr>'
        )

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="margin-bottom:24px;border:1px solid #E8E8E8;border-radius:4px;">
      <tr>
        <td style="padding:20px 24px;background:#FAFAFA;border-bottom:1px solid #E8E8E8;
                   border-radius:4px 4px 0 0;">
          {_severity_badge(analysis.severity)}
          <p style="margin:10px 0 4px 0;font-size:16px;font-weight:700;color:#1A202C;
                    line-height:1.4;">{reg.title}</p>
          <p style="margin:0;font-size:12px;color:#7F8C8D;">
            {reg.agency} &nbsp;·&nbsp; {doc_type} &nbsp;·&nbsp; Published {reg.published_date}
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:20px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="font-size:15px;line-height:1.6;color:#2C3E50;">
                {analysis.plain_english_summary}
              </td>
            </tr>
            {"<tr><td style='padding-top:12px;font-size:13px;'>" + deadline_html + "</td></tr>" if deadline_html else ""}
            {_action_items_html(analysis.action_items)}
            {_penalty_html(analysis.penalty_exposure)}
            {_cfr_sections_html(analysis.relevant_cfr_sections)}
            {source_link}
          </table>
        </td>
      </tr>
    </table>"""


def _regulation_text_block(reg) -> str:
    """Plain-text version of a single regulation."""
    analysis = reg.analysis
    days = _days_until(reg.effective_date)
    lines = [
        f"{'=' * 60}",
        f"[{analysis.severity.upper()}] {reg.title}",
        f"{reg.agency} | {reg.document_type} | Published {reg.published_date}",
    ]
    if days is not None:
        lines.append(f"Effective in {days} days ({reg.effective_date})")
    lines.append("")
    lines.append(analysis.plain_english_summary)
    if analysis.action_items:
        lines.append("")
        lines.append("WHAT YOU NEED TO DO:")
        for item in analysis.action_items:
            lines.append(f"  [ ] {item}")
    if analysis.penalty_exposure:
        lines.append("")
        lines.append(f"PENALTY EXPOSURE: {analysis.penalty_exposure}")
    if reg.html_url:
        lines.append("")
        lines.append(f"Source: {reg.html_url}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Urgent alert (single regulation)
# ---------------------------------------------------------------------------

def urgent_subject(reg) -> str:
    days = _days_until(reg.effective_date)
    if days is not None and days <= 30:
        return f"Action required: {reg.agency} rule takes effect in {days} days"
    return f"Compliance alert: {reg.title[:60]}"


def urgent_html(reg, customer) -> str:
    business = customer.business_name or customer.email
    card = _regulation_card_html(reg)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F7FA;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F7FA;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr><td style="padding-bottom:24px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
                <span style="font-size:20px;font-weight:800;color:#1A202C;letter-spacing:-0.5px;">
                  ComplianceWatch
                </span>
              </td>
              <td align="right">
                <span style="font-size:12px;color:#7F8C8D;">Compliance Alert</span>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Intro -->
        <tr><td style="background:#ffffff;border-radius:4px 4px 0 0;padding:24px 24px 0 24px;">
          <p style="margin:0 0 4px 0;font-size:14px;color:#7F8C8D;">For {business}</p>
          <p style="margin:0 0 20px 0;font-size:18px;font-weight:700;color:#1A202C;line-height:1.4;">
            A federal regulation affecting your business requires attention.
          </p>
          <hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 20px 0;">
        </td></tr>

        <!-- Regulation card -->
        <tr><td style="background:#ffffff;padding:0 24px 24px 24px;">
          {card}
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding-top:24px;">
          <p style="margin:0;font-size:12px;color:#A0AEC0;text-align:center;line-height:1.6;">
            You're receiving this because you subscribed to ComplianceWatch.<br>
            <a href="https://compliancewatch.app/unsubscribe?email={customer.email}"
               style="color:#A0AEC0;">Unsubscribe</a>
            &nbsp;·&nbsp;
            <a href="https://compliancewatch.app/dashboard" style="color:#A0AEC0;">View Dashboard</a>
            <br><br>
            ComplianceWatch &nbsp;·&nbsp; 123 Main St, Suite 100, Austin TX 78701
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def urgent_text(reg, customer) -> str:
    business = customer.business_name or customer.email
    return f"""ComplianceWatch — Compliance Alert
For: {business}

A federal regulation affecting your business requires attention.

{_regulation_text_block(reg)}

---
You're receiving this because you subscribed to ComplianceWatch.
Unsubscribe: https://compliancewatch.app/unsubscribe?email={customer.email}
ComplianceWatch · 123 Main St, Suite 100, Austin TX 78701
"""


# ---------------------------------------------------------------------------
# Weekly digest (multiple regulations)
# ---------------------------------------------------------------------------

def digest_subject(regulations: list, customer) -> str:
    n = len(regulations)
    urgent = sum(1 for r in regulations if r.analysis.severity in ("critical", "high"))
    if urgent:
        return f"ComplianceWatch Weekly — {urgent} urgent alert{'s' if urgent > 1 else ''} require your attention"
    return f"ComplianceWatch Weekly — {n} new compliance update{'s' if n > 1 else ''} this week"


def digest_html(regulations: list, customer) -> str:
    business = customer.business_name or customer.email
    n = len(regulations)
    urgent_count = sum(1 for r in regulations if r.analysis.severity in ("critical", "high"))

    cards = "\n".join(_regulation_card_html(r) for r in regulations)

    if urgent_count:
        intro = (
            f"You have <strong>{urgent_count} urgent item{'s' if urgent_count > 1 else ''}</strong> "
            f"requiring action, plus {n - urgent_count} other update{'s' if n - urgent_count != 1 else ''}."
        )
    else:
        intro = f"Here are this week's {n} compliance update{'s' if n > 1 else ''} relevant to your business."

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F7FA;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F7FA;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr><td style="padding-bottom:24px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
                <span style="font-size:20px;font-weight:800;color:#1A202C;letter-spacing:-0.5px;">
                  ComplianceWatch
                </span>
              </td>
              <td align="right">
                <span style="font-size:12px;color:#7F8C8D;">Weekly Digest</span>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Intro -->
        <tr><td style="background:#ffffff;border-radius:4px 4px 0 0;padding:24px 24px 8px 24px;">
          <p style="margin:0 0 4px 0;font-size:14px;color:#7F8C8D;">For {business}</p>
          <p style="margin:0 0 16px 0;font-size:18px;font-weight:700;color:#1A202C;line-height:1.4;">
            Your weekly compliance briefing
          </p>
          <p style="margin:0 0 20px 0;font-size:14px;color:#4A5568;line-height:1.6;">
            {intro}
          </p>
          <hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 20px 0;">
        </td></tr>

        <!-- Cards -->
        <tr><td style="background:#ffffff;padding:0 24px 24px 24px;">
          {cards}
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding-top:24px;">
          <p style="margin:0;font-size:12px;color:#A0AEC0;text-align:center;line-height:1.6;">
            You're receiving this because you subscribed to ComplianceWatch.<br>
            <a href="https://compliancewatch.app/unsubscribe?email={customer.email}"
               style="color:#A0AEC0;">Unsubscribe</a>
            &nbsp;·&nbsp;
            <a href="https://compliancewatch.app/settings" style="color:#A0AEC0;">Update Preferences</a>
            &nbsp;·&nbsp;
            <a href="https://compliancewatch.app/dashboard" style="color:#A0AEC0;">View Dashboard</a>
            <br><br>
            ComplianceWatch &nbsp;·&nbsp; 123 Main St, Suite 100, Austin TX 78701
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def digest_text(regulations: list, customer) -> str:
    business = customer.business_name or customer.email
    blocks = "\n\n".join(_regulation_text_block(r) for r in regulations)
    return f"""ComplianceWatch — Weekly Digest
For: {business}

{len(regulations)} compliance update(s) this week relevant to your business.

{blocks}

---
You're receiving this because you subscribed to ComplianceWatch.
Unsubscribe: https://compliancewatch.app/unsubscribe?email={customer.email}
Update preferences: https://compliancewatch.app/settings
ComplianceWatch · 123 Main St, Suite 100, Austin TX 78701
"""
