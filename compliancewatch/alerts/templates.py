"""
MJML-based email templates for ComplianceWatch.

Aesthetic direction: "Federal Gazette" — editorial authority, warm palette.
Georgia serif headlines on cream, amber accent, newspaper article card format.
Feels like a curated publication, not a SaaS dashboard alert.

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
    "informational": "#4B5563",
}

SEVERITY_LABEL = {
    "critical":      "Critical",
    "high":          "High Priority",
    "medium":        "Medium",
    "low":           "Low",
    "informational": "Informational",
}

SEVERITY_ACTION = {
    "critical":      "Immediate action required",
    "high":          "Action within 30 days",
    "medium":        "Action within 90 days",
    "low":           "For your awareness",
    "informational": "Proposed rule — comment period open",
}

SEVERITY_SECTION_LABEL = {
    "critical":      "Urgent — Act Now",
    "high":          "Action Required This Month",
    "medium":        "Upcoming Requirements",
    "low":           "For Your Awareness",
    "informational": "On the Horizon",
}

DOC_TYPE_LABEL = {
    "RULE":    "Final Rule",
    "PRORULE": "Proposed Rule",
    "NOTICE":  "Notice",
}

# ── Design tokens ─────────────────────────────────────────────────────────────

SERIF = "Georgia, 'Times New Roman', Times, serif"
SANS  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica Neue, Arial, sans-serif"
MONO  = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace"

# Page
BG         = "#F7F3ED"   # warm cream

# Masthead
MAST_BG    = "#16100A"   # very dark warm black
MAST_TEXT  = "#FAF5EE"   # warm off-white
MAST_DIM   = "#A89880"   # muted amber-gray for secondary text
AMBER      = "#D97706"   # primary accent — used exclusively

# Cards
WHITE      = "#FFFFFF"
CARD_BDR   = "#E5DDD3"   # warm border
RULE       = "#DDD6CC"   # section rules

# Typography
INK        = "#1C1917"   # near-black, warm tint
INK_MID    = "#44403C"   # stone-700
INK_DIM    = "#78716C"   # stone-500
INK_XS     = "#A8A29E"   # stone-400

# Action block
ACT_BG     = "#FAFAF8"
ACT_NUM    = "#1C1917"

# Penalty
PENAL_BG   = "#FEF2F2"
PENAL_BDR  = "#FECACA"
PENAL_TXT  = "#7F1D1D"

# Deadline urgency
URG_BG     = "#FFFBEB"
URG_BDR    = "#FCD34D"
URG_TXT    = "#78350F"


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


# ── Building blocks ───────────────────────────────────────────────────────────

def _head() -> str:
    return f"""  <mj-head>
    <mj-attributes>
      <mj-all font-family="{SANS}" />
      <mj-text font-size="15px" line-height="1.7" color="{INK}" padding="0" />
      <mj-section background-color="{BG}" padding="0" />
      <mj-column padding="0" />
    </mj-attributes>
    <mj-style>
      a {{ color: {AMBER}; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </mj-style>
  </mj-head>"""


def _masthead(label: str, descriptor: str) -> str:
    today = date.today().strftime("%B {d}, %Y".replace("{d}", str(date.today().day))).upper()
    return f"""
  <!-- top amber rule -->
  <mj-section background-color="{AMBER}" padding="5px 0" />

  <!-- masthead: single column, stacked — safe on all mobile widths -->
  <mj-section background-color="{MAST_BG}" padding="26px 0 8px 0">
    <mj-column>
      <!-- wordmark -->
      <mj-text font-family="{SERIF}" font-size="28px" font-weight="700"
               color="{MAST_TEXT}" letter-spacing="-0.5px" line-height="1"
               padding="0 0 8px 0">
        ComplianceWatch
      </mj-text>
      <!-- label + date on one line, small -->
      <mj-text font-family="{SANS}" font-size="10px" color="{AMBER}"
               text-transform="uppercase" letter-spacing="2px" font-weight="600"
               padding="0 0 3px 0">
        {label}
        <span style="color:{MAST_DIM};margin:0 7px;">&middot;</span>
        <span style="color:{MAST_DIM};">{today}</span>
        <span style="color:{MAST_DIM};margin:0 7px;">&middot;</span>
        <span style="color:{MAST_DIM};">{descriptor}</span>
      </mj-text>
    </mj-column>
  </mj-section>

  <!-- rule below masthead -->
  <mj-section background-color="{MAST_BG}" padding="0">
    <mj-column>
      <mj-divider border-color="rgba(255,255,255,0.07)" border-width="1px" padding="0" />
    </mj-column>
  </mj-section>

  <!-- byline bar -->
  <mj-section background-color="{MAST_BG}" padding="10px 0 16px 0">
    <mj-column>
      <mj-text font-family="{SANS}" font-size="11px" color="{MAST_DIM}"
               font-style="italic" padding="0">
        Federal regulatory intelligence — curated for small business owners
      </mj-text>
    </mj-column>
  </mj-section>"""


def _for_bar(business: str) -> str:
    return f"""
  <mj-section background-color="#0D0907" padding="10px 0">
    <mj-column>
      <mj-text font-size="11px" color="{MAST_DIM}" padding="0">
        Personalized for&nbsp;
        <span style="color:{MAST_TEXT};font-weight:600;">{business}</span>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _section_divider(severity: str) -> str:
    label = SEVERITY_SECTION_LABEL.get(severity, "Updates")
    color = SEVERITY_COLOR.get(severity, INK_DIM)
    return f"""
  <mj-section padding="24px 0 0 0">
    <mj-column>
      <mj-text padding="0">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td width="24" style="border-top:2px solid {color};vertical-align:middle;">&nbsp;</td>
            <td style="padding:0 12px;vertical-align:middle;white-space:nowrap;">
              <span style="font-family:{SANS};font-size:10px;font-weight:800;
                           color:{color};text-transform:uppercase;letter-spacing:2px;">
                {label}
              </span>
            </td>
            <td style="border-top:2px solid {color};vertical-align:middle;width:100%;">&nbsp;</td>
          </tr>
        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _toc(regulations: list) -> str:
    rows = ""
    for i, reg in enumerate(regulations, 1):
        color = SEVERITY_COLOR.get(reg.analysis.severity, INK_DIM)
        label = SEVERITY_LABEL.get(reg.analysis.severity, "")
        title = reg.title[:85] + ("…" if len(reg.title) > 85 else "")
        rows += f"""
          <tr>
            <td width="20" valign="top"
                style="padding:7px 0;font-family:{SANS};font-size:12px;
                       color:{INK_DIM};font-weight:600;">{i}.</td>
            <td style="padding:7px 0 7px 8px;border-bottom:1px solid {RULE};">
              <span style="font-family:{SANS};font-size:10px;font-weight:700;
                           color:{color};text-transform:uppercase;
                           letter-spacing:0.8px;">{label}&ensp;</span>
              <span style="font-family:{SERIF};font-size:14px;color:{INK};
                           line-height:1.4;">{_esc(title)}</span>
            </td>
          </tr>"""
    return f"""
  <mj-section padding="12px 0 0 0">
    <mj-column background-color="{WHITE}" padding="22px 28px 16px 28px"
               border-bottom="3px solid {AMBER}">
      <mj-text>
        <p style="margin:0 0 14px 0;font-family:{SANS};font-size:10px;font-weight:800;
                  color:{INK_DIM};text-transform:uppercase;letter-spacing:2px;">
          In This Issue
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _card(reg) -> str:
    a     = reg.analysis
    color = SEVERITY_COLOR.get(a.severity, INK_DIM)
    sev   = SEVERITY_LABEL.get(a.severity, a.severity)
    act   = SEVERITY_ACTION.get(a.severity, "")
    dtype = DOC_TYPE_LABEL.get(reg.document_type, reg.document_type)
    days  = _days_until(reg.effective_date)

    # ── deadline block ────────────────────────────────────────────────────────
    if days is not None:
        if days == 0:
            dl_color = "#B91C1C"
            dl_text  = "Effective <strong>today</strong> — compliance required immediately"
        elif days <= 14:
            dl_color = "#B91C1C"
            dl_text  = (f"Effective in <strong>{days} day{'s' if days != 1 else ''}</strong>"
                        f" &mdash; {reg.effective_date}")
        elif days <= 30:
            dl_color = "#B45309"
            dl_text  = (f"Effective <strong>{reg.effective_date}</strong>"
                        f" &mdash; {days} days from today")
        else:
            dl_color = INK_DIM
            dl_text  = (f"Effective <strong>{reg.effective_date}</strong>"
                        f" &mdash; {days} days away")

        deadline_row = f"""<tr><td style="padding-top:14px;padding-bottom:2px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background:{URG_BG};border:1px solid {URG_BDR};
                        border-radius:4px;padding:10px 14px;">
            <tr><td style="font-family:{SANS};font-size:13px;color:{dl_color};line-height:1.5;">
              &#128197;&ensp;{dl_text}
            </td></tr>
          </table>
        </td></tr>"""
    elif a.effective_date_note:
        deadline_row = (
            f'<tr><td style="padding-top:12px;font-family:{SANS};'
            f'font-size:12px;color:{INK_DIM};font-style:italic;">'
            f'{_esc(a.effective_date_note)}</td></tr>'
        )
    else:
        deadline_row = ""

    # ── action steps ──────────────────────────────────────────────────────────
    if a.action_items:
        steps = "".join(
            f'<tr>'
            f'<td width="28" valign="top" style="padding:6px 0;">'
            f'<span style="font-family:{SANS};font-size:11px;font-weight:800;'
            f'color:{ACT_NUM};display:inline-block;width:20px;text-align:right;">'
            f'{i + 1}.</span></td>'
            f'<td style="padding:6px 0 6px 10px;font-family:{SANS};'
            f'font-size:13px;color:{INK};line-height:1.6;">{_esc(item)}</td>'
            f'</tr>'
            for i, item in enumerate(a.action_items)
        )
        actions = (
            f'<tr><td style="padding-top:22px;">'
            f'<p style="margin:0 0 10px 0;font-family:{SANS};font-size:10px;'
            f'font-weight:800;color:{INK_DIM};text-transform:uppercase;'
            f'letter-spacing:2px;">What To Do</p>'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background:{ACT_BG};border-radius:4px;'
            f'border-left:3px solid {color};padding:10px 14px;">{steps}</table>'
            f'</td></tr>'
        )
    else:
        actions = ""

    # ── penalty ───────────────────────────────────────────────────────────────
    if a.penalty_exposure:
        penalty = (
            f'<tr><td style="padding-top:18px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background:{PENAL_BG};border:1px solid {PENAL_BDR};'
            f'border-radius:4px;padding:10px 14px;">'
            f'<tr><td style="font-family:{SANS};font-size:10px;font-weight:800;'
            f'color:{PENAL_TXT};text-transform:uppercase;letter-spacing:1.5px;'
            f'padding-bottom:5px;">Penalty Exposure</td></tr>'
            f'<tr><td style="font-family:{SANS};font-size:13px;color:{PENAL_TXT};'
            f'line-height:1.6;">{_esc(a.penalty_exposure)}</td></tr>'
            f'</table></td></tr>'
        )
    else:
        penalty = ""

    # ── CFR refs ──────────────────────────────────────────────────────────────
    if a.relevant_cfr_sections:
        tags = "&ensp;".join(
            f'<code style="font-family:{MONO};font-size:11px;'
            f'background:#F5F3EF;color:{INK};padding:3px 7px;'
            f'border-radius:3px;border:1px solid {CARD_BDR};">'
            f'{_esc(s)}</code>'
            for s in a.relevant_cfr_sections
        )
        cfr = (
            f'<tr><td style="padding-top:18px;">'
            f'<span style="font-family:{SANS};font-size:10px;font-weight:700;'
            f'color:{INK_DIM};text-transform:uppercase;letter-spacing:1.5px;">'
            f'CFR&ensp;</span>{tags}</td></tr>'
        )
    else:
        cfr = ""

    # ── source link ───────────────────────────────────────────────────────────
    source = (
        f'<tr><td style="padding-top:20px;border-top:1px solid {RULE};">'
        f'<a href="{reg.html_url}" '
        f'style="font-family:{SANS};font-size:12px;font-weight:700;'
        f'color:{AMBER};text-decoration:none;letter-spacing:0.3px;">'
        f'Read the full rule &rarr;</a>'
        f'<span style="font-family:{SANS};font-size:11px;color:{INK_XS};'
        f'margin-left:10px;">Federal Register</span>'
        f'</td></tr>'
        if reg.html_url else ""
    )

    return f"""
  <mj-section padding="12px 0 0 0">
    <mj-column background-color="{WHITE}" border-left="4px solid {color}"
               padding="24px 28px 24px 24px">
      <mj-text>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">

          <!-- meta line -->
          <tr><td style="padding-bottom:12px;">
            <span style="font-family:{SANS};font-size:10px;font-weight:700;
                         color:{color};text-transform:uppercase;letter-spacing:1.5px;">
              {sev}</span>
            <span style="font-family:{SANS};font-size:10px;color:{INK_DIM};
                         margin-left:8px;">{act}</span>
            <span style="font-family:{SANS};font-size:10px;color:{CARD_BDR};
                         margin:0 6px;">&middot;</span>
            <span style="font-family:{SANS};font-size:10px;color:{INK_DIM};">
              {_esc(reg.agency)}</span>
            <span style="font-family:{SANS};font-size:10px;color:{CARD_BDR};
                         margin:0 6px;">&middot;</span>
            <span style="font-family:{SANS};font-size:10px;color:{INK_DIM};">
              {dtype}</span>
            <span style="font-family:{SANS};font-size:10px;color:{CARD_BDR};
                         margin:0 6px;">&middot;</span>
            <span style="font-family:{SANS};font-size:10px;color:{INK_XS};">
              {reg.published_date}</span>
          </td></tr>

          <!-- headline in serif -->
          <tr><td style="padding-bottom:16px;border-bottom:1px solid {RULE};">
            <span style="font-family:{SERIF};font-size:22px;font-weight:700;
                         color:{INK};line-height:1.35;letter-spacing:-0.2px;">
              {_esc(reg.title)}
            </span>
          </td></tr>

          <!-- deadline -->
          {deadline_row}

          <!-- summary body -->
          <tr><td style="padding-top:16px;font-family:{SANS};font-size:15px;
                         color:{INK_MID};line-height:1.75;">
            {_esc(a.plain_english_summary)}
          </td></tr>

          {actions}
          {penalty}
          {cfr}
          {source}

        </table>
      </mj-text>
    </mj-column>
  </mj-section>"""


def _grouped_cards(regulations: list) -> str:
    order  = ["critical", "high", "medium", "low", "informational"]
    by_sev: dict = {s: [] for s in order}
    for reg in regulations:
        by_sev.setdefault(reg.analysis.severity, []).append(reg)

    out = ""
    for sev in order:
        regs = by_sev.get(sev, [])
        if regs:
            out += _section_divider(sev)
            for reg in regs:
                out += _card(reg)
    return out


def _footer(customer) -> str:
    return f"""
  <mj-section padding="32px 0 20px 0">
    <mj-column>
      <mj-divider border-color="{RULE}" border-width="1px" padding="0 0 24px 0" />
    </mj-column>
  </mj-section>
  <mj-section padding="0 0 48px 0">
    <mj-column>
      <mj-text font-size="11px" color="{INK_XS}" align="center" line-height="2.2"
               font-family="{SANS}">
        You're subscribed to <strong style="color:{INK_DIM};">ComplianceWatch</strong>
        — federal regulatory monitoring for small businesses.<br>
        <a href="https://compliancewatch.app/unsubscribe?email={customer.email}"
           style="color:{INK_DIM};text-decoration:underline;">Unsubscribe</a>
        &ensp;&middot;&ensp;
        <a href="https://compliancewatch.app/settings"
           style="color:{INK_DIM};text-decoration:underline;">Preferences</a>
        &ensp;&middot;&ensp;
        <a href="https://compliancewatch.app/dashboard"
           style="color:{INK_DIM};text-decoration:underline;">Dashboard</a>
        <br><br>
        <span style="color:{INK_XS};">ComplianceWatch &middot; Austin, TX 78701</span>
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

    if days is not None and days <= 14:
        descriptor = f"{days} DAYS TO COMPLY"
    elif a.severity == "critical":
        descriptor = "IMMEDIATE ACTION REQUIRED"
    else:
        descriptor = "COMPLIANCE ALERT"

    return _compile(_wrap(
        _masthead("Compliance Alert", descriptor)
        + _for_bar(business)
        + _section_divider(a.severity)
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
    n        = len(regulations)
    issue    = f"{n} UPDATE{'S' if n != 1 else ''} THIS WEEK"

    return _compile(_wrap(
        _masthead("Weekly Digest", issue)
        + _for_bar(business)
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
