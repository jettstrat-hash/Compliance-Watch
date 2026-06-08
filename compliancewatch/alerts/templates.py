"""
MJML-based email templates for ComplianceWatch.

Design language: dark branded header, severity chip badges, urgency countdown
banners, inset action blocks, monospace CFR pills — cross-client compatible
(Outlook, Gmail, Apple Mail, mobile).

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
    "informational": "#64748B",
}

# Lighter tint of each severity color used for chip backgrounds
SEVERITY_BG = {
    "critical":      "#FEF2F2",
    "high":          "#FFFBEB",
    "medium":        "#EFF6FF",
    "low":           "#F0FDF4",
    "informational": "#F8FAFC",
}

SEVERITY_LABEL = {
    "critical":      "Critical",
    "high":          "High Priority",
    "medium":        "Medium",
    "low":           "Low",
    "informational": "Informational",
}

SEVERITY_ACTION = {
    "critical":      "Immediate Action Required",
    "high":          "Action Within 30 Days",
    "medium":        "Action Within 90 Days",
    "low":           "For Your Awareness",
    "informational": "Proposed Rule — Comment Period Open",
}

DOC_TYPE_LABEL = {
    "RULE":    "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE":  "Notice",
}

DOC_TYPE_COLOR = {
    "RULE":    "#1D4ED8",
    "PRORULE": "#7C3AED",
    "NOTICE":  "#0369A1",
}

# ── Design tokens ─────────────────────────────────────────────────────────────

FONT  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica Neue, Arial, sans-serif"
MONO  = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace"

# Page
BG       = "#EAECF0"   # slightly warm gray page bg

# Header (dark branded bar)
HDR_BG   = "#0F172A"   # slate-900
HDR_TEXT = "#F8FAFC"   # near-white
HDR_SUB  = "#94A3B8"   # slate-400 muted label

# Cards
WHITE    = "#FFFFFF"
BORDER   = "#E2E8F0"
STRIPE   = "#F8FAFC"   # inset block bg

# Typography
TEXT     = "#374151"
TEXT_DK  = "#111827"
TEXT_SM  = "#6B7280"
TEXT_XS  = "#9CA3AF"

# Link
ACCENT   = "#1D4ED8"

# Urgency banner
URGENCY_BG     = "#FFF7ED"
URGENCY_BORDER = "#FDBA74"
URGENCY_TEXT   = "#9A3412"


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


def _header(label: str, sub: str = "") -> str:
    sub_row = (
        f'<tr><td style="padding-top:4px;font-size:12px;color:{HDR_SUB};">{sub}</td></tr>'
        if sub else ""
    )
    return f"""
  <mj-section background-color="{HDR_BG}" padding="28px 0 24px 0">
    <mj-column>
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td>
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="width:6px;background:{ACCENT};border-radius:2px;">&nbsp;</td>
                  <td style="padding-left:12px;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr><td style="font-size:20px;font-weight:800;color:{HDR_TEXT};
                               letter-spacing:-0.5px;line-height:1;">ComplianceWatch</td></tr>
                      {sub_row}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
            <td align="right" valign="middle">
              <span style="display:inline-block;background:rgba(255,255,255,0.1);
                           color:{HDR_TEXT};font-size:11px;font-weight:600;
                           text-transform:uppercase;letter-spacing:1px;
                           padding:5px 12px;border-radius:20px;border:1px solid rgba(255,255,255,0.15);">
                {label}
              </span>
            </td>
          </tr>
        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _intro(business: str, headline: str, body: str) -> str:
    return f"""
  <mj-section padding="16px 0 0 0">
    <mj-column background-color="{WHITE}" padding="28px 32px 24px 32px"
               border-bottom="3px solid {ACCENT}">
      <mj-text font-size="11px" font-weight="600" color="{TEXT_SM}" padding="0 0 8px 0"
               letter-spacing="0.5px" text-transform="uppercase">For {business}</mj-text>
      <mj-text font-size="22px" font-weight="800" color="{TEXT_DK}" line-height="1.3"
               padding="0 0 14px 0" letter-spacing="-0.3px">{headline}</mj-text>
      <mj-text font-size="15px" color="{TEXT}" line-height="1.7" padding="0">
        {body}
      </mj-text>
    </mj-column>
  </mj-section>"""


def _severity_chip(severity: str) -> str:
    color  = SEVERITY_COLOR.get(severity, "#64748B")
    bg     = SEVERITY_BG.get(severity, "#F8FAFC")
    label  = SEVERITY_LABEL.get(severity, severity.upper())
    action = SEVERITY_ACTION.get(severity, "")
    return (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;'
        f'padding:4px 10px;border-radius:20px;border:1px solid {color};">'
        f'{label}</span>'
        f'&nbsp;&nbsp;'
        f'<span style="font-size:12px;color:{TEXT_SM};font-weight:500;">{action}</span>'
    )


def _doc_chip(doc_type: str) -> str:
    label = DOC_TYPE_LABEL.get(doc_type, doc_type)
    color = DOC_TYPE_COLOR.get(doc_type, ACCENT)
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.6px;color:{color};">{label}</span>'
    )


def _urgency_banner(days: int, effective_date) -> str:
    if days == 0:
        msg = "This rule is <strong>effective today.</strong> Ensure compliance immediately."
    elif days == 1:
        msg = "This rule takes effect <strong>tomorrow.</strong> Final preparations required now."
    else:
        msg = (f"This rule takes effect in <strong>{days} days</strong> "
               f"({effective_date}). Review your compliance status now.")
    return f"""<tr><td style="padding-top:20px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{URGENCY_BG};border:1px solid {URGENCY_BORDER};
                    border-radius:6px;padding:14px 18px;">
        <tr>
          <td style="font-size:13px;color:{URGENCY_TEXT};line-height:1.6;">
            <span style="font-size:15px;margin-right:8px;">&#9888;</span>
            {msg}
          </td>
        </tr>
      </table>
    </td></tr>"""


def _card(reg) -> str:
    a     = reg.analysis
    color = SEVERITY_COLOR.get(a.severity, "#64748B")
    days  = _days_until(reg.effective_date)

    # urgency banner for imminent deadlines
    if days is not None and days <= 30:
        urgency_row = _urgency_banner(days, reg.effective_date)
    elif a.effective_date_note:
        urgency_row = (
            f'<tr><td style="padding-top:16px;font-size:13px;color:{TEXT_SM};">'
            f'{_esc(a.effective_date_note)}</td></tr>'
        )
    else:
        urgency_row = ""

    # effective date when > 30 days
    if days is not None and days > 30:
        eff_row = (
            f'<tr><td style="padding-top:14px;font-size:13px;color:{TEXT_SM};">'
            f'Effective {reg.effective_date} &mdash; {days} days from now</td></tr>'
        )
    else:
        eff_row = ""

    # numbered action items
    if a.action_items:
        rows = "".join(
            f'<tr>'
            f'<td width="28" valign="top" style="padding:7px 0;">'
            f'<span style="display:inline-block;width:22px;height:22px;line-height:22px;'
            f'text-align:center;background:{color};color:#fff;font-size:11px;font-weight:700;'
            f'border-radius:50%;">{i + 1}</span></td>'
            f'<td style="padding:7px 0 7px 8px;font-size:14px;color:{TEXT_DK};line-height:1.55;">'
            f'{_esc(item)}</td>'
            f'</tr>'
            for i, item in enumerate(a.action_items)
        )
        actions = f"""<tr><td style="padding-top:22px;">
          <p style="margin:0 0 12px 0;font-size:11px;font-weight:700;color:{TEXT_SM};
              text-transform:uppercase;letter-spacing:1px;">&#10003;&nbsp; What To Do</p>
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background:{STRIPE};padding:12px 16px;border-radius:6px;
                        border-left:3px solid {color};">{rows}</table>
        </td></tr>"""
    else:
        actions = ""

    # penalty
    penalty = (
        f'<tr><td style="padding-top:20px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="background:#FFF1F2;border-radius:6px;padding:12px 16px;">'
        f'<tr><td style="font-size:11px;font-weight:700;color:#9F1239;'
        f'text-transform:uppercase;letter-spacing:0.8px;padding-bottom:6px;">'
        f'&#9888; Penalty Risk</td></tr>'
        f'<tr><td style="font-size:13px;color:#881337;line-height:1.6;">'
        f'{_esc(a.penalty_exposure)}</td></tr>'
        f'</table></td></tr>'
        if a.penalty_exposure else ""
    )

    # monospace CFR citations
    if a.relevant_cfr_sections:
        codes = " ".join(
            f'<code style="font-family:{MONO};font-size:11px;background:{STRIPE};'
            f'color:{TEXT_DK};padding:3px 8px;border-radius:4px;'
            f'border:1px solid {BORDER};display:inline-block;margin:2px 4px 2px 0;">'
            f'{_esc(s)}</code>'
            for s in a.relevant_cfr_sections
        )
        cfr = (
            f'<tr><td style="padding-top:18px;">'
            f'<p style="margin:0 0 8px 0;font-size:11px;font-weight:700;color:{TEXT_SM};'
            f'text-transform:uppercase;letter-spacing:0.8px;">CFR References</p>'
            f'<div style="line-height:2.0;">{codes}</div></td></tr>'
        )
    else:
        cfr = ""

    source = (
        f'<tr><td style="padding-top:20px;border-top:1px solid {BORDER};">'
        f'<a href="{reg.html_url}" '
        f'style="font-size:13px;color:{ACCENT};font-weight:600;text-decoration:none;">'
        f'Read the full rule on Federal Register &nbsp;&rarr;</a></td></tr>'
        if reg.html_url else ""
    )

    return f"""
  <mj-section padding="12px 0 0 0">
    <mj-column border-left="4px solid {color}" background-color="{WHITE}"
               padding="22px 28px 24px 28px">
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">

          <!-- severity chip + doc type row -->
          <tr><td style="padding-bottom:16px;">
            {_severity_chip(a.severity)}<br>
            <span style="margin-top:8px;display:inline-block;">
              {_doc_chip(reg.document_type)}
              <span style="margin:0 6px;color:{BORDER};">&middot;</span>
              <span style="font-size:11px;color:{TEXT_XS};">{_esc(reg.agency)}</span>
              <span style="margin:0 6px;color:{BORDER};">&middot;</span>
              <span style="font-size:11px;color:{TEXT_XS};">{reg.published_date}</span>
            </span>
          </td></tr>

          <!-- title -->
          <tr><td style="padding-bottom:16px;border-bottom:1px solid {BORDER};">
            <span style="font-size:18px;font-weight:800;color:{TEXT_DK};line-height:1.3;
                         letter-spacing:-0.2px;">
              {_esc(reg.title)}
            </span>
          </td></tr>

          <!-- summary -->
          <tr><td style="padding-top:16px;font-size:15px;color:{TEXT};line-height:1.7;">
            {_esc(a.plain_english_summary)}
          </td></tr>

          {urgency_row}
          {eff_row}
          {actions}
          {penalty}
          {cfr}
          {source}

        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _digest_summary_bar(regulations: list) -> str:
    by_sev = {}
    for r in regulations:
        s = r.analysis.severity
        by_sev[s] = by_sev.get(s, 0) + 1

    order = ["critical", "high", "medium", "low", "informational"]
    cells = []
    for sev in order:
        n = by_sev.get(sev, 0)
        if not n:
            continue
        color = SEVERITY_COLOR[sev]
        bg    = SEVERITY_BG[sev]
        label = SEVERITY_LABEL[sev]
        cells.append(
            f'<td style="padding:0 8px 0 0;">'
            f'<span style="display:inline-block;background:{bg};color:{color};'
            f'font-size:12px;font-weight:700;padding:6px 14px;border-radius:20px;'
            f'border:1px solid {color};">{n} {label}</span>'
            f'</td>'
        )

    if not cells:
        return ""

    return f"""
  <mj-section padding="0 0 0 0">
    <mj-column background-color="{WHITE}" padding="16px 32px">
      <mj-text>
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>{"".join(cells)}</tr>
        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _footer(customer) -> str:
    return f"""
  <mj-section padding="24px 0 40px 0" background-color="{BG}">
    <mj-column>
      <mj-text font-size="11px" color="{TEXT_XS}" align="center" line-height="2.0">
        You're receiving this because you subscribed to <strong>ComplianceWatch</strong>.<br>
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


# ── Public API ────────────────────────────────────────────────────────────────

def urgent_subject(reg) -> str:
    days = _days_until(reg.effective_date)
    if days is not None and days <= 30:
        return f"Action required: {reg.agency} rule takes effect in {days} days"
    return f"Compliance alert: {reg.title[:72]}"


def urgent_html(reg, customer) -> str:
    a        = reg.analysis
    business = _esc(customer.business_name or customer.email)
    days     = _days_until(reg.effective_date)

    if days is not None and days <= 30:
        intro_headline = f"A rule affecting your business takes effect in {days} days"
    elif a.severity == "critical":
        intro_headline = "A critical federal regulation requires your immediate attention"
    else:
        intro_headline = "A federal regulation affecting your business requires attention"

    return _compile(_wrap(
        _header("Compliance Alert", sub="Regulatory update for your business")
        + _intro(
            business,
            intro_headline,
            "We monitor federal agencies so you don't have to. "
            "Review the details and recommended actions below.",
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
        _header("Weekly Digest", sub=f"Week of {date.today().strftime('%B %d, %Y')}")
        + _intro(business, "Your weekly compliance briefing", body)
        + _digest_summary_bar(regulations)
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
