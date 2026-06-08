"""
MJML-based email templates for ComplianceWatch.

Design language: modern newsletter (Morning Brew / Axios / TLDR aesthetic)
  - Full-width branded masthead with issue metadata
  - "In this issue" table of contents
  - Story-card format per regulation: deck → summary → bottom line → actions → CTA button
  - Section headers grouping cards by urgency tier
  - mj-button CTAs, proper visual hierarchy, warm palette

Install: pip install mjml
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# ── Severity config ────────────────────────────────────────────────────────────

SEVERITY_COLOR = {
    "critical":      "#B91C1C",
    "high":          "#B45309",
    "medium":        "#1D4ED8",
    "low":           "#047857",
    "informational": "#475569",
}

SEVERITY_BG = {
    "critical":      "#FEE2E2",
    "high":          "#FEF3C7",
    "medium":        "#DBEAFE",
    "low":           "#D1FAE5",
    "informational": "#F1F5F9",
}

SEVERITY_LABEL = {
    "critical":      "CRITICAL",
    "high":          "HIGH PRIORITY",
    "medium":        "MEDIUM",
    "low":           "LOW",
    "informational": "INFORMATIONAL",
}

SEVERITY_SECTION = {
    "critical":      ("URGENT ACTION REQUIRED",  "#7F1D1D", "#FEF2F2"),
    "high":          ("ACTION WITHIN 30 DAYS",   "#78350F", "#FFFBEB"),
    "medium":        ("ACTION WITHIN 90 DAYS",   "#1E3A8A", "#EFF6FF"),
    "low":           ("FOR YOUR AWARENESS",       "#064E3B", "#ECFDF5"),
    "informational": ("MONITORING",               "#334155", "#F8FAFC"),
}

DOC_TYPE_LABEL = {
    "RULE":    "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE":  "Notice",
}

# ── Design tokens ─────────────────────────────────────────────────────────────

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica Neue, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace"

# Page
BG        = "#F0F2F5"

# Masthead
MAST_BG   = "#0F172A"   # slate-900
MAST_LINE = "#F59E0B"   # amber accent stripe
MAST_TEXT = "#F8FAFC"
MAST_META = "#94A3B8"

# Cards / content
WHITE     = "#FFFFFF"
BORDER    = "#E2E8F0"
DIVIDER   = "#CBD5E1"
STRIPE    = "#F8FAFC"

# Typography
TEXT      = "#334155"
TEXT_DK   = "#0F172A"
TEXT_MID  = "#475569"
TEXT_SM   = "#64748B"
TEXT_XS   = "#94A3B8"

# Callout box ("The bottom line")
BTL_BG    = "#FFFBEB"
BTL_LEFT  = "#F59E0B"
BTL_TEXT  = "#92400E"

# Button
BTN_BG    = "#0F172A"
BTN_TEXT  = "#F8FAFC"

# Links
ACCENT    = "#1D4ED8"


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
      <mj-text font-size="15px" line-height="1.7" color="{TEXT}" padding="0" />
      <mj-section background-color="{BG}" padding="0" />
      <mj-column padding="0" />
    </mj-attributes>
    <mj-style>
      a {{ color: {ACCENT}; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </mj-style>
  </mj-head>"""


def _masthead(category: str, sub: str) -> str:
    today = date.today().strftime("%B %d, %Y").upper()
    return f"""
  <!-- amber top stripe -->
  <mj-section background-color="{MAST_LINE}" padding="4px 0" />

  <!-- main masthead -->
  <mj-section background-color="{MAST_BG}" padding="24px 0 20px 0">
    <mj-column>
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td valign="middle">
              <div style="font-size:26px;font-weight:900;color:{MAST_TEXT};
                          letter-spacing:-0.8px;line-height:1;">ComplianceWatch</div>
              <div style="font-size:11px;font-weight:600;color:{MAST_LINE};
                          text-transform:uppercase;letter-spacing:2px;
                          margin-top:5px;">{category}</div>
            </td>
            <td align="right" valign="middle">
              <div style="font-size:10px;color:{MAST_META};text-align:right;
                          text-transform:uppercase;letter-spacing:0.8px;
                          line-height:1.8;">
                {today}<br>{sub}
              </div>
            </td>
          </tr>
        </table>
      </mj-text>
    </mj-column>
  </mj-section>

  <!-- bottom rule -->
  <mj-section background-color="{MAST_BG}" padding="0 0 0 0">
    <mj-column>
      <mj-divider border-color="rgba(255,255,255,0.08)" border-width="1px" padding="0" />
    </mj-column>
  </mj-section>"""


def _toc(regulations: list) -> str:
    rows = ""
    for i, reg in enumerate(regulations, 1):
        color = SEVERITY_COLOR.get(reg.analysis.severity, "#475569")
        bg    = SEVERITY_BG.get(reg.analysis.severity, "#F1F5F9")
        label = SEVERITY_LABEL.get(reg.analysis.severity, "")
        rows += f"""<tr>
          <td width="28" valign="top" style="padding:6px 0;">
            <span style="font-size:12px;font-weight:700;color:{TEXT_SM};">{i}.</span>
          </td>
          <td style="padding:6px 0 6px 4px;">
            <span style="display:inline-block;font-size:10px;font-weight:700;
                         background:{bg};color:{color};padding:2px 8px;
                         border-radius:20px;margin-right:8px;text-transform:uppercase;
                         letter-spacing:0.5px;">{label}</span>
            <span style="font-size:13px;color:{TEXT_DK};font-weight:500;
                         line-height:1.4;">{_esc(reg.title[:90])}{'...' if len(reg.title) > 90 else ''}</span>
          </td>
        </tr>"""

    return f"""
  <mj-section padding="0 0 12px 0">
    <mj-column background-color="{WHITE}" padding="24px 32px">
      <mj-text>
        <p style="margin:0 0 14px 0;font-size:11px;font-weight:700;color:{TEXT_SM};
                  text-transform:uppercase;letter-spacing:1.2px;">In this issue</p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _section_header(severity: str) -> str:
    label, color, bg = SEVERITY_SECTION.get(severity, ("UPDATES", TEXT_SM, STRIPE))
    return f"""
  <mj-section padding="20px 0 0 0">
    <mj-column background-color="{bg}" padding="10px 32px">
      <mj-text>
        <span style="font-size:10px;font-weight:800;color:{color};
                     text-transform:uppercase;letter-spacing:1.8px;">{label}</span>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _card(reg) -> str:
    a     = reg.analysis
    color = SEVERITY_COLOR.get(a.severity, "#475569")
    bg    = SEVERITY_BG.get(a.severity, "#F1F5F9")
    label = SEVERITY_LABEL.get(a.severity, a.severity.upper())
    dtype = DOC_TYPE_LABEL.get(reg.document_type, reg.document_type)
    days  = _days_until(reg.effective_date)

    # deadline line
    if days is not None:
        if days == 0:
            deadline = f'<span style="color:#B91C1C;font-weight:700;">Effective TODAY</span>'
        elif days <= 14:
            deadline = (f'<span style="color:#B91C1C;font-weight:700;">'
                        f'Effective in {days} day{"s" if days != 1 else ""} &mdash; {reg.effective_date}</span>')
        elif days <= 30:
            deadline = (f'<span style="color:#B45309;font-weight:600;">'
                        f'Effective {reg.effective_date} ({days} days)</span>')
        else:
            deadline = f'<span style="color:{TEXT_SM};">Effective {reg.effective_date} &mdash; {days} days away</span>'
        deadline_row = f'<tr><td style="padding-top:2px;font-size:12px;">{deadline}</td></tr>'
    elif a.effective_date_note:
        deadline_row = (
            f'<tr><td style="padding-top:2px;font-size:12px;color:{TEXT_SM};">'
            f'{_esc(a.effective_date_note)}</td></tr>'
        )
    else:
        deadline_row = ""

    # meta chips
    meta = (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;'
        f'text-transform:uppercase;letter-spacing:0.6px;">{label}</span>'
        f'&nbsp;&nbsp;'
        f'<span style="font-size:11px;color:{TEXT_SM};">{_esc(reg.agency)}</span>'
        f'&nbsp;&middot;&nbsp;'
        f'<span style="font-size:11px;color:{TEXT_SM};">{dtype}</span>'
        f'&nbsp;&middot;&nbsp;'
        f'<span style="font-size:11px;color:{TEXT_SM};">{reg.published_date}</span>'
    )

    # "the bottom line" callout
    btl = (
        f'<tr><td style="padding-top:20px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="border-left:3px solid {BTL_LEFT};background:{BTL_BG};'
        f'padding:14px 18px;border-radius:0 6px 6px 0;">'
        f'<tr><td style="font-size:10px;font-weight:800;color:{BTL_TEXT};'
        f'text-transform:uppercase;letter-spacing:1.2px;padding-bottom:6px;">'
        f'&#9660;&nbsp; The Bottom Line</td></tr>'
        f'<tr><td style="font-size:14px;color:{BTL_TEXT};font-weight:500;line-height:1.6;">'
        f'{_esc(a.plain_english_summary)}</td></tr>'
        f'</table></td></tr>'
    )

    # action steps
    if a.action_items:
        steps = "".join(
            f'<tr>'
            f'<td width="32" valign="top" style="padding:5px 0;">'
            f'<span style="display:inline-block;width:20px;height:20px;line-height:20px;'
            f'text-align:center;background:{TEXT_DK};color:#fff;'
            f'font-size:10px;font-weight:700;border-radius:4px;">{i + 1}</span>'
            f'</td>'
            f'<td style="padding:5px 0 5px 8px;font-size:13px;color:{TEXT_DK};line-height:1.55;">'
            f'{_esc(item)}</td>'
            f'</tr>'
            for i, item in enumerate(a.action_items)
        )
        actions = (
            f'<tr><td style="padding-top:20px;">'
            f'<p style="margin:0 0 12px 0;font-size:10px;font-weight:800;color:{TEXT_SM};'
            f'text-transform:uppercase;letter-spacing:1.2px;">What to do</p>'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background:{STRIPE};border-radius:8px;padding:12px 16px;">{steps}</table>'
            f'</td></tr>'
        )
    else:
        actions = ""

    # penalty
    if a.penalty_exposure:
        penalty = (
            f'<tr><td style="padding-top:16px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background:#FFF1F2;border-radius:6px;padding:10px 14px;">'
            f'<tr><td style="font-size:10px;font-weight:800;color:#9F1239;'
            f'text-transform:uppercase;letter-spacing:1px;padding-bottom:4px;">'
            f'&#9888; Penalty Risk</td></tr>'
            f'<tr><td style="font-size:12px;color:#881337;line-height:1.6;">'
            f'{_esc(a.penalty_exposure)}</td></tr>'
            f'</table></td></tr>'
        )
    else:
        penalty = ""

    # CFR refs
    if a.relevant_cfr_sections:
        tags = " ".join(
            f'<code style="font-family:{MONO};font-size:11px;background:{STRIPE};'
            f'color:{TEXT_DK};padding:3px 8px;border-radius:4px;border:1px solid {BORDER};">'
            f'{_esc(s)}</code>'
            for s in a.relevant_cfr_sections
        )
        cfr = (
            f'<tr><td style="padding-top:16px;">'
            f'<span style="font-size:10px;font-weight:700;color:{TEXT_SM};'
            f'text-transform:uppercase;letter-spacing:1px;">CFR References&nbsp;&nbsp;</span>'
            f'{tags}</td></tr>'
        )
    else:
        cfr = ""

    # CTA button row
    btn_url = reg.html_url or "#"
    button = f"""
  <mj-section padding="0">
    <mj-column background-color="{WHITE}" padding="0 32px 28px 32px">
      <mj-button background-color="{BTN_BG}" color="{BTN_TEXT}"
                 font-size="12px" font-weight="700" letter-spacing="0.5px"
                 border-radius="6px" padding="12px 24px"
                 align="left" href="{btn_url}"
                 inner-padding="0">
        Read Full Rule on Federal Register &nbsp;&#8594;
      </mj-button>
    </mj-column>
  </mj-section>"""

    card_body = f"""
  <mj-section padding="0">
    <mj-column background-color="{WHITE}" border-left="3px solid {color}"
               padding="24px 32px 20px 28px">
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">

          <!-- meta row -->
          <tr><td style="padding-bottom:14px;">{meta}</td></tr>

          <!-- headline -->
          <tr><td style="padding-bottom:4px;border-bottom:2px solid {BORDER};">
            <span style="font-size:20px;font-weight:800;color:{TEXT_DK};
                         letter-spacing:-0.3px;line-height:1.3;">
              {_esc(reg.title)}
            </span>
          </td></tr>

          <!-- deadline -->
          {deadline_row}

          {btl}
          {actions}
          {penalty}
          {cfr}

        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""

    return card_body + (button if reg.html_url else "") + f"""
  <mj-section padding="0 0 2px 0">
    <mj-column background-color="{BG}" padding="6px 0" />
  </mj-section>"""


def _for_business_bar(business: str) -> str:
    return f"""
  <mj-section padding="0">
    <mj-column background-color="{MAST_BG}" padding="12px 32px">
      <mj-text font-size="12px" color="{MAST_META}">
        Personalized for <strong style="color:{MAST_TEXT};">{business}</strong>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _footer(customer) -> str:
    return f"""
  <mj-section padding="28px 0 40px 0">
    <mj-column>
      <mj-divider border-color="{DIVIDER}" border-width="1px" padding="0 0 24px 0" />
      <mj-text font-size="11px" color="{TEXT_XS}" align="center" line-height="2.1">
        You're subscribed to <strong style="color:{TEXT_SM};">ComplianceWatch</strong>
        &nbsp;&mdash;&nbsp; regulatory monitoring for small business.<br>
        <a href="https://compliancewatch.app/unsubscribe?email={customer.email}"
           style="color:{TEXT_SM};text-decoration:underline;">Unsubscribe</a>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="https://compliancewatch.app/settings"
           style="color:{TEXT_SM};text-decoration:underline;">Update Preferences</a>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="https://compliancewatch.app/dashboard"
           style="color:{TEXT_SM};text-decoration:underline;">Dashboard</a>
        <br><br>
        <span style="color:{TEXT_XS};">ComplianceWatch &nbsp;&middot;&nbsp; Austin, TX 78701</span>
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


# ── Cards grouped by severity tier ────────────────────────────────────────────

def _grouped_cards(regulations: list) -> str:
    order = ["critical", "high", "medium", "low", "informational"]
    by_sev: dict = {s: [] for s in order}
    for reg in regulations:
        s = reg.analysis.severity
        by_sev.setdefault(s, []).append(reg)

    out = ""
    for sev in order:
        regs = by_sev.get(sev, [])
        if not regs:
            continue
        out += _section_header(sev)
        for reg in regs:
            out += _card(reg)
    return out


# ── Public API ────────────────────────────────────────────────────────────────

def urgent_subject(reg) -> str:
    days = _days_until(reg.effective_date)
    if days is not None and days <= 30:
        return f"Action required: {reg.agency} rule takes effect in {days} days"
    return f"Compliance alert: {reg.title[:72]}"


def urgent_html(reg, customer) -> str:
    business = _esc(customer.business_name or customer.email)
    days     = _days_until(reg.effective_date)

    if days is not None and days <= 14:
        sub = f"{days} DAYS TO COMPLY"
    elif days is not None and days <= 30:
        sub = "ACTION REQUIRED"
    else:
        sub = "COMPLIANCE ALERT"

    return _compile(_wrap(
        _masthead("Compliance Alert", sub)
        + _for_business_bar(business)
        + _section_header(reg.analysis.severity)
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
    issue  = f"{n} UPDATE{'S' if n != 1 else ''} THIS WEEK"

    return _compile(_wrap(
        _masthead("Weekly Digest", issue)
        + _for_business_bar(business)
        + _toc(regulations)
        + _grouped_cards(regulations)
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
