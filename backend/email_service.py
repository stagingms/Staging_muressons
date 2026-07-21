"""
Muressons — Email Service
Sends transactional emails via SMTP. Degrades gracefully if SMTP is not
configured — emails are logged to stdout instead of raising exceptions.

Environment variables:
    SMTP_HOST       SMTP server hostname  (e.g. smtp.gmail.com)
    SMTP_PORT       SMTP server port      (default: 587)
    SMTP_USER       SMTP login username
    SMTP_PASSWORD   SMTP login password / app-password
    SMTP_FROM       Sender "From" address (defaults to SMTP_USER)
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor

_logger = logging.getLogger("muressons.email")

# ── SMTP configuration (read once at import time) ─────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "") or SMTP_USER

_smtp_configured: bool = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

# Background thread pool so SMTP I/O never blocks the async event loop
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="email")


def is_configured() -> bool:
    """Return True if SMTP credentials are present."""
    return _smtp_configured


def _send_sync(to: str, subject: str, html_body: str, text_body: str | None = None) -> None:
    """Blocking send — runs inside the thread pool."""
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject

    # Plain-text fallback
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    # HTML version (preferred by email clients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to], msg.as_string())
        _logger.info("Email sent to %s — subject: %s", to, subject)
    except Exception as exc:
        _logger.error("Failed to send email to %s: %s", to, exc)


def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> None:
    """Fire-and-forget email send (non-blocking).

    If SMTP is not configured the email content is logged at INFO level
    so that the admin can still see it in server logs.
    """
    if not to:
        _logger.warning("send_email called with empty recipient — skipping")
        return

    if not _smtp_configured:
        _logger.info(
            "[EMAIL-STUB] SMTP not configured. Would have sent:\n"
            "  To:      %s\n"
            "  Subject: %s\n"
            "  Body:    (HTML email, %d chars)",
            to, subject, len(html_body),
        )
        return

    _pool.submit(_send_sync, to, subject, html_body, text_body)


# ── Pre-built templates ──────────────────────────────────────────

def send_password_reset_email(
    to: str,
    facilitator_id: str,
    facilitator_name: str,
    new_password: str,
) -> None:
    """Send a password-reset notification to the facilitator."""
    subject = "🔐 Muressons — Your Password Has Been Reset"

    html_body = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#0f172a;color:#e2e8f0;">
  <div style="max-width:520px;margin:32px auto;background:#1e293b;border-radius:12px;border:1px solid rgba(99,102,241,0.25);overflow:hidden;">
    <!-- Header -->
    <div style="padding:24px 28px 16px;background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(6,182,212,0.10));border-bottom:1px solid rgba(99,102,241,0.15);">
      <div style="font-size:24px;margin-bottom:4px;">🔐</div>
      <h1 style="margin:0;font-size:18px;font-weight:700;color:#f1f5f9;">Password Reset</h1>
      <p style="margin:4px 0 0;font-size:13px;color:#94a3b8;">Your Muressons facilitator password has been reset by an administrator.</p>
    </div>
    <!-- Body -->
    <div style="padding:24px 28px;">
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
        <tr>
          <td style="padding:8px 0;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;width:120px;">Facilitator ID</td>
          <td style="padding:8px 0;font-size:14px;color:#f1f5f9;font-family:'Courier New',monospace;font-weight:600;">{facilitator_id}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Name</td>
          <td style="padding:8px 0;font-size:14px;color:#f1f5f9;">{facilitator_name}</td>
        </tr>
      </table>
      <div style="background:#0f172a;border:1px solid rgba(99,102,241,0.3);border-radius:8px;padding:16px 20px;text-align:center;margin-bottom:16px;">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#64748b;margin-bottom:8px;">New Password</div>
        <div style="font-size:22px;font-family:'Courier New',monospace;font-weight:700;color:#22c55e;letter-spacing:0.15em;">{new_password}</div>
      </div>
      <p style="font-size:12px;color:#94a3b8;line-height:1.6;margin:0;">
        Please sign in with this password and change it at your earliest convenience.
        If you did not expect this reset, contact your system administrator immediately.
      </p>
    </div>
    <!-- Footer -->
    <div style="padding:16px 28px;border-top:1px solid rgba(255,255,255,0.05);text-align:center;">
      <p style="margin:0;font-size:11px;color:#475569;">Muressons Global Corporation — Simulation Platform</p>
    </div>
  </div>
</body>
</html>"""

    text_body = (
        f"Muressons — Password Reset\n\n"
        f"Your facilitator password has been reset by an administrator.\n\n"
        f"Facilitator ID: {facilitator_id}\n"
        f"Name: {facilitator_name}\n"
        f"New Password: {new_password}\n\n"
        f"Please sign in and change it at your earliest convenience.\n"
        f"If you did not expect this reset, contact your administrator."
    )

    send_email(to, subject, html_body, text_body)
