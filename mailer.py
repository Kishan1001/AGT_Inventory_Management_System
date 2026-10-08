# mailer.py
# ---------------------------------------------------------
#  EMAIL ALERT MODULE — Low Stock Notifications
#  Reads credentials from st.secrets["email"]
#  v3: adds Excel attachment of the low-stock list
# ---------------------------------------------------------
import io
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta, timezone

import streamlit as st

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist():
    return datetime.now(IST)


# =========================================================
#  LOAD CONFIG FROM STREAMLIT SECRETS (with detailed errors)
# =========================================================
def _get_cfg():
    """
    Returns ((host, port, user, pwd, recipients), None) on success.
    Returns (None, "reason") on failure.
    """
    try:
        cfg = st.secrets["email"]
    except FileNotFoundError:
        return None, "secrets.toml file not found. Create it at .streamlit/secrets.toml"
    except KeyError:
        return None, "No [email] section in secrets.toml."
    except Exception as e:
        return None, f"Cannot read secrets: {e}"

    try:
        host = cfg.get("smtp_host", "smtp.gmail.com")
        port = int(cfg.get("smtp_port", 587))
        user = cfg["smtp_user"]
        pwd  = cfg["smtp_pass"]
        recipients = list(cfg.get("recipients", []))
    except KeyError as e:
        return None, f"Missing key in [email] secrets: {e}"
    except Exception as e:
        return None, f"Bad secrets format: {e}"

    if not user:
        return None, "smtp_user is empty."
    if not pwd:
        return None, "smtp_pass is empty."
    if not recipients:
        return None, "recipients list is empty."

    return (host, port, user, pwd, recipients), None


def is_email_configured():
    cfg, _ = _get_cfg()
    return cfg is not None


# =========================================================
#  BUILD EXCEL ATTACHMENT
# =========================================================
def _build_attachment(alerts: list, trigger_reason: str):
    """
    Return (bytes, filename) for the low-stock Excel file.
    Falls back to (None, None) if pandas/openpyxl unavailable.
    """
    try:
        import pandas as pd
    except Exception:
        return None, None

    rows = []
    for a in alerts:
        rows.append({
            "Item Code":         a["code"],
            "Item Name":         a["name"],
            "Category":          a.get("category", "—"),
            "Subcategory":       a.get("subcategory", "—"),
            "Location":          a.get("location", "—"),
            "Current Qty":       a["qty"],
            "Minimum Required":  a["threshold"],
            "Shortfall":         a["shortfall"],
            "Status":            "OUT OF STOCK" if a["is_zero"] else "LOW STOCK",
        })

    df = pd.DataFrame(rows)

    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Low Stock")

            # ---- Auto-size columns for a polished look ----
            ws = writer.sheets["Low Stock"]
            for col_idx, col_name in enumerate(df.columns, start=1):
                max_len = max(
                    [len(str(col_name))] +
                    [len(str(v)) for v in df[col_name].tolist()]
                )
                ws.column_dimensions[
                    ws.cell(row=1, column=col_idx).column_letter
                ].width = min(max_len + 3, 45)
    except Exception:
        return None, None

    ts = now_ist().strftime("%d-%m-%Y_%H-%M")
    safe_trigger = "".join(
        ch if ch.isalnum() or ch in ("-", "_") else "_"
        for ch in trigger_reason.replace(" ", "_")
    )[:40]
    filename = f"agt_low_stock_{safe_trigger}_{ts}.xlsx"

    return buf.getvalue(), filename


# =========================================================
#  HTML EMAIL TEMPLATE
# =========================================================
def _build_email_html(alerts: list, trigger_reason: str,
                      attachment_name: str = None) -> str:
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    total = len(alerts)
    zero_count = sum(1 for a in alerts if a["is_zero"])

    rows_html = ""
    for a in alerts:
        qty_color = "#DC2626" if a["is_zero"] else "#D97706"
        status_txt = "🚫 OUT OF STOCK" if a["is_zero"] else "⚠️ LOW STOCK"
        status_bg = "#FEE2E2" if a["is_zero"] else "#FEF3C7"
        status_fg = "#991B1B" if a["is_zero"] else "#92400E"

        rows_html += f"""
        <tr>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       font-family:'Courier New',monospace; font-size:13px;
                       font-weight:600; color:#1F2A44;">{a['code']}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       font-size:13px; color:#1A2332;">{a['name']}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       font-size:12px; color:#6B7280;">{a.get('location') or '—'}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       text-align:right; font-family:'Courier New',monospace;
                       font-size:14px; font-weight:700; color:{qty_color};">{a['qty']}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       text-align:right; font-family:'Courier New',monospace;
                       font-size:13px; color:#6B7280;">{a['threshold']}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       text-align:right; font-family:'Courier New',monospace;
                       font-size:13px; font-weight:700; color:#B45309;">{a['shortfall']}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #E5E7EB;
                       text-align:center;">
                <span style="background:{status_bg}; color:{status_fg};
                             padding:3px 8px; border-radius:4px;
                             font-size:11px; font-weight:700;
                             letter-spacing:0.04em; white-space:nowrap;">
                    {status_txt}</span>
            </td>
        </tr>"""

    # ---- Attachment notice banner ----
    attachment_banner = ""
    if attachment_name:
        attachment_banner = f"""
        <div style="margin:0 32px; padding:14px 18px;
                    background:linear-gradient(135deg,#FAF6EC 0%,#F5EBD3 100%);
                    border:1.5px solid #C6A75E;
                    border-left:5px solid #A98A44;
                    border-radius:8px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:20px;">📎</span>
                <div>
                    <div style="font-size:13px; font-weight:700; color:#1F2A44;
                                letter-spacing:0.01em;">
                        Excel file attached
                    </div>
                    <div style="font-size:12px; color:#6B7280; margin-top:2px;">
                        Open
                        <strong style="color:#A98A44; font-family:'Courier New',monospace;">
                            {attachment_name}
                        </strong>
                        to view all <strong>{total}</strong> item(s) in a spreadsheet
                        with sortable columns.
                    </div>
                </div>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background:#F4F6FA;
             font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:900px; margin:24px auto; background:#FFFFFF;
              border-radius:12px; overflow:hidden;
              box-shadow:0 4px 20px rgba(31,42,68,0.12);">

    <div style="background:#1F2A44; padding:28px 32px;
                border-bottom:4px solid #C6A75E;">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:28px;">📦</span>
        <div>
          <h1 style="color:#FFFFFF; margin:0; font-size:20px;
                     font-weight:700; letter-spacing:-0.01em;">
            AGT Inventory — Low Stock Alert</h1>
          <p style="color:rgba(255,255,255,0.65); margin:4px 0 0 0;
                    font-size:13px;">
            DN-60 Valve Production Tracker · {timestamp}</p>
        </div>
      </div>
    </div>

    <div style="padding:24px 32px 8px 32px;">
      <div style="display:flex; gap:16px; flex-wrap:wrap;">
        <div style="flex:1; min-width:160px; background:#FEF3C7;
                    border-left:4px solid #D97706; border-radius:8px;
                    padding:16px 20px;">
          <div style="font-size:11px; font-weight:700; color:#92400E;
                      text-transform:uppercase; letter-spacing:0.08em;">
            Low Stock Items</div>
          <div style="font-size:28px; font-weight:800; color:#B45309;
                      margin-top:6px; line-height:1;">{total - zero_count}</div>
        </div>
        <div style="flex:1; min-width:160px; background:#FEE2E2;
                    border-left:4px solid #DC2626; border-radius:8px;
                    padding:16px 20px;">
          <div style="font-size:11px; font-weight:700; color:#991B1B;
                      text-transform:uppercase; letter-spacing:0.08em;">
            Out of Stock</div>
          <div style="font-size:28px; font-weight:800; color:#B91C1C;
                      margin-top:6px; line-height:1;">{zero_count}</div>
        </div>
        <div style="flex:1; min-width:160px; background:#EFF6FF;
                    border-left:4px solid #3B82F6; border-radius:8px;
                    padding:16px 20px;">
          <div style="font-size:11px; font-weight:700; color:#1E40AF;
                      text-transform:uppercase; letter-spacing:0.08em;">
            Trigger</div>
          <div style="font-size:15px; font-weight:700; color:#1D4ED8;
                      margin-top:10px; line-height:1.3;">{trigger_reason}</div>
        </div>
      </div>
    </div>

    {attachment_banner}

    <div style="padding:16px 32px 24px 32px; overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse;
                    border:1px solid #E5E7EB; border-radius:8px;
                    overflow:hidden;">
        <thead><tr style="background:#1F2A44;">
          <th style="padding:12px; text-align:left; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Code</th>
          <th style="padding:12px; text-align:left; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Item Name</th>
          <th style="padding:12px; text-align:left; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Location</th>
          <th style="padding:12px; text-align:right; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Qty</th>
          <th style="padding:12px; text-align:right; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Min</th>
          <th style="padding:12px; text-align:right; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Shortfall</th>
          <th style="padding:12px; text-align:center; color:#FFFFFF; font-size:11px;
                     font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase;">Status</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>

    <div style="background:#FAF6EC; padding:18px 32px;
                border-top:1px solid #E8DCC8;">
      <p style="margin:0; font-size:12px; color:#6B7280; line-height:1.6;">
        This is an automated alert from the
        <strong style="color:#1F2A44;">AGT Inventory Management System</strong>.
        Please review and replenish stock accordingly.</p>
      <p style="margin:8px 0 0 0; font-size:11px; color:#94A3B8;">
        © 2026 AASHDHA GLOBAL TECH · Built with ❤️ for Kishan</p>
    </div>
  </div>
</body></html>"""


# =========================================================
#  SEND EMAIL (with attachment)
# =========================================================
def send_low_stock_alert(alerts: list, trigger_reason: str = "Manual check"):
    """Returns (success: bool, message: str)."""
    cfg, err = _get_cfg()
    if cfg is None:
        return False, f"Email not configured — {err}"
    host, port, user, pwd, recipients = cfg

    if not alerts:
        return False, "No alerts to send."

    try:
        # ---- Build Excel attachment ----
        attach_bytes, attach_name = _build_attachment(alerts, trigger_reason)

        zero = sum(1 for a in alerts if a["is_zero"])
        if zero > 0:
            subject = (f"🚨 URGENT: {len(alerts)} Low Stock "
                       f"({zero} OUT OF STOCK) — AGT Inventory")
        else:
            subject = (f"⚠️ Low Stock Alert: {len(alerts)} items "
                       f"below minimum — AGT Inventory")

        # ---- Build message ----
        # Use "mixed" as the outer container so we can attach files.
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"AGT Inventory Alerts <{user}>"
        msg["To"] = ", ".join(recipients)

        # Inner alternative part: plain + HTML
        alt = MIMEMultipart("alternative")
        html_body = _build_email_html(alerts, trigger_reason, attach_name)

        # Plain-text fallback (for clients that don't render HTML)
        plain_lines = [
            f"AGT Inventory — Low Stock Alert",
            f"Trigger: {trigger_reason}",
            "",
            f"Total items below threshold: {len(alerts)}",
            f"Out of stock: {zero}",
            "",
            "Item Code | Item Name | Qty | Min | Shortfall",
            "-" * 70,
        ]
        for a in alerts:
            plain_lines.append(
                f"{a['code']} | {a['name'][:35]} | "
                f"{a['qty']} | {a['threshold']} | {a['shortfall']}"
            )
        if attach_name:
            plain_lines += ["", f"Full list attached as: {attach_name}"]

        alt.attach(MIMEText("\n".join(plain_lines), "plain", "utf-8"))
        alt.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt)

        # ---- Attach the Excel file ----
        if attach_bytes and attach_name:
            part = MIMEApplication(
                attach_bytes,
                _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=attach_name,
            )
            msg.attach(part)

        # ---- Send ----
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(user, pwd)
            server.sendmail(user, recipients, msg.as_string())

        suffix = f" (with Excel: {attach_name})" if attach_name else ""
        return True, f"Email sent to {len(recipients)} recipient(s){suffix}."

    except smtplib.SMTPAuthenticationError:
        return False, ("SMTP auth failed. Use a Gmail App Password "
                       "(16 chars, no spaces), not your regular password.")
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Email failed: {e}"


def test_smtp_connection():
    """Verify SMTP creds without sending an email."""
    cfg, err = _get_cfg()
    if cfg is None:
        return False, f"Email not configured — {err}"
    host, port, user, pwd, _ = cfg
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(user, pwd)
        return True, "SMTP connection OK."
    except Exception as e:
        return False, f"SMTP test failed: {e}"