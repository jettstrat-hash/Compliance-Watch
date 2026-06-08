"""
MJML-based email templates for ComplianceWatch.

Replaces hand-written table HTML with MJML markup that compiles to
cross-client compatible HTML — Outlook, Gmail, Apple Mail, mobile.

Design principles (Stripe/Linear-inspired):
  - White cards on light-gray background, near-black text
  - Severity signaled by left-border accent color only (never colored backgrounds)
  - 3-size type hierarchy: 19px title / 15px body / 11px meta
  - Monospace font for CFR citations — signals precision and authority
  - Aggressive whitespace: content breathes
  - One accent color (blue) used only for links

Install: pip install mjml
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# ── Severity ──────────────────────────────────────────────────────────────────

SEVERITY_COLOR = {
    "critical":      "#DC2626",
    "high":          "#D97706",
    "medium":        "#2563EB",
    "low":           "#059669",
    "informational": "#94A3B8",
}

SEVERITY_LABEL = {
    "critical":      "Critical — Immediate Action Required",
    "high":          "High Priority — Action Within 30 Days",
    "medium":        "Medium — Action Within 90 Days",
    "low":           "Low — For Your Awareness",
    "informational": "Informational — Proposed Rule",
}

DOC_TYPE_LABEL = {
    "RULE":    "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE":  "Notice",
}

# ── Design tokens ─────────────────────────────────────────────────────────────

FONT  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica Neue, Arial, sans-serif"
MONO  = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace"

BG      = "#F1F5F9"   # page background
WHITE   = "#FFFFFF"   # card background
BORDER  = "#E2E8F0"   # dividers / code borders
STRIPE  = "#F8FAFC"   # inset block background (action list)
TEXT    = "#374151"   # body text
TEXT_DK = "#111827"   # headings
TEXT_SM = "#6B7280"   # labels / section headers
TEXT_XS = "#9CA3AF"   # meta / footer
ACCENT  = "#1D4ED8"   # links only


# ── Helpers ───────────────────────────────────────────────────────────────────

def _days_until(d: Optional[date]) -> Optional[int]:
    if not d:
        return None
    delta = (d - date.today()).days
    return delta if delta >= 0 else None


def _esc(s) -> str:
    return (str(s) if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _compile(mjml_string: str) -> str:
    from mjml import mjml_to_html
    result = mjml_to_html(mjml_string)
    if getattr(result, "errors", None):
        logger.warning("MJML warnings: %s", result.errors)
    return result.html


# ── MJML building blocks ──────────────────────────────────────────────────────

def _head() -> str:
    return f"""  <mj-head>
    <mj-attributes>
      <mj-all font-family="{FONT}" />
      <mj-text font-size="15px" line-height="1.65" color="{TEXT}" padding="0" />
      <mj-section background-color="{BG}" padding="0" />
      <mj-column padding="0" />
    </mj-attributes>
    <mj-style>
      a {{ color: {ACCENT}; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </mj-style>
  </mj-head>"""


def _header(label: str) -> str:
    return f"""
  <mj-section padding="32px 0 20px 0">
    <mj-column>
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
          <td style="font-size:18px;font-weight:800;color:{TEXT_DK};letter-spacing:-0.3px;">
            ComplianceWatch
          </td>
          <td align="right"
              style="font-size:11px;font-weight:600;color:{TEXT_XS};
                     text-transform:uppercase;letter-spacing:0.8px;">{label}</td>
        </tr></table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _intro(business: str, headline: str, body: str) -> str:
    return f"""
  <mj-section padding="0 0 16px 0">
    <mj-column background-color="{WHITE}" padding="28px 32px">
      <mj-text font-size="12px" color="{TEXT_XS}" padding="0 0 6px 0">For {business}</mj-text>
      <mj-text font-size="18px" font-weight="700" color="{TEXT_DK}" line-height="1.35"
               padding="0 0 12px 0">{headline}</mj-text>
      <mj-text font-size="14px" color="{TEXT}" line-height="1.6" padding="0 0 20px 0">
        {body}
      </mj-text>
      <mj-divider border-color="{BORDER}" border-width="1px" padding="0" />
    </mj-column>
  </mj-section>"""


def _card(reg) -> str:
    a     = reg.analysis
    color = SEVERITY_COLOR.get(a.severity, "#94A3B8")
    sev   = SEVERITY_LABEL.get(a.severity, a.severity.upper())
    dtype = DOC_TYPE_LABEL.get(reg.document_type, reg.document_type)
    days  = _days_until(reg.effective_date)

    # effective date row
    if days is not None:
        if days == 0:
            eff = f'<span style="color:#DC2626;font-weight:600;">Effective TODAY</span>'
        elif days <= 30:
            eff = (f'<span style="color:#DC2626;font-weight:600;">'
                   f'Effective in {days} day{"s" if days != 1 else ""} &mdash; {reg.effective_date}</span>')
        else:
            eff = f'<span style="color:{TEXT};">Effective {reg.effective_date} &mdash; {days} days away</span>'
        eff_row = f'<tr><td style="padding-top:14px;font-size:13px;">{eff}</td></tr>'
    elif a.effective_date_note:
        eff_row = (f'<tr><td style="padding-top:14px;font-size:13px;color:{TEXT};">'
                   f'{_esc(a.effective_date_note)}</td></tr>')
    else:
        eff_row = ""

    # numbered action items
    if a.action_items:
        rows = "".join(
            f'<tr><td style="padding:6px 0;font-size:14px;color:{TEXT_DK};line-height:1.5;">'
            f'<span style="color:{color};font-weight:700;margin-right:10px;font-size:13px;">'
            f'{i+1}.</span>{_esc(item)}</td></tr>'
            for i, item in enumerate(a.action_items)
        )
        actions = f"""<tr><td style="padding-top:22px;">
          <p style="margin:0 0 10px 0;font-size:11px;font-weight:600;color:{TEXT_SM};
              text-transform:uppercase;letter-spacing:0.8px;">What To Do</p>
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background:{STRIPE};padding:14px 16px;border-radius:4px;">{rows}</table>
        </td></tr>"""
    else:
        actions = ""

    # penalty
    penalty = (
        f'<tr><td style="padding-top:18px;">'
        f'<p style="margin:0 0 5px 0;font-size:11px;font-weight:600;color:{TEXT_SM};'
        f'text-transform:uppercase;letter-spacing:0.8px;">Penalty Risk</p>'
        f'<p style="margin:0;font-size:13px;color:{TEXT};line-height:1.5;">'
        f'{_esc(a.penalty_exposure)}</p></td></tr>'
        if a.penalty_exposure else ""
    )

    # monospace CFR citations
    if a.relevant_cfr_sections:
        codes = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(
            f'<code style="font-family:{MONO};font-size:12px;background:{STRIPE};'
            f'color:{TEXT_DK};padding:2px 7px;border-radius:3px;border:1px solid {BORDER};">'
            f'{_esc(s)}</code>'
            for s in a.relevant_cfr_sections
        )
        cfr = f'<tr><td style="padding-top:16px;line-height:2.2;">{codes}</td></tr>'
    else:
        cfr = ""

    source = (
        f'<tr><td style="padding-top:18px;font-size:13px;">'
        f'<a href="{reg.html_url}" style="color:{ACCENT};font-weight:500;text-decoration:none;">'
        f'View on Federal Register &rarr;</a></td></tr>'
        if reg.html_url else ""
    )

    return f"""
  <mj-section padding="0 0 14px 0">
    <mj-column border-left="4px solid {color}" background-color="{WHITE}" padding="24px 28px">
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">

          <tr><td style="padding-bottom:12px;">
            <span style="font-size:11px;font-weight:700;color:{color};
                text-transform:uppercase;letter-spacing:0.7px;">{sev}</span><br>
            <span style="font-size:11px;color:{TEXT_XS};">{_esc(reg.agency)}</span>
            <span style="margin:0 5px;color:{BORDER};">&middot;</span>
            <span style="font-size:11px;color:{TEXT_XS};">{dtype}</span>
            <span style="margin:0 5px;color:{BORDER};">&middot;</span>
            <span style="font-size:11px;color:{TEXT_XS};">{reg.published_date}</span>
          </td></tr>

          <tr><td style="padding-bottom:14px;">
            <span style="font-size:19px;font-weight:700;color:{TEXT_DK};line-height:1.3;">
              {_esc(reg.title)}
            </span>
          </td></tr>

          <tr><td style="font-size:15px;color:{TEXT};line-height:1.65;">
            {_esc(a.plain_english_summary)}
          </td></tr>

          {eff_row}
          {actions}
          {penalty}
          {cfr}
          {source}

        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _footer(customer) -> str:
    return f"""
  <mj-section padding="8px 0 36px 0">
    <mj-column>
      <mj-text font-size="11px" color="{TEXT_XS}" align="center" line-height="1.9">
        You're receiving this because you subscribed to ComplianceWatch.<br>
        <a href="https://compliancewatch.app/unsubscribe?email={customer.email}"
           style="color:{TEXT_XS};">Unsubscribe</a>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="https://compliancewatch.app/settings"
           style="color:{TEXT_XS};">Update Preferences</a>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="https://compliancewatch.app/dashboard"
           style="color:{TEXT_XS};">Dashboard</a>
        <br><br>
        ComplianceWatch &nbsp;&middot;&nbsp; Austin, TX 78701
      </mj-text>
    </mj-column>
  </mj-section>"""


def _wrap(content: str) -> str:
    return f"""<mjml>
{_head()}
  <mj-body background-color="{BG}">
    {content}
  </mj-body>
</mjml>"""


# ── Public API ────────────────────────────────────────────────────────────────

def urgent_subject(reg) -> str:
    days = _days_until(reg.effective_date)
    if days is not None and days <= 30:
        return f"Action required: {reg.agency} rule takes effect in {days} days"
    return f"Compliance alert: {reg.title[:72]}"


def urgent_html(reg, customer) -> str:
    business = _esc(customer.business_name or customer.email)
    return _compile(_wrap(
        _header("Compliance Alert")
        + _intro(
            business,
            "A federal regulation affecting your business requires attention.",
            "We found a new rule that applies to your industry. "
            "Details and recommended actions are below.",
        )
        + _card(reg)
        + _footer(customer)
    ))


def urgent_text(reg, customer) -> str:
    a    = reg.analysis
    days = _days_until(reg.effective_date)
    lines = [
        "ComplianceWatch — Compliance Alert",
        f"For: {customer.business_name or customer.email}",
        "", "=" * 62,
        f"[{a.severity.upper()}] {reg.title}",
        f"{reg.agency}  |  {reg.document_type}  |  Published {reg.published_date}",
    ]
    if days is not None:
        lines.append(f"Effective in {days} days ({reg.effective_date})")
    lines += ["", a.plain_english_summary]
    if a.action_items:
        lines += ["", "WHAT TO DO:"]
        for i, item in enumerate(a.action_items, 1):
            lines.append(f"  {i}. {item}")
    if a.penalty_exposure:
        lines += ["", f"PENALTY RISK: {a.penalty_exposure}"]
    if a.relevant_cfr_sections:
        lines += ["", "CFR: " + "  ·  ".join(a.relevant_cfr_sections)]
    if reg.html_url:
        lines += ["", f"Source: {reg.html_url}"]
    lines += [
        "", "─" * 62,
        "You're receiving this because you subscribed to ComplianceWatch.",
        f"Unsubscribe: https://compliancewatch.app/unsubscribe?email={customer.email}",
        "ComplianceWatch · Austin, TX 78701",
    ]
    return "\n".join(lines)


def digest_subject(regulations: list, customer) -> str:
    n      = len(regulations)
    urgent = sum(1 for r in regulations if r.analysis.severity in ("critical", "high"))
    if urgent:
        s = "s" if urgent > 1 else ""
        return f"ComplianceWatch Weekly — {urgent} urgent alert{s} require your attention"
    return f"ComplianceWatch Weekly — {n} new compliance update{'s' if n != 1 else ''}"


def digest_html(regulations: list, customer) -> str:
    business = _esc(customer.business_name or customer.email)
    n      = len(regulations)
    urgent = sum(1 for r in regulations if r.analysis.severity in ("critical", "high"))

    body = (
        f"You have <strong style='color:{TEXT_DK};'>{urgent} urgent "
        f"item{'s' if urgent > 1 else ''}</strong> requiring action, "
        f"plus {n - urgent} additional update{'s' if n - urgent != 1 else ''}."
        if urgent else
        f"Here are this week's {n} compliance update{'s' if n != 1 else ''} relevant to your business."
    )

    return _compile(_wrap(
        _header("Weekly Digest")
        + _intro(business, "Your weekly compliance briefing", body)
        + "\n".join(_card(r) for r in regulations)
        + _footer(customer)
    ))


def digest_text(regulations: list, customer) -> str:
    n = len(regulations)
    lines = [
        "ComplianceWatch — Weekly Digest",
        f"For: {customer.business_name or customer.email}",
        f"{n} compliance update{'s' if n != 1 else ''} this week", "",
    ]
    for reg in regulations:
        a    = reg.analysis
        days = _days_until(reg.effective_date)
        lines += [
            "=" * 62,
            f"[{a.severity.upper()}] {reg.title}",
            f"{reg.agency}  |  {reg.document_type}  |  Published {reg.published_date}",
        ]
        if days is not None:
            lines.append(f"Effective in {days} days ({reg.effective_date})")
        lines += ["", a.plain_english_summary]
        if a.action_items:
            lines += ["", "WHAT TO DO:"]
            for i, item in enumerate(a.action_items, 1):
                lines.append(f"  {i}. {item}")
        if a.penalty_exposure:
            lines += ["", f"PENALTY RISK: {a.penalty_exposure}"]
        if a.relevant_cfr_sections:
            lines += ["", "CFR: " + "  ·  ".join(a.relevant_cfr_sections)]
        if reg.html_url:
            lines += ["", f"Source: {reg.html_url}"]
        lines.append("")
    lines += [
        "─" * 62,
        "You're receiving this because you subscribed to ComplianceWatch.",
        f"Unsubscribe: https://compliancewatch.app/unsubscribe?email={customer.email}",
        "Update preferences: https://compliancewatch.app/settings",
        "ComplianceWatch · Austin, TX 78701",
    ]
    return "\n".join(lines)
