# app.py
# ---------------------------------------------------------
#  STREAMLIT WEB UI — Enterprise Dashboard
#  Palette: #1F2A44 (Navy) · #E8DCC8 (Cream) · #C6A75E (Gold)
#  v39: manual adjustment auto-scroll fixed
#  Built with ❤️ for Kishan
# ---------------------------------------------------------
import io
import random
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import inventory_ops as ops
import mailer  # 📧 Email alert module
from inventory_ops import (
    DN60_PART_NUM,
    collection,
    download_excel_data,
    close_connection,
)

# =========================================================
#  🕐 TIMEZONE — India Standard Time (UTC + 5:30)
# =========================================================
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist():
    """Return current time in IST (Asia/Kolkata)."""
    return datetime.now(IST)


# =========================================================
#  📜 AUTO-SCROLL HELPERS
# =========================================================
def auto_scroll_to(element_id: str = None, delay: int = 250):
    """Smoothly scroll the parent Streamlit window to an element."""
    if element_id:
        js = f"""
        <script>
            setTimeout(function() {{
                try {{
                    var el = window.parent.document.getElementById("{element_id}");
                    if (!el) {{
                        el = window.parent.document.querySelector("{element_id}");
                    }}
                    if (el) {{
                        el.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'center'
                        }});
                    }}
                }} catch (e) {{
                    console.warn('auto_scroll_to failed:', e);
                }}
            }}, {delay});
        </script>
        """
    else:
        js = f"""
        <script>
            setTimeout(function() {{
                try {{
                    window.parent.scrollTo({{
                        top: window.parent.document.body.scrollHeight,
                        behavior: 'smooth'
                    }});
                }} catch (e) {{}}
            }}, {delay});
        </script>
        """
    components.html(js, height=0, width=0)


def scroll_to_top(delay: int = 200):
    """Scroll the parent window to the top of the page."""
    components.html(f"""
    <script>
        setTimeout(function() {{
            try {{
                window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
            }} catch (e) {{}}
        }}, {delay});
    </script>
    """, height=0, width=0)


# =========================================================
#  ⚠️ LOW STOCK THRESHOLDS
# =========================================================
DEFAULT_LOW_STOCK = 100

LOW_STOCK_OVERRIDES = {
    "94193159L": 2500,
    # Add more overrides anytime:
    # "94197705L": 500,
    # "94203335L": 200,
}


def low_stock_threshold(item_code: str) -> int:
    """Exact-match lookup of the low-stock threshold."""
    key = str(item_code).strip()
    return LOW_STOCK_OVERRIDES.get(key, DEFAULT_LOW_STOCK)


def is_low_stock(item_code: str, quantity) -> bool:
    """Check if an item is below its (custom or default) low-stock threshold."""
    try:
        qty = int(quantity)
    except Exception:
        return False
    return qty < low_stock_threshold(item_code)


# =========================================================
#  🎊 UPLOAD SUCCESS ANIMATION
# =========================================================
def show_upload_success_animated(inserted: int, duplicates: int, total: int):
    """Premium SVG checkmark draw + card rise animation."""
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    uid = int(datetime.now().timestamp() * 1000)

    st.markdown(f"""
    <style>
        @keyframes rise-{uid} {{
            0%   {{ opacity: 0; transform: translateY(20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes circle-draw-{uid} {{
            0%   {{ stroke-dashoffset: 350; }}
            100% {{ stroke-dashoffset: 0; }}
        }}
        @keyframes check-draw-{uid} {{
            0%   {{ stroke-dashoffset: 100; }}
            100% {{ stroke-dashoffset: 0; }}
        }}
        @keyframes glow-{uid} {{
            0%, 100% {{ box-shadow: 0 4px 20px -8px rgba(198,167,94,0.3); }}
            50%      {{ box-shadow: 0 4px 30px -4px rgba(198,167,94,0.7); }}
        }}
    </style>
    <div style="
        background: linear-gradient(135deg, #FFFFFF 0%, #FAF6EC 100%);
        border: 1.5px solid #E8DCC8;
        border-left: 5px solid #C6A75E;
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin: 1rem 0 1.5rem 0;
        font-family: 'Inter', sans-serif;
        animation: rise-{uid} 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),
                   glow-{uid} 2.5s ease-in-out 0.6s;
    ">
        <div style="display:flex; align-items:center; gap:16px; margin-bottom:1.2rem;">
            <svg width="48" height="48" viewBox="0 0 48 48" style="flex-shrink:0;">
                <circle cx="24" cy="24" r="22" fill="none"
                        stroke="#C6A75E" stroke-width="2.5"
                        stroke-dasharray="350"
                        style="animation: circle-draw-{uid} 0.8s ease-out forwards;"/>
                <path d="M14 24 L21 31 L34 18" fill="none"
                      stroke="#C6A75E" stroke-width="3.5"
                      stroke-linecap="round" stroke-linejoin="round"
                      stroke-dasharray="100"
                      style="stroke-dashoffset:100;
                             animation: check-draw-{uid} 0.5s ease-out 0.6s forwards;"/>
            </svg>
            <div>
                <div style="font-size:1.15rem; font-weight:700; color:#1F2A44;
                            letter-spacing:-0.01em; line-height:1.3;">
                    Upload Complete</div>
                <div style="font-size:0.82rem; color:#6B7280; margin-top:2px;">
                    Inventory synchronized · {timestamp}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px;
                    padding-top:1rem; border-top:1px solid #E8DCC8;">
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">
                    Inserted</div>
                <div style="font-size:1.5rem; font-weight:800; color:#1F2A44;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{inserted:,}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">
                    Skipped</div>
                <div style="font-size:1.5rem; font-weight:800;
                            color:{'#B45309' if duplicates > 0 else '#1F2A44'};
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{duplicates:,}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">
                    Total</div>
                <div style="font-size:1.5rem; font-weight:800; color:#A98A44;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{total:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  📧 EMAIL ALERT HELPERS
# =========================================================
def _record_email_attempt(trigger: str, ok: bool, msg: str):
    """Save the result of an email attempt (kept for internal use)."""
    log = st.session_state.setdefault("email_alert_log", [])
    log.insert(0, {
        "when": now_ist().strftime("%d-%m-%Y %H:%M:%S"),
        "trigger": trigger,
        "ok": ok,
        "msg": msg,
    })
    st.session_state["email_alert_log"] = log[:20]


def collect_low_stock_alerts():
    """Return a list of dicts for every item below its threshold."""
    alerts = []
    try:
        cursor = collection.find(
            {},
            {
                "_id": 0,
                "Item_code": 1,
                "Item_name": 1,
                "Item_category": 1,
                "Item_subcategory": 1,
                "Location": 1,
                "Quantity": 1,
            },
        )
        for doc in cursor:
            code = str(doc.get("Item_code", "")).strip()
            qty = int(doc.get("Quantity", 0) or 0)
            if not is_low_stock(code, qty):
                continue
            threshold = low_stock_threshold(code)
            alerts.append({
                "code": code,
                "name": str(doc.get("Item_name", "—")).strip() or "—",
                "category": str(doc.get("Item_category", "—")),
                "subcategory": str(doc.get("Item_subcategory", "—")),
                "location": str(doc.get("Location", "—")),
                "qty": qty,
                "threshold": threshold,
                "shortfall": max(0, threshold - qty),
                "is_zero": qty == 0,
            })
    except Exception:
        pass

    alerts.sort(key=lambda a: (not a["is_zero"], -a["shortfall"]))
    return alerts


def maybe_send_low_stock_alert(trigger_reason: str, force: bool = False):
    """Check thresholds and send email alert if needed."""
    alerts = collect_low_stock_alerts()
    if not alerts:
        _record_email_attempt(trigger_reason, False, "No low-stock items found.")
        return False, "No low-stock items found."

    if not force:
        last_sent = st.session_state.get("last_alert_sent_at")
        if last_sent:
            try:
                last_dt = datetime.strptime(last_sent, "%d-%m-%Y %H:%M:%S")
                elapsed = (now_ist().replace(tzinfo=None) - last_dt).total_seconds()
                if elapsed < 600:
                    msg = "Alert cooldown active (10 min)."
                    _record_email_attempt(trigger_reason, False, msg)
                    return False, msg
            except Exception:
                pass

    ok, msg = mailer.send_low_stock_alert(alerts, trigger_reason)
    _record_email_attempt(trigger_reason, ok, msg)

    if ok:
        st.session_state["last_alert_sent_at"] = now_ist().strftime("%d-%m-%Y %H:%M:%S")
        st.session_state["last_alert_count"] = len(alerts)
    return ok, msg


# =========================================================
#  📜 HISTORY COLLECTION — for Audit Log
# =========================================================
HISTORY_COLLECTION_NAME = "inventory_history"

try:
    history_collection = collection.database[HISTORY_COLLECTION_NAME]
except Exception:
    history_collection = None


def log_history(item_code, item_name, old_qty, new_qty, reason):
    """Append a stock-change record to the history collection."""
    if history_collection is None:
        return
    try:
        history_collection.insert_one({
            "Item_code": str(item_code).strip(),
            "Item_name": str(item_name).strip().upper(),
            "Old_Qty": int(old_qty),
            "New_Qty": int(new_qty),
            "Change": int(new_qty) - int(old_qty),
            "Reason": str(reason),
            "Timestamp": now_ist().strftime("%d-%m-%Y %H:%M:%S"),
        })
    except Exception:
        pass


# =========================================================
#  😄 FUN ZONE — Kishan Edition
# =========================================================
FUN_MODE = False

WRONG_PASSWORD_LINES = [
    "🚨 Nice try, hacker! But this isn't your inventory, mate.",
    "🔐 That password is so wrong it hurt my feelings, Kishan.",
    "🕵️ Breaking in? Bold move. Try again when you're older.",
    "🧠 Tip: the password isn't 'password123'. Just a hunch.",
    "🎭 Access denied. The fridge is that way, chief.",
    "🛑 Wrong password. This incident has been reported to... your Boss.",
]

NO_FILE_LINES = [
    "📁 Upload something, boss! Excel files don't summon themselves.",
    "🕳️ An empty file? That's not inventory, that's a vibe.",
    "📭 Nothing here but hopes and dreams, Kishan. Drop a file.",
]

ZERO_STOCK_LINES = [
    "😬 We're out of this one. The warehouse is on a diet.",
    "🫥 Stock: 0. Somewhere, a warehouse keeper is crying.",
    "🚫 Can't build with nothing. Physics says no.",
]


def big_order_message(count: int):
    if count >= 5000:
        return f"🚀 {count} valves?! Kishan, are we going to war or to market?"
    if count >= 1000:
        return f"💪 {count} valves — ambitious! Hope the supplier likes you."
    if count >= 500:
        return f"📈 {count} valves. That's a serious batch, boss."
    return None


def late_night_message():
    hour = now_ist().hour
    if 0 <= hour < 5:
        return "🦉 It's past midnight, Kishan. Go to sleep — the valves will still be here tomorrow."
    if 22 <= hour <= 23:
        return "🌙 Late shift, Kishan? Respect. Coffee's on the house."
    return None


def funny(pool):
    """Return a random funny line from the pool (or the first, if FUN_MODE is off)."""
    return random.choice(pool) if FUN_MODE else pool[0]


# =========================================================
#  PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AGT Inventory Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
#  CUSTOM CSS — Professional Enterprise Theme
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --navy:     #1F2A44;
        --navy-700: #2A3856;
        --navy-50:  #F4F6FA;
        --cream:    #E8DCC8;
        --cream-50: #FAF6EC;
        --gold:     #C6A75E;
        --gold-700: #A98A44;
        --ink:      #1A2332;
        --muted:    #6B7280;
        --border:   #E5E7EB;
        --white:    #FFFFFF;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-feature-settings: "cv02","cv03","cv04","cv11";
        -webkit-font-smoothing: antialiased;
        color: var(--ink);
        font-size: 15px;
    }

    .stApp { background: #FAFAF7; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: auto !important;
        min-height: 0 !important;
        visibility: visible !important;
        pointer-events: none !important;
        z-index: 999999 !important;
    }

    header[data-testid="stHeader"] [data-testid="stMainMenu"],
    header[data-testid="stHeader"] button[kind="header"],
    header[data-testid="stHeader"] button[data-testid="baseButton-header"] {
        position: fixed !important;
        top: 12px !important;
        right: 12px !important;
        left: auto !important;
        z-index: 999998 !important;
        pointer-events: auto !important;
        visibility: visible !important;
    }

    /* ---------- Mobile sidebar toggle ---------- */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        pointer-events: auto !important;
        position: fixed !important;
        top: 70px !important;
        left: 0 !important;
        right: auto !important;
        width: 38px !important;
        height: 42px !important;
        background: #1F2A44 !important;
        border: 1.5px solid #C6A75E !important;
        border-left: none !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 6px !important;
        margin: 0 !important;
        z-index: 2147483647 !important;
        box-shadow: 0 4px 14px rgba(31,42,68,0.5),
                    0 0 0 1px rgba(198,167,94,0.15) !important;
        align-items: center !important;
        justify-content: center !important;
        animation: toggle-pulse 3s ease-in-out infinite !important;
        transition: background 0.15s ease, transform 0.15s ease !important;
    }

    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="collapsedControl"]:hover {
        background: #2A3856 !important;
        transform: translateX(2px) !important;
    }

    @keyframes toggle-pulse {
        0%, 100% { box-shadow: 0 4px 14px rgba(31,42,68,0.5),
                               0 0 0 0 rgba(198,167,94,0.4); }
        50%      { box-shadow: 0 4px 14px rgba(31,42,68,0.5),
                               0 0 0 8px rgba(198,167,94,0); }
    }

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        fill: #C6A75E !important;
        color: #C6A75E !important;
        stroke: #C6A75E !important;
        width: 22px !important;
        height: 22px !important;
        display: block !important;
    }

    [data-testid="stSidebarCollapsedControl"] > div,
    [data-testid="collapsedControl"] > div {
        visibility: visible !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 100% !important;
    }

    /* ---------- Sidebar collapse button (desktop) ---------- */
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"],
    [data-testid="stSidebar"] button[kind="headerNoPadding"] {
        position: relative !important;
        top: auto !important;
        left: auto !important;
        right: auto !important;
        width: 30px !important;
        height: 30px !important;
        background: transparent !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        animation: none !important;
        transform: none !important;
        margin: 0 0 0.5rem 0 !important;
        padding: 4px !important;
        align-items: center !important;
        justify-content: center !important;
        display: flex !important;
        transition: background 0.15s ease !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"]:hover {
        background: rgba(198,167,94,0.18) !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"] svg {
        fill: #C6A75E !important;
        color: #C6A75E !important;
        stroke: #C6A75E !important;
        width: 18px !important;
        height: 18px !important;
    }

    [data-testid="stSidebar"] { z-index: 999998 !important; }

    @media (max-width: 768px) {
        [data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

    /* ============ HERO ============ */
    .hero {
        background: var(--navy);
        padding: 1.6rem 1.9rem;
        border-radius: 12px;
        margin-bottom: 1.4rem;
        border-left: 4px solid var(--gold);
        box-shadow: 0 1px 3px rgba(31,42,68,0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        overflow: hidden;
        position: relative;
    }
    .hero-content { position: relative; z-index: 2; min-width: 0; }
    .hero h1 {
        color: #FFFFFF; margin: 0; font-size: 1.4rem;
        font-weight: 700; letter-spacing: -0.01em; line-height: 1.3;
    }
    .hero p {
        color: rgba(255,255,255,0.72); margin: 0.35rem 0 0 0;
        font-size: 0.85rem; font-weight: 400; letter-spacing: 0.005em;
    }
    .hero .badge {
        display: inline-flex; align-items: center; gap: 0.4rem;
        background: rgba(198,167,94,0.15); color: var(--gold);
        padding: 0.28rem 0.7rem; border-radius: 4px;
        font-size: 0.7rem; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase;
        margin-top: 0.85rem;
        border: 1px solid rgba(198,167,94,0.35);
    }
    .hero .badge .dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #4ADE80; box-shadow: 0 0 6px rgba(74,222,128,0.8);
    }

    .hero-3d {
        width: 120px; height: 120px; perspective: 700px;
        opacity: 0.55; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
    }
    .hero-3d .cube {
        position: relative; width: 70px; height: 70px;
        transform-style: preserve-3d;
        animation: hero-spin 24s linear infinite;
    }
    .hero-3d .cube .face {
        position: absolute; width: 70px; height: 70px;
        border: 1px solid rgba(198,167,94,0.7);
        background: rgba(198,167,94,0.05);
        box-shadow: inset 0 0 20px rgba(198,167,94,0.08);
    }
    .hero-3d .cube .front  { transform: translateZ(35px); }
    .hero-3d .cube .back   { transform: rotateY(180deg) translateZ(35px); }
    .hero-3d .cube .right  { transform: rotateY(90deg)  translateZ(35px); }
    .hero-3d .cube .left   { transform: rotateY(-90deg) translateZ(35px); }
    .hero-3d .cube .top    { transform: rotateX(90deg)  translateZ(35px); }
    .hero-3d .cube .bottom { transform: rotateX(-90deg) translateZ(35px); }

    @keyframes hero-spin {
        0%   { transform: rotateX(-18deg) rotateY(0deg); }
        100% { transform: rotateX(-18deg) rotateY(360deg); }
    }

    @media (prefers-reduced-motion: reduce) {
        .hero-3d .cube { animation: none; transform: rotateX(-18deg) rotateY(35deg); }
    }
    @media (max-width: 768px) {
        .hero-3d { display: none; }
        .hero { padding: 1.4rem 1.15rem; }
        .hero h1 { font-size: 1.15rem; }
    }

    /* ============ METRIC CARDS ============ */
    .metric-card {
        background: var(--white);
        padding: 1.05rem 1.25rem;
        border-radius: 10px;
        border: 1px solid var(--border);
        border-top: 3px solid var(--navy);
        box-shadow: 0 1px 2px rgba(31,42,68,0.04);
        height: 100%;
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(31,42,68,0.08);
        border-color: #D1D5DB;
    }
    .metric-card.accent-gold   { border-top-color: var(--gold); }
    .metric-card.accent-warn   { border-top-color: #D97706; }
    .metric-card.accent-danger { border-top-color: #DC2626; }
    .metric-card.accent-ok     { border-top-color: #059669; }

    .metric-label {
        font-size: 0.72rem; font-weight: 600; color: var(--muted);
        text-transform: uppercase; letter-spacing: 0.06em; margin: 0;
    }
    .metric-value {
        font-size: 1.55rem; font-weight: 700; color: var(--ink);
        margin: 0.4rem 0 0 0; letter-spacing: -0.02em;
        line-height: 1.15; font-variant-numeric: tabular-nums;
    }
    .metric-value.primary { color: var(--navy); }
    .metric-value.gold    { color: var(--gold-700); }
    .metric-value.warn    { color: #B45309; }
    .metric-value.danger  { color: #B91C1C; }
    .metric-value.success { color: #047857; }

    .metric-icon {
        display: inline-block; font-size: 1rem;
        margin-bottom: 0.35rem; opacity: 0.85;
    }

    /* ============ SECTION HEADERS ============ */
    .section-header {
        font-size: 1.05rem; font-weight: 700; color: var(--ink);
        margin: 0 0 0.3rem 0; letter-spacing: -0.01em;
        padding-left: 0.75rem; border-left: 3px solid var(--gold);
        line-height: 1.3;
    }
    .section-sub {
        color: var(--muted); font-size: 0.82rem;
        margin: 0 0 1.1rem 0.75rem; font-weight: 400;
    }

    /* ============ MAIN BUTTONS ============ */
    .stButton > button {
        background: var(--navy); color: #FFFFFF;
        border: 1px solid var(--navy); border-radius: 8px;
        padding: 0.55rem 1.1rem;
        font-weight: 600; font-size: 0.83rem;
        letter-spacing: 0.01em;
        transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
        box-shadow: 0 1px 2px rgba(31,42,68,0.06);
        position: relative;
    }
    .stButton > button:hover {
        background: var(--navy-700);
        border-color: var(--gold);
        color: #FFFFFF;
    }
    .stButton > button:focus {
        color: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(198,167,94,0.25);
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        animation: btn-pulse 2.4s ease-in-out infinite;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        animation-play-state: paused;
        box-shadow: 0 0 0 4px rgba(198,167,94,0.28), 0 4px 12px rgba(31,42,68,0.15);
    }

    @keyframes btn-pulse {
        0%   { box-shadow: 0 1px 2px rgba(31,42,68,0.06), 0 0 0 0 rgba(198,167,94,0.55); }
        70%  { box-shadow: 0 1px 2px rgba(31,42,68,0.06), 0 0 0 10px rgba(198,167,94,0); }
        100% { box-shadow: 0 1px 2px rgba(31,42,68,0.06), 0 0 0 0 rgba(198,167,94,0); }
    }

    @media (prefers-reduced-motion: reduce) {
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            animation: none;
        }
    }

    .stDownloadButton > button {
        background: var(--gold); color: var(--navy);
        border: 1px solid var(--gold-700); border-radius: 8px;
        padding: 0.55rem 1.1rem; font-weight: 600; font-size: 0.83rem;
        letter-spacing: 0.01em;
        box-shadow: 0 1px 2px rgba(31,42,68,0.06);
    }
    .stDownloadButton > button:hover {
        background: var(--gold-700); color: #FFFFFF;
        border-color: var(--gold-700);
    }

    /* ============ INPUTS + TEXTAREA ============ */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px; border: 1px solid #D1D5DB;
        background: var(--white); padding: 0.55rem 0.8rem;
        font-size: 0.88rem;
        color: var(--ink);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--gold);
        box-shadow: 0 0 0 3px rgba(198,167,94,0.18);
    }
    label, .stTextInput label, .stNumberInput label, .stTextArea label {
        font-weight: 600 !important; color: var(--ink) !important;
        font-size: 0.8rem !important; letter-spacing: 0.02em;
        text-transform: none;
    }

    .stNumberInput button[data-testid="stNumberInputStepUp"],
    .stNumberInput button[data-testid="stNumberInputStepDown"],
    .stNumberInput div[data-baseweb="input"] button {
        display: none !important;
    }

    /* ============ INVENTORY HTML TABLE ============ */
    .inv-table-wrap {
        max-height: 720px; overflow-y: auto; overflow-x: auto;
        border-radius: 12px; border: 1px solid var(--border);
        background: var(--white);
        box-shadow: 0 4px 16px -8px rgba(31,42,68,0.12);
    }
    .inv-table-wrap::-webkit-scrollbar { width: 10px; height: 10px; }
    .inv-table-wrap::-webkit-scrollbar-track { background: #F7F8FA; border-radius: 10px; }
    .inv-table-wrap::-webkit-scrollbar-thumb {
        background: #D1D5DB; border-radius: 10px;
        border: 2px solid #F7F8FA;
    }
    .inv-table-wrap::-webkit-scrollbar-thumb:hover { background: var(--gold); }

    .inv-table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-size: 0.82rem; background: var(--white);
        font-feature-settings: "tnum";
    }

    .inv-table thead th {
        position: sticky; top: 0; z-index: 5;
        background: var(--navy) !important;
        color: #FFFFFF !important;
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        text-align: left !important;
        padding: 0.75rem 0.9rem !important;
        border: none !important;
        border-bottom: 3px solid var(--gold) !important;
        white-space: nowrap; user-select: none;
    }
    .inv-table thead th:first-child { border-top-left-radius: 12px; }
    .inv-table thead th:last-child  { border-top-right-radius: 12px; }
    .inv-table thead th:nth-child(5),
    .inv-table thead th:nth-child(6),
    .inv-table thead th:nth-child(7),
    .inv-table thead th:nth-child(8) { text-align: right !important; }

    .inv-table tbody td {
        color: var(--ink) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        padding: 0.65rem 0.9rem !important;
        border: none !important;
        border-bottom: 1px solid #E5E7EB !important;
        vertical-align: middle; line-height: 1.4;
        background: transparent;
        transition: background 0.12s ease;
    }
    .inv-table tbody td:nth-child(1) {
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-size: 0.75rem !important; font-weight: 600 !important;
        color: var(--navy) !important; letter-spacing: -0.01em;
    }
    .inv-table tbody td:nth-child(2) { font-weight: 600 !important; color: var(--ink) !important; }
    .inv-table tbody td:nth-child(3),
    .inv-table tbody td:nth-child(4) {
        color: var(--muted) !important; font-size: 0.75rem !important;
    }
    .inv-table tbody td:nth-child(5) {
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-size: 0.75rem !important; color: var(--muted) !important;
    }
    .inv-table tbody td:nth-child(6) {
        text-align: right !important;
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-weight: 700 !important; font-size: 0.82rem !important;
        color: var(--navy) !important;
        font-variant-numeric: tabular-nums;
    }
    .inv-table tbody td:nth-child(7) {
        text-align: right !important;
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-weight: 700 !important;
        color: #B45309 !important;
        font-variant-numeric: tabular-nums; white-space: nowrap;
    }
    .inv-table tbody td:nth-child(8) {
        text-align: right !important; color: var(--muted) !important;
        font-size: 0.72rem !important;
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-variant-numeric: tabular-nums; white-space: nowrap;
    }

    .inv-table tbody tr:nth-child(even) td { background-color: #FAFBFD !important; }
    .inv-table tbody tr:hover td { background-color: rgba(198,167,94,0.10) !important; }
    .inv-table tbody tr:last-child td { border-bottom: 1px solid #E5E7EB !important; }
    .inv-table tbody tr:last-child td:first-child { border-bottom-left-radius: 12px; }
    .inv-table tbody tr:last-child td:last-child  { border-bottom-right-radius: 12px; }

    @media (max-width: 768px) {
        .inv-table thead th, .inv-table tbody td {
            padding: 0.55rem 0.65rem !important;
            font-size: 0.75rem !important;
        }
        .inv-table thead th { font-size: 0.62rem !important; }
    }

    /* =========================================================
       SIDEBAR — Reference radio-style menu
       ========================================================= */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1F2A44 0%, #18223A 100%) !important;
        border-right: 1px solid #16202F;
    }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }

    [data-testid="stSidebar"] .stButton {
        margin: 0 !important;
        padding: 0 10px !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        position: relative !important;
        background: transparent !important;
        color: #CBD5E1 !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem 0.5rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.005em !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        animation: none !important;
        margin: 0 !important;
        min-height: 38px !important;
        height: auto !important;
        transition: background 0.18s ease, color 0.18s ease,
                    border-color 0.18s ease, box-shadow 0.18s ease !important;
        width: 100% !important;
        line-height: 1.35 !important;
    }

    [data-testid="stSidebar"] .stButton > button::before {
        content: "" !important;
        position: absolute !important;
        left: 12px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: 14px !important;
        height: 14px !important;
        border-radius: 50% !important;
        border: 2px solid #64748B !important;
        background: transparent !important;
        transition: all 0.18s ease !important;
        box-sizing: border-box !important;
    }

    [data-testid="stSidebar"] .stButton > button p {
        margin-left: 26px !important;
        font-size: 0.92rem !important;
        font-weight: inherit !important;
        letter-spacing: inherit !important;
        line-height: 1.4 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(198,167,94,0.08) !important;
        color: #FFFFFF !important;
        transform: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover::before {
        border-color: #C6A75E !important;
    }

    [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: none !important;
        outline: none !important;
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(90deg,
            rgba(232,220,200,0.14) 0%,
            rgba(232,220,200,0.06) 60%,
            transparent 100%) !important;
        color: #FFFFFF !important;
        border-left: 3px solid #C6A75E !important;
        font-weight: 600 !important;
        box-shadow:
            0 0 0 1px rgba(198,167,94,0.12) inset,
            0 0 24px -6px rgba(198,167,94,0.55),
            0 4px 24px -8px rgba(198,167,94,0.45) !important;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"]::before,
    [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"]::before {
        border-color: #C6A75E !important;
        background: #C6A75E !important;
        box-shadow: 0 0 0 4px rgba(198,167,94,0.15) !important;
    }

    [data-testid="stSidebar"] .stButton + .stButton {
        margin-top: 0 !important;
    }

    /* ============ ALERTS ============ */
    .stAlert {
        border-radius: 8px; border: 1px solid var(--border);
        box-shadow: none; font-size: 0.85rem;
    }

    /* ============ FILE UPLOADER ============ */
    [data-testid="stFileUploader"] { border-radius: 8px; }
    [data-testid="stFileUploader"] section {
        border-radius: 8px; border: 1.5px dashed #D1D5DB;
        background: var(--white); transition: border-color 0.15s ease;
    }
    [data-testid="stFileUploader"] section:hover { border-color: var(--gold); }

    .stProgress > div > div > div > div { background: var(--gold); }

    hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }

    @media (max-width: 900px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
        [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 45% !important; flex: 1 1 45% !important;
        }
    }

    /* =========================================================
       TOAST TIMING — keep toasts visible for 5 seconds
       Streamlit auto-dismisses toasts after ~4s; we extend the
       fade-out delay to 5s and add a gold countdown bar.
       ========================================================= */
    div[data-testid="stToast"] {
        animation-duration: 0.3s, 0.5s !important;
        animation-delay: 0s, 5s !important;
        position: relative !important;
        overflow: hidden !important;
    }

    /* Gold countdown bar inside each toast */
    div[data-testid="stToast"]::after {
        content: "" !important;
        position: absolute !important;
        left: 0 !important;
        bottom: 0 !important;
        height: 2px !important;
        background: linear-gradient(90deg, #C6A75E 0%, #A98A44 100%) !important;
        animation: toast-countdown 5s linear forwards !important;
        border-radius: 0 0 6px 6px !important;
    }

    @keyframes toast-countdown {
        0%   { width: 100%; }
        100% { width: 0%; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
#  🧭 NAVIGATION STATE
# =========================================================
DEFAULT_PAGE = "📋   View Inventory"

if "current_page" not in st.session_state:
    st.session_state["current_page"] = DEFAULT_PAGE

# =========================================================
#  SIDEBAR — Reference style
# =========================================================
with st.sidebar:
    # ---------- Branding ----------
    st.markdown(
        '<div style="display:flex; align-items:center; gap:12px; '
        'padding:6px 4px 24px 4px;">'
        '<div style="width:46px; height:46px; border-radius:12px; '
        'background:linear-gradient(135deg,#E8D4A5 0%,#C6A75E 100%); '
        'display:flex; align-items:center; justify-content:center; '
        'font-size:22px; flex-shrink:0; '
        'box-shadow: 0 6px 16px rgba(198,167,94,0.35);">📦</div>'
        '<div style="min-width:0;">'
        '<div style="font-size:0.98rem; font-weight:700; color:#FFFFFF; '
        'letter-spacing:-0.01em; line-height:1.25; margin-bottom:3px;">'
        'Inventory Hub</div>'
        '<div style="font-size:0.78rem; color:#C6A75E; '
        'letter-spacing:0.01em; font-weight:500; line-height:1.35;">'
        'AGT Inventory Management System</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---------- ADMIN section label ----------
    st.markdown(
        '<div style="font-size:0.72rem; color:#C6A75E; letter-spacing:0.16em; '
        'text-transform:uppercase; font-weight:700; margin:0 0 14px 12px;">'
        'Admin</div>',
        unsafe_allow_html=True,
    )

    # ---------- ADMIN: Audit Log ----------
    _audit_active = st.session_state["current_page"] == "📜   Audit Log"
    if st.button(
            "📜   Audit Log",
            key="nav_btn_audit",
            use_container_width=True,
            type=("primary" if _audit_active else "secondary"),
    ):
        st.session_state["current_page"] = "📜   Audit Log"
        st.rerun()

    # ---------- Divider between ADMIN and MENU ----------
    st.markdown(
        '<div style="display:flex; align-items:center; gap:10px; '
        'margin:24px 12px 14px 12px;">'
        '<div style="flex:1; height:1px; '
        'background:linear-gradient(90deg,transparent,rgba(198,167,94,0.45));">'
        '</div>'
        '<span style="font-size:0.66rem; font-weight:700; letter-spacing:0.16em; '
        'color:#C6A75E; text-transform:uppercase;">Menu</span>'
        '<div style="flex:1; height:1px; '
        'background:linear-gradient(90deg,rgba(198,167,94,0.45),transparent);">'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---------- Menu items ----------
    _main_items = [
        "📋   View Inventory",
        "⚠️   Low Stock Items",
        "📤   Update from Excel",
        "⚙️   Update by DN-60",
        "📊   Check Production",
        "🧮   Required Items",
    ]

    for _item in _main_items:
        _is_active = st.session_state["current_page"] == _item
        if st.button(
                _item,
                key=f"nav_btn_{_item}",
                use_container_width=True,
                type=("primary" if _is_active else "secondary"),
        ):
            st.session_state["current_page"] = _item
            st.rerun()

    # ---------- Footer ----------
    st.markdown(
        '<div style="margin-top:32px; padding:18px 12px 0 12px; '
        'border-top:1px solid rgba(198,167,94,0.18); '
        'display:flex; align-items:center; justify-content:space-between; '
        'font-size:0.68rem; color:#94A3B8; white-space:nowrap;">'
        '<div style="display:flex; align-items:center; gap:6px;">'
        '<span style="width:6px; height:6px; border-radius:50%; '
        'background:#22C55E; box-shadow:0 0 6px rgba(34,197,94,0.8);"></span>'
        '<span style="font-weight:500;">Online</span>'
        '</div>'
        '<span style="opacity:0.6; font-weight:500;">© 2026 AASHDHA GLOBAL TECH</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------- Resolve current page ----------
page = st.session_state["current_page"]

# =========================================================
#  HERO HEADER
# =========================================================
st.markdown(f"""
<div class="hero">
    <div class="hero-content">
        <h1>AGT Inventory Management System</h1>
        <p>DN-60 Valve Production Tracker</p>
        <span class="badge"><span class="dot"></span> Live · {now_ist().strftime('%d %b %Y, %H:%M')}</span>
    </div>
    <div class="hero-3d" aria-hidden="true">
        <div class="cube">
            <div class="face front"></div>
            <div class="face back"></div>
            <div class="face right"></div>
            <div class="face left"></div>
            <div class="face top"></div>
            <div class="face bottom"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
#  QUICK STATS — 5 cards
# =========================================================
try:
    total_items = collection.count_documents({})
    total_qty_pipeline = list(collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$Quantity"}}}
    ]))
    total_qty = total_qty_pipeline[0]["total"] if total_qty_pipeline else 0

    _all_items = list(collection.find(
        {},
        {"_id": 0, "Item_code": 1, "Quantity": 1}
    ))
    low_stock = sum(
        1 for it in _all_items
        if is_low_stock(it.get("Item_code", ""), it.get("Quantity", 0))
    )
except Exception:
    total_items, low_stock, total_qty = 0, 0, 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📦</div>
        <p class="metric-label">Item Types</p>
        <p class="metric-value primary">{total_items}</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card accent-ok">
        <div class="metric-icon">🔢</div>
        <p class="metric-label">Total Quantity</p>
        <p class="metric-value success">{total_qty:,}</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card {'accent-danger' if low_stock > 0 else 'accent-ok'}">
        <div class="metric-icon">⚠️</div>
        <p class="metric-label">Low Stock Items</p>
        <p class="metric-value {'danger' if low_stock > 0 else 'success'}">{low_stock}</p>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card accent-gold">
        <div class="metric-icon">🎯</div>
        <p class="metric-label">DN-60 Parts</p>
        <p class="metric-value gold">{len(DN60_PART_NUM)}</p>
    </div>
    """, unsafe_allow_html=True)
with c5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🕐</div>
        <p class="metric-label">Last Checked</p>
        <p class="metric-value" style="font-size:1.05rem;">{now_ist().strftime('%d-%m-%Y %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
#  ROUTED CONTENT
# =========================================================

# ---------------------------------------------------------
#  SECTION 1 — Upload Excel & Update
# ---------------------------------------------------------
if page == "📤   Update from Excel":
    st.markdown('<div class="section-header">📤 Update Inventory from Excel</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload your Item_Sheet.xlsx to replace the entire inventory.</div>',
                unsafe_allow_html=True)

    st.warning("⚠️ **Warning:** This will DROP the existing collection and re-insert all items from the uploaded file.")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        password1 = st.text_input("🔒 Enter Password", type="password", key="pwd1", placeholder="Enter Password")
    with col_b:
        uploaded_file = st.file_uploader("📁 Choose Item_Sheet.xlsx", type=["xlsx"], key="uploader1")

    st.markdown("<br>", unsafe_allow_html=True)

    progress_ph = st.empty()
    result_ph = st.empty()

    if st.button("🚀 Update Inventory", key="btn1", type="primary", use_container_width=True):
        if password1.lower() == "kishan":
            st.success("👑 Welcome back, boss. You *are* the system.")
        elif password1.lower() != "updatek":
            st.error(funny(WRONG_PASSWORD_LINES))
            st.toast("🔐 Access denied!", icon="🚨")
        elif uploaded_file is None:
            st.warning(funny(NO_FILE_LINES))
        else:
            try:
                with progress_ph.container():
                    st.markdown('<div id="upload-progress-anchor"></div>', unsafe_allow_html=True)
                    st.info("⏳ Upload in progress — please wait…")
                auto_scroll_to("upload-progress-anchor", delay=150)

                with st.spinner("Updating inventory..."):
                    ops.download_excel_data('old')
                    collection.drop()

                    df = pd.read_excel(uploaded_file)
                    st.info(f"📄 Total rows in file: {len(df)}")

                    inserted, duplicates = 0, 0
                    progress = st.progress(0)

                    for index, row in df.iterrows():
                        data = row.to_dict()
                        data["_id"] = str(data["Item_code"]).strip()
                        data["Item_code"] = str(data["Item_code"]).strip()
                        data["Item_name"] = str(data.get("Item_name", "")).strip().upper()
                        data["Item_category"] = str(data.get("Item_category", "")).strip().upper()
                        data["Item_subcategory"] = str(data.get("Item_subcategory", "")).strip().upper()
                        data["Quantity"] = int(data["Quantity"])
                        data["Updated_date"] = now_ist().strftime("%d-%m-%Y %H:%M:%S")
                        try:
                            collection.insert_one(data)
                            log_history(
                                item_code=data["Item_code"],
                                item_name=data["Item_name"],
                                old_qty=0,
                                new_qty=int(data["Quantity"]),
                                reason="Excel upload (initial)",
                            )
                            inserted += 1
                        except Exception:
                            duplicates += 1
                        progress.progress((index + 1) / len(df))

                progress_ph.empty()

                with result_ph.container():
                    st.markdown('<div id="upload-success-anchor"></div>', unsafe_allow_html=True)
                    show_upload_success_animated(inserted, duplicates, len(df))

                auto_scroll_to("upload-success-anchor", delay=400)

                ok, msg = maybe_send_low_stock_alert(
                    trigger_reason="Excel re-upload"
                )
                if ok:
                    st.toast(f"📧 Low-stock alert emailed — {msg}", icon="📬")
                else:
                    st.toast(f"📧 Alert not sent: {msg}", icon="⚠️")

                if inserted >= 100:
                    st.toast(f"🎊 {inserted} items in one go, Kishan! Legendary upload.", icon="🏆")
                elif inserted >= 30:
                    st.toast("📦 Solid upload — nice work, Kishan.", icon="👍")
                else:
                    st.toast("✅ Uploaded. Small batch, no drama.", icon="📎")

            except Exception as e:
                progress_ph.empty()
                st.error(f"❌ Update failed: {e}")

# ---------------------------------------------------------
#  SECTION 2 — Update by DN-60 valve count
# ---------------------------------------------------------
elif page == "⚙️   Update by DN-60":
    st.markdown('<div class="section-header">⚙️ Update by DN-60 Valve Count</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Subtract parts required to build a given number of DN-60 valves.</div>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        password2 = st.text_input("🔒 Enter Password", type="password", key="pwd2", placeholder="Enter Password")
    with col_b:
        dn60_count = st.number_input("🔧 Number of valves", min_value=1, value=10, step=1, key="n2")

    st.markdown("<br>", unsafe_allow_html=True)

    dn60_result_ph = st.empty()

    if st.button("⚙️ Build Valves", key="btn2", type="primary", use_container_width=True):
        if password2.lower() == "kishan":
            st.success("👑 Right away, boss. Building at your command.")
        elif password2.lower() != "dn60k":
            st.error(funny(WRONG_PASSWORD_LINES))
            st.toast("🔐 Access denied!", icon="🚨")
        else:
            big_msg = big_order_message(dn60_count)
            if big_msg:
                st.info(big_msg)

            try:
                errors = []
                for part_num, per_valve in DN60_PART_NUM.items():
                    doc = collection.find_one({"Item_code": part_num})
                    if not doc:
                        errors.append(f"Part {part_num} not found in DB")
                        continue
                    old_count = int(doc['Quantity'])
                    required = dn60_count * per_valve
                    if old_count < required:
                        errors.append(f"[{part_num}] {doc['Item_name']} — need {required}, have {old_count}")

                if errors:
                    st.error("❌ Cannot subtract — insufficient stock:")
                    for e in errors:
                        st.write(f"• {e}")
                else:
                    ops.download_excel_data('old')
                    today = now_ist().strftime("%d-%m-%Y")
                    rows = []

                    for part_num in sorted(DN60_PART_NUM, key=int):
                        per_valve = DN60_PART_NUM[part_num]
                        doc = collection.find_one({"Item_code": part_num})

                        old_count = int(doc['Quantity'])
                        used = dn60_count * per_valve
                        new_count = old_count - used

                        collection.update_one(
                            {"Item_code": part_num},
                            {"$set": {"Quantity": new_count, "Updated_date": today}}
                        )
                        log_history(
                            item_code=part_num,
                            item_name=doc['Item_name'],
                            old_qty=old_count,
                            new_qty=new_count,
                            reason=f"Build {dn60_count} DN-60 valves",
                        )

                        rows.append({
                            "#": part_num,
                            "Item Name": doc['Item_name'],
                            "Old": old_count,
                            "Used": used,
                            "New": new_count,
                        })

                    with dn60_result_ph.container():
                        st.markdown('<div id="dn60-result-anchor"></div>', unsafe_allow_html=True)
                        st.success(f"✅ Stock updated for building **{dn60_count}** valves!")
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    auto_scroll_to("dn60-result-anchor", delay=350)

                    ok, msg = maybe_send_low_stock_alert(
                        trigger_reason=f"DN-60 build ({dn60_count} valves)"
                    )
                    if ok:
                        st.toast(f"📧 Low-stock alert emailed — {msg}", icon="📬")
                    else:
                        st.toast(f"📧 Alert not sent: {msg}", icon="⚠️")
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

# ---------------------------------------------------------
#  SECTION 3 — Check DN-60 production capacity
# ---------------------------------------------------------
elif page == "📊   Check Production":
    st.markdown('<div class="section-header">📊 DN-60 Production Capacity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">How many DN-60 valves can be produced with the current stock?</div>',
                unsafe_allow_html=True)

    prod_result_ph = st.empty()

    if st.button("🔄 Check Capacity", key="btn3", type="primary", use_container_width=True):
        try:
            limits, available, part_names = {}, {}, {}

            for part, qty_per_valve in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                if item:
                    stock = int(item.get("Quantity", 0))
                    name = item.get("Item_name", f"Part {part}")
                else:
                    stock = 0
                    name = f"Part {part} (not found)"

                available[part] = stock
                limits[part] = stock // qty_per_valve
                part_names[part] = name

            max_valves = min(limits.values())
            limiting_part = min(limits, key=limits.get)

            if available[limiting_part] == 0:
                st.toast(funny(ZERO_STOCK_LINES), icon="😬")

            with prod_result_ph.container():
                st.markdown('<div id="prod-result-anchor"></div>', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""
                    <div class="metric-card accent-gold">
                        <div class="metric-icon">🎯</div>
                        <p class="metric-label">Max Valves</p>
                        <p class="metric-value gold">{max_valves}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="metric-card accent-warn">
                        <div class="metric-icon">⚠️</div>
                        <p class="metric-label">Limiting Part</p>
                        <p class="metric-value warn" style="font-size:1.05rem;">{part_names[limiting_part]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""
                    <div class="metric-card accent-danger">
                        <div class="metric-icon">📦</div>
                        <p class="metric-label">Stock of Limiting Part</p>
                        <p class="metric-value danger">{available[limiting_part]}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                rows = []
                for part in sorted(DN60_PART_NUM, key=int):
                    rows.append({
                        "Part": part,
                        "Part Name": part_names[part],
                        "Stock": available[part],
                        "Per Valve": DN60_PART_NUM[part],
                        "Can Make": limits[part],
                        "Status": "⚠️ LIMITING" if part == limiting_part else "✅ OK",
                    })

                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                st.info(
                    f"**Bottleneck:** {part_names[limiting_part]} — need **{DN60_PART_NUM[limiting_part]}/valve**, have **{available[limiting_part]}**")

            auto_scroll_to("prod-result-anchor", delay=350)
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 4 — Required items for target
# ---------------------------------------------------------
elif page == "🧮   Required Items":
    st.markdown('<div class="section-header">🧮 Parts Required for Target Quantity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Calculate how many parts to order to build N valves.</div>',
                unsafe_allow_html=True)

    target = st.number_input("🎯 Target number of DN-60 valves", min_value=1, value=100, step=1, key="target4")

    req_result_ph = st.empty()

    if st.button("🧮 Calculate", key="btn4", type="primary", use_container_width=True):
        try:
            rows, total_short = [], 0

            for part, per_valve in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                if item:
                    stock = int(item.get("Quantity", 0))
                    name = item.get("Item_name", f"Part {part}")
                    category = item.get("Item_category", "—")
                    subcategory = item.get("Item_subcategory", "—")
                else:
                    stock = 0
                    name = f"Part {part} (not found)"
                    category = "—"
                    subcategory = "—"

                needed = per_valve * target
                shortfall = max(0, needed - stock)
                if shortfall > 0:
                    total_short += 1

                rows.append({
                    "Part": part,
                    "Part Name": name,
                    "Category": category,
                    "Subcategory": subcategory,
                    "Per": per_valve,
                    "Stock": stock,
                    "Needed": needed,
                    "Order": shortfall,
                    "Status": "🛒 ORDER" if shortfall > 0 else "✅ OK",
                })

            with req_result_ph.container():
                st.markdown('<div id="req-result-anchor"></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <div class="metric-card accent-gold">
                        <div class="metric-icon">🎯</div>
                        <p class="metric-label">Target</p>
                        <p class="metric-value gold">{target}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="metric-card {'accent-danger' if total_short > 0 else 'accent-ok'}">
                        <div class="metric-icon">🛒</div>
                        <p class="metric-label">Parts to Order</p>
                        <p class="metric-value {'danger' if total_short > 0 else 'success'}">{total_short}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True, height=600)

                if total_short == 0:
                    st.success("✅ You already have enough stock! No order needed.")
                else:
                    if total_short >= 8:
                        st.warning(
                            f"🛒 **ORDER LIST:** — {total_short} parts to order. Kishan, your wallet just fainted.")
                    elif total_short >= 4:
                        st.warning(f"🛒 **ORDER LIST:** — {total_short} parts. Manageable, but not fun.")
                    else:
                        st.warning("🛒 **ORDER LIST:**")

                    order_rows = [r for r in rows if r["Order"] > 0]
                    for r in order_rows:
                        st.write(
                            f"• **{r['Part Name']}** "
                            f"_(Category: {r['Category']} · Sub: {r['Subcategory']})_ "
                            f"→ order **{r['Order']}** nos"
                        )

            auto_scroll_to("req-result-anchor", delay=350)
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 5 — View current inventory + search + download + adjust
# ---------------------------------------------------------
elif page == "📋   View Inventory":
    if st.session_state.pop("clear_inv_filters", False):
        st.session_state["inv_search"] = ""
        st.session_state["inv_category"] = "All"
        st.session_state["inv_subcategory"] = "All"

    col_load, col_info = st.columns([1, 3])

    with col_load:
        load_clicked = st.button(
            "🔄 Load Inventory",
            key="btn5",
            type="primary",
            use_container_width=True,
        )

    with col_info:
        if "inv_data" in st.session_state:
            cached_at = st.session_state.get("inv_loaded_at", "")
            st.caption(f"✔️ Data loaded · {cached_at}")

    if load_clicked or "inv_data" not in st.session_state:
        try:
            data = list(collection.find({}, {
                "_id": 0,
                "Item_code": 1, "Item_name": 1,
                "Item_category": 1, "Item_subcategory": 1,
                "Location": 1, "Quantity": 1,
                "Updated_date": 1,
            }).sort("Item_code", 1))

            if not data:
                st.warning("⚠️ Inventory is empty.")
                st.session_state.pop("inv_data", None)
                st.stop()

            df = pd.DataFrame(data)
            df["Quantity"] = df["Quantity"].astype(int)

            st.session_state["inv_data"] = df
            st.session_state["inv_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M')

        except Exception as e:
            st.error(f"❌ Failed to load: {e}")
            st.stop()

    df = st.session_state.get("inv_data")
    if df is None or df.empty:
        st.info("Click **🔄 Load Inventory** to fetch current stock.")
        st.stop()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-header" style="font-size:0.95rem; margin-bottom:0.5rem;">'
        '🔍 Search & Filter</div>',
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3 = st.columns([3, 1, 1])

    with fc1:
        search_text = st.text_input(
            "Search",
            placeholder="🔎 Try: O-RING, BOLT, CIRCLIP, or a code like 94181553L",
            key="inv_search",
            help="Case-insensitive · partial match · searches both name and code",
            label_visibility="collapsed",
        )

    with fc2:
        category_opts = ["All"] + sorted(
            [c for c in df["Item_category"].dropna().unique().tolist() if str(c).strip()]
        )
        if st.session_state.get("inv_category") not in category_opts:
            st.session_state["inv_category"] = "All"
        selected_category = st.selectbox(
            "Category",
            options=category_opts,
            key="inv_category",
            label_visibility="collapsed",
        )

    with fc3:
        if selected_category == "All":
            sub_pool = df["Item_subcategory"].dropna().unique().tolist()
        else:
            sub_pool = df.loc[
                df["Item_category"] == selected_category, "Item_subcategory"
            ].dropna().unique().tolist()

        subcategory_opts = ["All"] + sorted([s for s in sub_pool if str(s).strip()])
        if st.session_state.get("inv_subcategory") not in subcategory_opts:
            st.session_state["inv_subcategory"] = "All"
        selected_subcategory = st.selectbox(
            "Subcategory",
            options=subcategory_opts,
            key="inv_subcategory",
            label_visibility="collapsed",
        )

    filtered = df.copy()

    if search_text.strip():
        q = search_text.strip().lower()
        mask = (
                filtered["Item_name"].astype(str).str.lower().str.contains(q, na=False)
                | filtered["Item_code"].astype(str).str.lower().str.contains(q, na=False)
        )
        filtered = filtered[mask]

    if selected_category != "All":
        filtered = filtered[filtered["Item_category"] == selected_category]

    if selected_subcategory != "All":
        filtered = filtered[filtered["Item_subcategory"] == selected_subcategory]

    sc1, sc2 = st.columns([4, 1])

    with sc1:
        st.caption(
            f"Showing **{len(filtered)}** of **{len(df)}** items"
            + (f" · {len(df) - len(filtered)} filtered out"
               if len(filtered) < len(df) else "")
        )

    with sc2:
        if len(filtered) < len(df):
            if st.button("🧹 Clear", key="clear_filters", use_container_width=True):
                st.session_state["clear_inv_filters"] = True
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if filtered.empty:
        st.info("🔍 No items match your search. Try different keywords or clear filters.")
    else:
        display_df = filtered.copy()
        display_df = display_df.fillna("—")
        display_df = display_df.astype(str).replace({
            "nan": "—", "NaN": "—", "NAN": "—",
            "None": "—", "none": "—",
            "null": "—", "NULL": "—",
            "NaT": "—", "": "—",
        })

        display_df = display_df.rename(columns={
            "Item_code": "Code",
            "Item_name": "Item Name",
            "Item_category": "Category",
            "Item_subcategory": "Subcategory",
            "Location": "Location",
            "Quantity": "Qty",
            "Updated_date": "Updated (IST)",
        })

        html_table = display_df.to_html(
            index=False,
            classes="inv-table",
            escape=False,
            border=0,
        )

        st.markdown(
            f'<div class="inv-table-wrap">{html_table}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header" style="font-size:0.95rem; margin-bottom:0.5rem;">'
        '⚡ Quick Stock Adjustment</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-sub" style="margin-bottom:0.9rem;">'
        'Set the current stock for any item — password same as Excel update.</div>',
        unsafe_allow_html=True,
    )

    # Container to hold the loading state
    adj_progress_ph = st.empty()
    flash_ph = st.empty()

    # 🚨 Auto-scroll fix for success flash
    if st.session_state.pop("scroll_to_adj_flash", False):
        auto_scroll_to("adj-flash-anchor", delay=250)

    _flash = st.session_state.pop("adj_flash", None)
    if _flash:
        with flash_ph.container():
            st.markdown('<div id="adj-flash-anchor"></div>', unsafe_allow_html=True)
            if _flash["status"] == "ok":
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
                        border: 1.5px solid #059669;
                        border-left: 5px solid #047857;
                        border-radius: 10px;
                        padding: 0.9rem 1.15rem;
                        margin: 0.3rem 0 1rem 0;
                        box-shadow: 0 2px 8px -2px rgba(5,150,105,0.25);
                        font-family: 'Inter', sans-serif;
                    ">
                        <div style="
                            display: flex; align-items: center; gap: 0.5rem;
                            font-weight: 700; color: #065F46;
                            font-size: 0.95rem; margin-bottom: 0.35rem;
                        ">
                            <span style="font-size:1.1rem;">✅</span>
                            Stock Updated Successfully
                        </div>
                        <div style="
                            color: #047857; font-size: 0.88rem; line-height: 1.55;
                        ">
                            <span style="
                                font-family: 'JetBrains Mono', monospace;
                                background: rgba(5,150,105,0.12);
                                padding: 2px 8px; border-radius: 5px;
                                font-weight: 700; color: #065F46;
                            ">{_flash['code']}</span>
                            &nbsp;—&nbsp;
                            <strong style="color: #065F46;">{_flash['name']}</strong>
                            <br>
                            <span style="opacity: 0.85;">
                                Quantity:
                                <strong>{_flash['old']}</strong>
                                &nbsp;→&nbsp;
                                <strong style="color:#047857;">{_flash['new']}</strong>
                                &nbsp;
                                <span style="
                                    background: rgba(5,150,105,0.18);
                                    padding: 1px 7px; border-radius: 4px;
                                    font-family: 'JetBrains Mono', monospace;
                                    font-weight: 700;
                                ">{_flash['diff']}</span>
                            </span>
                            <br>
                            <span style="opacity: 0.85; font-style: italic;">
                                Reason: {_flash.get('reason', '—')}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="
                        background: #EFF6FF; border: 1.5px solid #3B82F6;
                        border-left: 5px solid #1D4ED8; border-radius: 10px;
                        padding: 0.85rem 1.1rem; margin: 0.3rem 0 1rem 0;
                        color: #1E40AF; font-weight: 600; font-size: 0.88rem;
                        font-family: 'Inter', sans-serif;
                    ">
                        ℹ️ No change — <code>{_flash['code']}</code>
                        is still <strong>{_flash['new']}</strong>.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    _flash_err = st.session_state.pop("adj_flash_err", None)
    if _flash_err:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
                border: 1.5px solid #DC2626;
                border-left: 5px solid #B91C1C;
                border-radius: 10px;
                padding: 0.85rem 1.1rem; margin: 0.3rem 0 1rem 0;
                color: #991B1B; font-weight: 600; font-size: 0.88rem;
                font-family: 'Inter', sans-serif;
            ">
                🚨 {_flash_err}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not filtered.empty:
        adj_c1, adj_c2, adj_c3 = st.columns([1.2, 3, 1.2])

        with adj_c1:
            adj_pwd = st.text_input(
                "🔒 Password",
                type="password",
                key="adj_pwd",
                placeholder="Password",
            )

        with adj_c2:
            adj_item = st.selectbox(
                "Item",
                options=["— Select item —"] + filtered["Item_code"].astype(str).tolist(),
                key="adj_item",
            )

        if adj_item != "— Select item —":
            _doc = collection.find_one({"Item_code": adj_item})
            _current_qty = int(_doc.get("Quantity", 0)) if _doc else 0
        else:
            _current_qty = 0

        with adj_c3:
            adj_new_qty = st.number_input(
                "Current Stock",
                min_value=0,
                max_value=10_000_000,
                value=_current_qty,
                step=1,
                key=f"adj_new_qty_{adj_item}",
            )

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        adj_reason = st.text_area(
            "📝 Reason (required)",
            placeholder="e.g. Received 500 from supplier / Corrected physical count / Damaged goods removed",
            key="adj_reason_input",
            height=80,
            max_chars=300,
        )

        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

        save_clicked = st.button(
            "💾 Update Stock",
            key="adj_save",
            type="primary",
            use_container_width=True,
        )

        if save_clicked:
            if adj_pwd.lower() not in ("updatek", "kishan"):
                st.session_state["adj_flash_err"] = funny(WRONG_PASSWORD_LINES)
                st.session_state.pop("inv_data", None)
                st.rerun()
            elif adj_item == "— Select item —":
                st.session_state["adj_flash_err"] = "Please select an item first."
                st.session_state.pop("inv_data", None)
                st.rerun()
            elif not adj_reason.strip():
                st.session_state[
                    "adj_flash_err"] = "⚠️ Please enter a reason for this change — it's required for the audit log."
                st.session_state.pop("inv_data", None)
                st.rerun()
            else:
                # 1. Show loading state and scroll to it
                with adj_progress_ph.container():
                    st.markdown('<div id="adj-progress-anchor"></div>', unsafe_allow_html=True)
                    st.info("⏳ Updating stock — please wait…")
                auto_scroll_to("adj-progress-anchor", delay=150)

                doc = collection.find_one({"Item_code": adj_item})
                if not doc:
                    st.session_state["adj_flash_err"] = f"Item {adj_item} not found in DB."
                    st.session_state.pop("inv_data", None)
                    st.rerun()
                else:
                    old_qty = int(doc.get("Quantity", 0))
                    new_qty = int(adj_new_qty)
                    item_name = doc.get("Item_name", "")

                    collection.update_one(
                        {"Item_code": adj_item},
                        {"$set": {
                            "Quantity": new_qty,
                            "Updated_date": now_ist().strftime("%d-%m-%Y %H:%M:%S"),
                        }}
                    )
                    log_history(
                        item_code=adj_item,
                        item_name=item_name,
                        old_qty=old_qty,
                        new_qty=new_qty,
                        reason=adj_reason.strip(),
                    )

                    if new_qty > old_qty:
                        diff_txt = f"+{new_qty - old_qty}"
                    elif new_qty < old_qty:
                        diff_txt = f"{new_qty - old_qty}"
                    else:
                        diff_txt = "±0"

                    st.session_state["adj_flash"] = {
                        "code": adj_item,
                        "name": item_name,
                        "old": old_qty,
                        "new": new_qty,
                        "diff": diff_txt,
                        "reason": adj_reason.strip(),
                        "status": "ok" if new_qty != old_qty else "same",
                    }

                    if is_low_stock(adj_item, new_qty):
                        ok, msg = maybe_send_low_stock_alert(
                            trigger_reason=f"Adjust {adj_item} ({old_qty}→{new_qty})"
                        )
                        if ok:
                            st.toast(f"📧 Low-stock alert emailed — {msg}", icon="📬")
                        else:
                            st.toast(f"📧 Alert not sent: {msg}", icon="⚠️")

                    st.session_state.pop("adj_reason_input", None)
                    st.session_state.pop("inv_data", None)

                    # 2. Flag for auto-scroll after rerun
                    st.session_state["scroll_to_adj_flash"] = True
                    time.sleep(1)  # Let the user see the loading spinner
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Current Stock")

    timestamp = now_ist().strftime("%d-%m-%Y__%H-%M")

    if df.empty:
        st.button(
            "📥 Download as Excel",
            disabled=True,
            use_container_width=True,
            key="dl5_disabled",
            help="Nothing to download — inventory is empty.",
        )
    else:
        st.download_button(
            label=f"📥 Download Full Inventory ({len(df)} items) as Excel",
            data=buffer.getvalue(),
            file_name=f"agt_full_inventory_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl5",
            use_container_width=True,
        )

# ---------------------------------------------------------
#  SECTION 6 — Low Stock Items
# ---------------------------------------------------------
elif page == "⚠️   Low Stock Items":
    st.markdown('<div class="section-header">⚠️ Low Stock Items</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">'
        f'Every item below its minimum threshold '
        f'(default: {DEFAULT_LOW_STOCK} · some parts have custom minimums).'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_load, col_info = st.columns([1, 3])

    with col_load:
        low_load_clicked = st.button(
            "🔄 Load Low Stock",
            key="btn6",
            type="primary",
            use_container_width=True,
        )

    with col_info:
        if "low_data" in st.session_state:
            cached_at = st.session_state.get("low_loaded_at", "")
            st.caption(f"✔️ Data loaded · {cached_at}")

    _LOW_CACHE_VERSION = 3

    if (
            low_load_clicked
            or "low_data" not in st.session_state
            or st.session_state.get("low_cache_version") != _LOW_CACHE_VERSION
    ):
        try:
            _all = list(collection.find(
                {},
                {
                    "_id": 0,
                    "Item_code": 1, "Item_name": 1,
                    "Item_category": 1, "Item_subcategory": 1,
                    "Location": 1, "Quantity": 1,
                    "Updated_date": 1,
                }
            ))

            df_all = pd.DataFrame(_all)
            if not df_all.empty:
                df_all["Quantity"] = df_all["Quantity"].astype(int)

                df = df_all[
                    df_all.apply(
                        lambda r: is_low_stock(r["Item_code"], r["Quantity"]),
                        axis=1
                    )
                ].copy()

                df["Threshold"] = df["Item_code"].apply(low_stock_threshold)
                df = df.sort_values("Quantity", ascending=True).reset_index(drop=True)
            else:
                df = pd.DataFrame()

            st.session_state["low_data"] = df
            st.session_state["low_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M')
            st.session_state["low_cache_version"] = _LOW_CACHE_VERSION

        except Exception as e:
            st.error(f"❌ Failed to load: {e}")
            st.stop()

    df_low = st.session_state.get("low_data")

    if df_low is None or df_low.empty:
        st.success("🎉 Great news — no items are below their thresholds!")
        st.stop()

    total_low_items = len(df_low)
    out_of_stock = int((df_low["Quantity"] == 0).sum())

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
            border: 2px solid #F59E0B;
            border-left: 6px solid #D97706;
            border-radius: 12px;
            padding: 1.1rem 1.35rem;
            box-shadow: 0 4px 14px -4px rgba(245,158,11,0.45);
            height: 100%;
        ">
            <div style="font-size:1.3rem; margin-bottom:0.35rem;">⚠️</div>
            <p style="
                font-size: 0.75rem; font-weight: 700; color: #92400E;
                text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
            ">Low Stock Items</p>
            <p style="
                font-size: 1.9rem; font-weight: 800; color: #B45309;
                margin: 0.45rem 0 0 0; letter-spacing: -0.02em; line-height: 1.1;
            ">{total_low_items}</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
            border: 2px solid #EF4444;
            border-left: 6px solid #DC2626;
            border-radius: 12px;
            padding: 1.1rem 1.35rem;
            box-shadow: 0 4px 14px -4px rgba(239,68,68,0.45);
            height: 100%;
        ">
            <div style="font-size:1.3rem; margin-bottom:0.35rem;">🚫</div>
            <p style="
                font-size: 0.75rem; font-weight: 700; color: #991B1B;
                text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
            ">Out of Stock (0)</p>
            <p style="
                font-size: 1.9rem; font-weight: 800; color: #B91C1C;
                margin: 0.45rem 0 0 0; letter-spacing: -0.02em; line-height: 1.1;
            ">{out_of_stock}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-header" style="font-size:0.95rem; margin-bottom:0.5rem;">'
        '🔍 Search Low Stock</div>',
        unsafe_allow_html=True,
    )

    search_low = st.text_input(
        "Search",
        placeholder="🔎 Filter by item name or code…",
        key="low_search",
        label_visibility="collapsed",
    )

    df_filtered = df_low.copy()
    if search_low.strip():
        q = search_low.strip().lower()
        mask = (
                df_filtered["Item_name"].astype(str).str.lower().str.contains(q, na=False)
                | df_filtered["Item_code"].astype(str).str.lower().str.contains(q, na=False)
        )
        df_filtered = df_filtered[mask]

    st.caption(
        f"Showing **{len(df_filtered)}** of **{len(df_low)}** low-stock items"
        + (f" · {len(df_low) - len(df_filtered)} filtered out"
           if len(df_filtered) < len(df_low) else "")
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if df_filtered.empty:
        st.info("🔍 No low-stock items match your search.")
    else:
        def clean(v):
            if pd.isna(v) or str(v).lower() in ("nan", "none", "null", "nat"):
                return "—"
            return str(v)


        rows_html = []
        for _, r in df_filtered.iterrows():
            qty = int(r.get("Quantity", 0))
            threshold_val = int(r.get("Threshold", DEFAULT_LOW_STOCK))

            rows_html.append(
                "<tr>"
                f"<td>{clean(r.get('Item_code'))}</td>"
                f"<td>{clean(r.get('Item_name'))}</td>"
                f"<td>{clean(r.get('Item_category'))}</td>"
                f"<td>{clean(r.get('Item_subcategory'))}</td>"
                f"<td>{clean(r.get('Location'))}</td>"
                f"<td style='text-align:right;'>{qty}</td>"
                f"<td style='text-align:right;'>{threshold_val}</td>"
                f"<td style='text-align:right;'>{clean(r.get('Updated_date'))}</td>"
                "</tr>"
            )

        html_table = (
                '<table class="inv-table">'
                '<thead><tr>'
                '<th>Code</th>'
                '<th>Item Name</th>'
                '<th>Category</th>'
                '<th>Subcategory</th>'
                '<th>Location</th>'
                '<th style="text-align:right;">Qty</th>'
                '<th style="text-align:right;">Min Required</th>'
                '<th style="text-align:right;">Updated (IST)</th>'
                '</tr></thead>'
                '<tbody>' + "".join(rows_html) + '</tbody>'
                                                 '</table>'
        )

        st.markdown(
            f'<div class="inv-table-wrap">{html_table}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Low Stock")

    ts = now_ist().strftime("%d-%m-%Y__%H-%M")

    st.download_button(
        label=f"📥 Download {len(df_filtered)} Low-Stock Item(s) as Excel",
        data=buffer.getvalue(),
        file_name=f"agt_low_stock_{ts}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl6",
        use_container_width=True,
    )


# ---------------------------------------------------------
#  SECTION 7 — 📜 Audit Log (Password Protected)
# ---------------------------------------------------------
elif page == "📜   Audit Log":
    st.markdown('<div class="section-header">📜 Audit Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">'
        'Complete record of every stock change — when, what, why. '
        'Password protected.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.get("audit_authed", False):
        st.info("🔒 **Enter the admin password to view the audit log.**")

        col_pwd, col_btn = st.columns([3, 1])
        with col_pwd:
            admin_pwd = st.text_input(
                "Admin password",
                type="password",
                key="audit_pwd_input",
                placeholder="Enter admin password",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("🔓 Unlock", key="audit_unlock_btn", type="primary", use_container_width=True):
                if admin_pwd == "admin@agt2026":
                    st.session_state["audit_authed"] = True
                    st.rerun()
                else:
                    st.error("❌ Wrong admin password.")
                    st.toast("🔐 Access denied!", icon="🚨")

        st.stop()

    _, col_lock = st.columns([4, 1])
    with col_lock:
        if st.button("🔒 Lock", key="audit_lock_btn", use_container_width=True):
            st.session_state["audit_authed"] = False
            st.rerun()

    if history_collection is None:
        st.error("⚠️ History collection unavailable.")
        st.stop()

    col_load, col_info = st.columns([1, 3])

    with col_load:
        audit_load_clicked = st.button(
            "🔄 Load Audit Log",
            key="btn_audit_load",
            type="primary",
            use_container_width=True,
        )

    with col_info:
        if "audit_data" in st.session_state:
            cached_at = st.session_state.get("audit_loaded_at", "")
            st.caption(f"✔️ Data loaded · {cached_at}")

    if audit_load_clicked or "audit_data" not in st.session_state:
        try:
            rows = list(history_collection.find({}, {"_id": 0}))

            df_audit = pd.DataFrame(rows)

            if not df_audit.empty:
                df_audit["Timestamp"] = pd.to_datetime(
                    df_audit["Timestamp"], format="%d-%m-%Y %H:%M:%S", errors="coerce"
                )
                df_audit = df_audit.dropna(subset=["Timestamp"])
                df_audit = df_audit.sort_values("Timestamp", ascending=False).reset_index(drop=True)

            st.session_state["audit_data"] = df_audit
            st.session_state["audit_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M')

        except Exception as e:
            st.error(f"❌ Failed to load audit log: {e}")
            st.stop()

    df_audit = st.session_state.get("audit_data")

    if df_audit is None or df_audit.empty:
        st.info("📭 No audit entries yet. Make some changes to start logging.")
        st.stop()

    total_entries = len(df_audit)
    adds = int(df_audit[df_audit["Change"] > 0]["Change"].sum())
    rems = int(df_audit[df_audit["Change"] < 0]["Change"].sum())
    unique_items = df_audit["Item_code"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <p class="metric-label">Total Entries</p>
            <p class="metric-value primary">{total_entries}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card accent-gold">
            <div class="metric-icon">📦</div>
            <p class="metric-label">Unique Items</p>
            <p class="metric-value gold">{unique_items}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card accent-ok">
            <div class="metric-icon">🟢</div>
            <p class="metric-label">Total Added</p>
            <p class="metric-value success">+{adds:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card accent-danger">
            <div class="metric-icon">🔴</div>
            <p class="metric-label">Total Removed</p>
            <p class="metric-value danger">{rems:,}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-header" style="font-size:0.95rem; margin-bottom:0.5rem;">'
        '🔍 Filter Audit Log</div>',
        unsafe_allow_html=True,
    )

    f1, f2 = st.columns([3, 1])

    with f1:
        audit_search = st.text_input(
            "Search",
            placeholder="🔎 Search item code / name / reason…",
            key="audit_search_input",
            label_visibility="collapsed",
        )

    with f2:
        reason_options = ["All reasons"] + sorted(
            [r for r in df_audit["Reason"].dropna().unique().tolist() if str(r).strip()]
        )
        audit_reason_filter = st.selectbox(
            "Reason",
            options=reason_options,
            key="audit_reason_filter_select",
            label_visibility="collapsed",
        )

    df_view = df_audit.copy()

    if audit_search.strip():
        q = audit_search.strip().lower()
        mask = (
                df_view["Item_code"].astype(str).str.lower().str.contains(q, na=False)
                | df_view["Item_name"].astype(str).str.lower().str.contains(q, na=False)
                | df_view["Reason"].astype(str).str.lower().str.contains(q, na=False)
        )
        df_view = df_view[mask]

    if audit_reason_filter != "All reasons":
        df_view = df_view[df_view["Reason"] == audit_reason_filter]

    st.caption(
        f"Showing **{len(df_view)}** of **{len(df_audit)}** entries"
        + (f" · {len(df_audit) - len(df_view)} filtered out"
           if len(df_view) < len(df_audit) else "")
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if df_view.empty:
        st.info("🔍 No audit entries match your filters.")
    else:
        def _delta_style(v):
            try:
                v = int(v)
            except Exception:
                return ""
            if v > 0:
                return "color:#10B981; font-weight:700; text-align:right;"
            if v < 0:
                return "color:#EF4444; font-weight:700; text-align:right;"
            return "color:#6B7280; text-align:right;"


        def clean(v):
            if pd.isna(v) or str(v).lower() in ("nan", "none", "null", "nat", ""):
                return "—"
            return str(v)


        rows_html = []
        for _, r in df_view.iterrows():
            ts = r["Timestamp"].strftime("%d-%m-%Y %H:%M:%S") if pd.notna(r["Timestamp"]) else "—"
            delta = r.get("Change", 0)
            try:
                delta_str = f"+{int(delta)}" if int(delta) > 0 else str(int(delta))
            except Exception:
                delta_str = str(delta)

            rows_html.append(
                "<tr>"
                f"<td style='font-family:JetBrains Mono,monospace; font-size:0.72rem;'>{ts}</td>"
                f"<td style='font-family:JetBrains Mono,monospace; font-weight:600;'>{clean(r.get('Item_code'))}</td>"
                f"<td style='font-weight:600;'>{clean(r.get('Item_name'))}</td>"
                f"<td style='text-align:right;'>{int(r.get('Old_Qty', 0))}</td>"
                f"<td style='text-align:right;'>{int(r.get('New_Qty', 0))}</td>"
                f"<td style='{_delta_style(delta)}'>{delta_str}</td>"
                f"<td style='color:#6B7280; font-size:0.75rem;'>{clean(r.get('Reason'))}</td>"
                "</tr>"
            )

        html_table = (
                '<table class="inv-table">'
                '<thead><tr>'
                '<th>When (IST)</th>'
                '<th>Code</th>'
                '<th>Item Name</th>'
                '<th style="text-align:right;">Old</th>'
                '<th style="text-align:right;">New</th>'
                '<th style="text-align:right;">Δ</th>'
                '<th>Reason</th>'
                '</tr></thead>'
                '<tbody>' + "".join(rows_html) + '</tbody>'
                                                 '</table>'
        )

        st.markdown(
            f'<div class="inv-table-wrap">{html_table}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    buffer_a = io.BytesIO()
    with pd.ExcelWriter(buffer_a, engine="openpyxl") as writer:
        df_view.to_excel(writer, index=False, sheet_name="Audit Log")

    ts_dl = now_ist().strftime("%d-%m-%Y__%H-%M")

    st.download_button(
        label=f"📥 Download Audit Log ({len(df_view)} entries) as Excel",
        data=buffer_a.getvalue(),
        file_name=f"agt_audit_log_{ts_dl}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_audit_btn",
        use_container_width=True,
    )

# =========================================================
#  📜 AUTO SCROLL ON PAGE NAVIGATION
# =========================================================
if st.session_state.get("_last_page") != page:
    st.session_state["_last_page"] = page
    scroll_to_top(delay=150)

# =========================================================
#  🌙 LATE-NIGHT EASTER EGG
# =========================================================
_late = late_night_message()
if _late:
    st.toast(_late, icon="🌙")