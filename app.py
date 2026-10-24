# app.py
# ---------------------------------------------------------
#  STREAMLIT WEB UI — Enterprise Dashboard
#  Palette: #1F2A44 (Navy) · #E8DCC8 (Cream) · #C6A75E (Gold)
#  v43: Removed Location column from PO Requirements
#  Built with ❤️ for Kishan
# ---------------------------------------------------------
import io
import random
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -- Google Sheets Imports --
import gspread
from google.oauth2.service_account import Credentials

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
    return datetime.now(IST)


# =========================================================
#  📜 AUTO-SCROLL & UI HELPERS
# =========================================================
def auto_scroll_to(element_id: str = None, delay: int = 250):
    if element_id:
        js = f"""
        <script>
            setTimeout(function() {{
                try {{
                    var el = window.parent.document.getElementById("{element_id}");
                    if (!el) {{ el = window.parent.document.querySelector("{element_id}"); }}
                    if (el) {{ el.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }}
                }} catch (e) {{}}
            }}, {delay});
        </script>
        """
    else:
        js = f"""
        <script>
            setTimeout(function() {{
                try {{ window.parent.scrollTo({{ top: window.parent.document.body.scrollHeight, behavior: 'smooth' }}); }} catch (e) {{}}
            }}, {delay});
        </script>
        """
    components.html(js, height=0, width=0)


def scroll_to_top(delay: int = 200):
    components.html(f"""
    <script>
        setTimeout(function() {{
            try {{ window.parent.scrollTo({{ top: 0, behavior: 'smooth' }}); }} catch (e) {{}}
        }}, {delay});
    </script>
    """, height=0, width=0)


# =========================================================
#  ⚠️ LOW STOCK THRESHOLDS
# =========================================================
DEFAULT_LOW_STOCK = 100
LOW_STOCK_OVERRIDES = {"94193159L": 2500}


def low_stock_threshold(item_code: str) -> int:
    return LOW_STOCK_OVERRIDES.get(str(item_code).strip(), DEFAULT_LOW_STOCK)


def is_low_stock(item_code: str, quantity) -> bool:
    try:
        return int(quantity) < low_stock_threshold(item_code)
    except:
        return False


# =========================================================
#  🎊 UPLOAD SUCCESS ANIMATION
# =========================================================
def show_upload_success_animated(inserted: int, duplicates: int, total: int):
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    uid = int(datetime.now().timestamp() * 1000)
    st.markdown(f"""
    <style>
        @keyframes rise-{uid} {{ 0% {{ opacity: 0; transform: translateY(20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes check-draw-{uid} {{ 0% {{ stroke-dashoffset: 100; }} 100% {{ stroke-dashoffset: 0; }} }}
        @keyframes glow-{uid} {{ 0%, 100% {{ box-shadow: 0 4px 20px -8px rgba(198,167,94,0.3); }} 50% {{ box-shadow: 0 4px 30px -4px rgba(198,167,94,0.7); }} }}
    </style>
    <div style="background: linear-gradient(135deg, #FFFFFF 0%, #FAF6EC 100%); border: 1.5px solid #E8DCC8; border-left: 5px solid #C6A75E; border-radius: 14px; padding: 1.6rem 2rem; margin: 1rem 0 1.5rem 0; animation: rise-{uid} 0.6s ease-out, glow-{uid} 2.5s ease-in-out 0.6s;">
        <div style="display:flex; align-items:center; gap:16px;">
            <svg width="48" height="48" viewBox="0 0 48 48"><circle cx="24" cy="24" r="22" fill="none" stroke="#C6A75E" stroke-width="2.5"/><path d="M14 24 L21 31 L34 18" fill="none" stroke="#C6A75E" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="100" style="animation: check-draw-{uid} 0.5s ease-out forwards;"/></svg>
            <div>
                <div style="font-size:1.15rem; font-weight:700; color:#1F2A44;">Upload Complete</div>
                <div style="font-size:0.82rem; color:#6B7280;">Inventory synchronized · {timestamp}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; padding-top:1rem; border-top:1px solid #E8DCC8; margin-top:1rem;">
            <div style="text-align:center;"><div style="font-size:0.68rem; font-weight:700; color:#6B7280;">Inserted</div><div style="font-size:1.5rem; font-weight:800; color:#1F2A44;">{inserted:,}</div></div>
            <div style="text-align:center;"><div style="font-size:0.68rem; font-weight:700; color:#6B7280;">Skipped</div><div style="font-size:1.5rem; font-weight:800; color:{'#B45309' if duplicates else '#1F2A44'};">{duplicates:,}</div></div>
            <div style="text-align:center;"><div style="font-size:0.68rem; font-weight:700; color:#6B7280;">Total</div><div style="font-size:1.5rem; font-weight:800; color:#A98A44;">{total:,}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  📧 EMAIL & HISTORY HELPERS
# =========================================================
def _record_email_attempt(trigger: str, ok: bool, msg: str):
    log = st.session_state.setdefault("email_alert_log", [])
    log.insert(0, {"when": now_ist().strftime("%d-%m-%Y %H:%M:%S"), "trigger": trigger, "ok": ok, "msg": msg})
    st.session_state["email_alert_log"] = log[:20]


def collect_low_stock_alerts():
    alerts = []
    try:
        for doc in collection.find({},
                                   {"_id": 0, "Item_code": 1, "Item_name": 1, "Item_category": 1, "Item_subcategory": 1,
                                    "Location": 1, "Quantity": 1}):
            code, qty = str(doc.get("Item_code", "")).strip(), int(doc.get("Quantity", 0) or 0)
            if is_low_stock(code, qty):
                t = low_stock_threshold(code)
                alerts.append({"code": code, "name": str(doc.get("Item_name", "—")),
                               "category": str(doc.get("Item_category", "—")),
                               "subcategory": str(doc.get("Item_subcategory", "—")),
                               "location": str(doc.get("Location", "—")), "qty": qty, "threshold": t,
                               "shortfall": max(0, t - qty), "is_zero": qty == 0})
    except:
        pass
    return sorted(alerts, key=lambda a: (not a["is_zero"], -a["shortfall"]))


def maybe_send_low_stock_alert(trigger_reason: str, force: bool = False):
    alerts = collect_low_stock_alerts()
    if not alerts: return False, "No low-stock items found."
    if not force:
        last_sent = st.session_state.get("last_alert_sent_at")
        if last_sent:
            try:
                if (now_ist().replace(tzinfo=None) - datetime.strptime(last_sent,
                                                                       "%d-%m-%Y %H:%M:%S")).total_seconds() < 600:
                    return False, "Alert cooldown active (10 min)."
            except:
                pass
    ok, msg = mailer.send_low_stock_alert(alerts, trigger_reason)
    _record_email_attempt(trigger_reason, ok, msg)
    if ok: st.session_state["last_alert_sent_at"] = now_ist().strftime("%d-%m-%Y %H:%M:%S")
    return ok, msg


HISTORY_COLLECTION_NAME = "inventory_history"
try:
    history_collection = collection.database[HISTORY_COLLECTION_NAME]
except:
    history_collection = None


def log_history(item_code, item_name, old_qty, new_qty, reason):
    if history_collection:
        try:
            history_collection.insert_one(
                {"Item_code": str(item_code).strip(), "Item_name": str(item_name).strip().upper(),
                 "Old_Qty": int(old_qty), "New_Qty": int(new_qty), "Change": int(new_qty) - int(old_qty),
                 "Reason": str(reason), "Timestamp": now_ist().strftime("%d-%m-%Y %H:%M:%S")})
        except:
            pass


# =========================================================
#  😄 FUN ZONE
# =========================================================
FUN_MODE = False
WRONG_PASSWORD_LINES = ["🚨 Nice try, hacker!", "🔐 That password is so wrong.", "🕵️ Breaking in?",
                        "🧠 Tip: not 'password123'.", "🎭 Access denied.", "🛑 Reported to your Boss."]
NO_FILE_LINES = ["📁 Upload something!", "🕳️ An empty file?", "📭 Nothing here."]
ZERO_STOCK_LINES = ["😬 We're out.", "🫥 Stock: 0.", "🚫 Can't build."]


def big_order_message(c):
    if c >= 5000: return f"🚀 {c} valves?! War or market?"
    if c >= 1000: return f"💪 {c} valves — ambitious!"
    if c >= 500: return f"📈 {c} valves. Serious batch."
    return None


def late_night_message():
    h = now_ist().hour
    if 0 <= h < 5: return "🦉 Past midnight, Kishan."
    if 22 <= h <= 23: return "🌙 Late shift?"
    return None


def funny(pool): return random.choice(pool) if FUN_MODE else pool[0]


# =========================================================
#  PAGE CONFIG & CUSTOM CSS
# =========================================================
st.set_page_config(page_title="AGT Inventory", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    :root { --navy: #1F2A44; --navy-700: #2A3856; --cream: #E8DCC8; --gold: #C6A75E; --gold-700: #A98A44; --ink: #1A2332; --muted: #6B7280; --border: #E5E7EB; --white: #FFFFFF; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--ink); font-size: 15px; }
    .stApp { background: #FAFAF7; }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; height: auto !important; visibility: visible !important; pointer-events: none !important; z-index: 999999 !important; }
    header[data-testid="stHeader"] button { position: fixed !important; top: 12px !important; right: 12px !important; z-index: 999998 !important; pointer-events: auto !important; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1F2A44 0%, #18223A 100%) !important; }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1400px; }

    .hero { background: var(--navy); padding: 1.6rem 1.9rem; border-radius: 12px; margin-bottom: 1.4rem; border-left: 4px solid var(--gold); display: flex; align-items: center; justify-content: space-between; }
    .hero h1 { color: #FFFFFF; margin: 0; font-size: 1.4rem; font-weight: 700; }
    .hero p { color: rgba(255,255,255,0.72); margin: 0.35rem 0 0 0; font-size: 0.85rem; }
    .hero .badge { display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(198,167,94,0.15); color: var(--gold); padding: 0.28rem 0.7rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; margin-top: 0.85rem; border: 1px solid rgba(198,167,94,0.35); }

    .metric-card { background: var(--white); padding: 1.05rem 1.25rem; border-radius: 10px; border: 1px solid var(--border); border-top: 3px solid var(--navy); }
    .metric-label { font-size: 0.72rem; font-weight: 600; color: var(--muted); text-transform: uppercase; margin: 0; }
    .metric-value { font-size: 1.55rem; font-weight: 700; color: var(--ink); margin: 0.4rem 0 0 0; }
    .metric-value.primary { color: var(--navy); } .metric-value.gold { color: var(--gold-700); } .metric-value.danger { color: #B91C1C; } .metric-value.success { color: #047857; }

    .section-header { font-size: 1.05rem; font-weight: 700; color: var(--ink); margin: 0 0 0.3rem 0; padding-left: 0.75rem; border-left: 3px solid var(--gold); }
    .section-sub { color: var(--muted); font-size: 0.82rem; margin: 0 0 1.1rem 0.75rem; }

    .stButton > button { background: var(--navy); color: #FFFFFF; border-radius: 8px; font-weight: 600; font-size: 0.83rem; }
    .stButton > button:hover { background: var(--navy-700); border-color: var(--gold); }
    .stDownloadButton > button { background: var(--gold); color: var(--navy); border-radius: 8px; font-weight: 600; }

    .inv-table-wrap { max-height: 720px; overflow-y: auto; border-radius: 12px; border: 1px solid var(--border); background: var(--white); }
    .inv-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .inv-table thead th { position: sticky; top: 0; background: var(--navy) !important; color: #FFFFFF !important; font-size: 0.65rem !important; font-weight: 700 !important; text-transform: uppercase !important; padding: 0.75rem 0.9rem !important; text-align: left; border-bottom: 3px solid var(--gold) !important; }
    .inv-table tbody td { padding: 0.65rem 0.9rem !important; border-bottom: 1px solid #E5E7EB !important; color: var(--ink) !important; font-weight: 500; }
    .inv-table tbody tr:nth-child(even) td { background-color: #FAFBFD !important; }
    .inv-table tbody tr:hover td { background-color: rgba(198,167,94,0.10) !important; }

    div[data-testid="stToast"] { animation-duration: 0.3s, 0.5s !important; animation-delay: 0s, 5s !important; position: relative !important; overflow: hidden !important; }
    div[data-testid="stToast"]::after { content: "" !important; position: absolute !important; left: 0 !important; bottom: 0 !important; height: 2px !important; background: linear-gradient(90deg, #C6A75E 0%, #A98A44 100%) !important; animation: toast-countdown 5s linear forwards !important; }
    @keyframes toast-countdown { 0% { width: 100%; } 100% { width: 0%; } }
</style>
""", unsafe_allow_html=True)

# =========================================================
#  🧭 NAVIGATION STATE
# =========================================================
DEFAULT_PAGE = "📋   View Inventory"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = DEFAULT_PAGE

# =========================================================
#  SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(
        '<div style="display:flex; align-items:center; gap:12px; padding:6px 4px 24px 4px;"><div style="width:46px; height:46px; border-radius:12px; background:linear-gradient(135deg,#E8D4A5 0%,#C6A75E 100%); display:flex; align-items:center; justify-content:center; font-size:22px;">📦</div><div><div style="font-size:0.98rem; font-weight:700; color:#FFFFFF;">Inventory Hub</div><div style="font-size:0.78rem; color:#C6A75E;">AGT Inventory Management</div></div></div>',
        unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.72rem; color:#C6A75E; font-weight:700; margin:0 0 14px 12px; text-transform:uppercase;">Admin</div>',
        unsafe_allow_html=True)
    if st.button("📜   Audit Log", key="nav_audit", use_container_width=True,
                 type=("primary" if st.session_state["current_page"] == "📜   Audit Log" else "secondary")):
        st.session_state["current_page"] = "📜   Audit Log"
        st.rerun()

    st.markdown('<div style="margin:24px 12px 14px 12px; border-top:1px solid rgba(198,167,94,0.3);"></div>',
                unsafe_allow_html=True)

    _main_items = [
        "📋   View Inventory",
        "⚠️   Low Stock Items",
        "📤   Update from Excel",
        "⚙️   Update by DN-60",
        "📊   Check Production",
        "🧮   Required Items",
        "📋   PO Requirements",
    ]

    for _item in _main_items:
        if st.button(_item, key=f"nav_{_item}", use_container_width=True,
                     type=("primary" if st.session_state["current_page"] == _item else "secondary")):
            st.session_state["current_page"] = _item
            st.rerun()

    st.markdown(
        '<div style="margin-top:32px; border-top:1px solid rgba(198,167,94,0.18); padding-top:18px; font-size:0.68rem; color:#94A3B8; display:flex; justify-content:space-between;"><div>🟢 Online</div><div>© 2026 AASHDHA GLOBAL TECH</div></div>',
        unsafe_allow_html=True)

page = st.session_state["current_page"]

# =========================================================
#  HERO HEADER & STATS
# =========================================================
st.markdown(
    f'<div class="hero"><div><h1>AGT Inventory Management System</h1><p>DN-60 Valve Production Tracker</p><span class="badge">Live · {now_ist().strftime("%d %b %Y, %H:%M")}</span></div></div>',
    unsafe_allow_html=True)

try:
    total_items = collection.count_documents({})
    total_qty_pipeline = list(collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$Quantity"}}}]))
    total_qty = total_qty_pipeline[0]["total"] if total_qty_pipeline else 0
    _all_items = list(collection.find({}, {"_id": 0, "Item_code": 1, "Quantity": 1}))
    low_stock = sum(1 for it in _all_items if is_low_stock(it.get("Item_code", ""), it.get("Quantity", 0)))
except:
    total_items, low_stock, total_qty = 0, 0, 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.markdown(
    f'<div class="metric-card"><div style="font-size:1rem; margin-bottom:0.35rem;">📦</div><p class="metric-label">Item Types</p><p class="metric-value primary">{total_items}</p></div>',
    unsafe_allow_html=True)
with c2: st.markdown(
    f'<div class="metric-card accent-ok"><div style="font-size:1rem; margin-bottom:0.35rem;">🔢</div><p class="metric-label">Total Quantity</p><p class="metric-value success">{total_qty:,}</p></div>',
    unsafe_allow_html=True)
with c3: st.markdown(
    f'<div class="metric-card {"accent-danger" if low_stock > 0 else "accent-ok"}"><div style="font-size:1rem; margin-bottom:0.35rem;">⚠️</div><p class="metric-label">Low Stock Items</p><p class="metric-value {"danger" if low_stock > 0 else "success"}">{low_stock}</p></div>',
    unsafe_allow_html=True)
with c4: st.markdown(
    f'<div class="metric-card accent-gold"><div style="font-size:1rem; margin-bottom:0.35rem;">🎯</div><p class="metric-label">DN-60 Parts</p><p class="metric-value gold">{len(DN60_PART_NUM)}</p></div>',
    unsafe_allow_html=True)
with c5: st.markdown(
    f'<div class="metric-card"><div style="font-size:1rem; margin-bottom:0.35rem;">🕐</div><p class="metric-label">Last Checked</p><p class="metric-value" style="font-size:1.05rem;">{now_ist().strftime("%d-%m-%Y %H:%M")}</p></div>',
    unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
#  ROUTED CONTENT
# =========================================================

# ---------------------------------------------------------
#  📋 NEW: PO REQUIREMENTS (GOOGLE SHEETS)
# ---------------------------------------------------------
if page == "📋   PO Requirements":
    st.markdown('<div class="section-header">📋 PO Pending Requirements</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Fetches Pending orders from Google Sheets and checks stock availability against MongoDB.</div>',
        unsafe_allow_html=True)

    if st.button("🔄 Fetch & Analyze Pending POs", type="primary", use_container_width=True):
        with st.spinner("Connecting to Google Sheets securely..."):
            try:
                # 1. Authenticate using the Service Account secrets
                scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
                creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
                client = gspread.authorize(creds)

                # 2. Open the sheet using the ID from secrets
                sheet_id = st.secrets["SHEET_ID"]
                sheet = client.open_by_key(sheet_id).sheet1

                # 3. Fetch data into DataFrame
                data = sheet.get_all_records()
                if not data:
                    st.warning("⚠️ Sheet is empty or no headers found.")
                    st.stop()

                df_sheet = pd.DataFrame(data)

                # Check if required columns exist
                required_cols = ["Item Code", "Item Qty", "Delivery Status"]
                missing_cols = [c for c in required_cols if c not in df_sheet.columns]
                if missing_cols:
                    st.error(f"❌ Missing columns in Google Sheet: {', '.join(missing_cols)}")
                    st.stop()

                # 4. Filter for "Pending" status (case-insensitive)
                df_pending = df_sheet[
                    df_sheet["Delivery Status"].astype(str).str.strip().str.lower() == "pending"].copy()

                if df_pending.empty:
                    st.success("🎉 No pending items found in the Google Sheet!")
                    st.stop()

                # Ensure 'Item Qty' is numeric
                df_pending["Item Qty"] = pd.to_numeric(df_pending["Item Qty"], errors="coerce").fillna(0).astype(int)

                # 5. Cross-reference with MongoDB
                report_rows = []
                total_req = 0
                total_short = 0
                items_to_order = 0

                for _, row in df_pending.iterrows():
                    # --- CLEAN & FORMAT ITEM CODE ---
                    raw_code = str(row["Item Code"]).strip()

                    # Handle scientific notation (e.g., 3.01E+11)
                    if "E+" in raw_code:
                        try:
                            raw_code = str(int(float(raw_code)))
                        except:
                            pass

                    # Append 'L' if it doesn't already end with 'L' or 'I'
                    if not (raw_code.endswith('L') or raw_code.endswith('I')):
                        item_code = raw_code + "L"
                    else:
                        item_code = raw_code
                    # --------------------------------

                    req_qty = int(row["Item Qty"])
                    total_req += req_qty

                    # Query DB for this item
                    db_item = collection.find_one({"Item_code": item_code})

                    if db_item:
                        stock = int(db_item.get("Quantity", 0))
                        item_name = db_item.get("Item_name", "—")
                    else:
                        stock = 0
                        item_name = "⚠️ Not in DB"

                    shortfall = max(0, req_qty - stock)

                    if shortfall > 0:
                        total_short += shortfall
                        items_to_order += 1

                    report_rows.append({
                        "PO No": row.get("PO No", "—"),
                        "PO Date": row.get("PO Date", "—"),
                        "Item Code": item_code,
                        "Item Name": item_name,
                        "Req Qty": req_qty,
                        "Stock Available": stock,
                        "Shortfall": shortfall,
                        "Status": "🛒 ORDER" if shortfall > 0 else "✅ OK"
                    })

                df_report = pd.DataFrame(report_rows)

                # 6. Display Summary Metrics
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f'<div class="metric-card"><p class="metric-label">Total Pending Qty</p><p class="metric-value primary">{total_req:,}</p></div>',
                        unsafe_allow_html=True)
                with c2:
                    st.markdown(
                        f'<div class="metric-card {"accent-danger" if total_short > 0 else "accent-ok"}"><p class="metric-label">Total Shortfall</p><p class="metric-value {"danger" if total_short > 0 else "success"}">{total_short:,}</p></div>',
                        unsafe_allow_html=True)
                with c3:
                    st.markdown(
                        f'<div class="metric-card {"accent-warn" if items_to_order > 0 else "accent-ok"}"><p class="metric-label">Items to Order</p><p class="metric-value {"warn" if items_to_order > 0 else "success"}">{items_to_order}</p></div>',
                        unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)


                # 7. Display HTML Table
                def clean(v):
                    return str(v) if pd.notna(v) else "—"


                rows_html = []
                for _, r in df_report.iterrows():
                    badge = "background:#FEE2E2; color:#991B1B;" if "ORDER" in r[
                        "Status"] else "background:#D1FAE5; color:#065F46;"
                    shortfall_color = "color:#DC2626; font-weight:700;" if r["Shortfall"] > 0 else "color:#6B7280;"

                    rows_html.append(
                        "<tr>"
                        f"<td>{clean(r['PO No'])}</td>"
                        f"<td>{clean(r['PO Date'])}</td>"
                        f"<td style='font-family:JetBrains Mono,monospace; font-weight:600;'>{clean(r['Item Code'])}</td>"
                        f"<td>{clean(r['Item Name'])}</td>"
                        f"<td style='text-align:right;'>{r['Req Qty']}</td>"
                        f"<td style='text-align:right;'>{r['Stock Available']}</td>"
                        f"<td style='text-align:right; {shortfall_color}'>{r['Shortfall']}</td>"
                        f"<td style='text-align:center;'><span style='padding:4px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; {badge}'>{r['Status']}</span></td>"
                        "</tr>"
                    )

                html_table = f"""
                <div class="inv-table-wrap">
                    <table class="inv-table">
                        <thead><tr>
                            <th>PO No</th><th>PO Date</th><th>Item Code</th><th>Item Name</th>
                            <th style="text-align:right;">Req Qty</th><th style="text-align:right;">Stock</th>
                            <th style="text-align:right;">Shortfall</th><th style="text-align:center;">Status</th>
                        </tr></thead>
                        <tbody>{''.join(rows_html)}</tbody>
                    </table>
                </div>
                """
                st.markdown(html_table, unsafe_allow_html=True)

                # 8. Download Button
                st.markdown("<br>", unsafe_allow_html=True)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_report.to_excel(writer, index=False, sheet_name="PO Requirements")

                st.download_button(
                    label="📥 Download Report as Excel",
                    data=buffer.getvalue(),
                    file_name=f"PO_Requirements_{now_ist().strftime('%d-%m-%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except gspread.exceptions.APIError as e:
                st.error(
                    f"❌ Google API Error: Make sure the service account email is shared on the sheet. Details: {e}")
            except Exception as e:
                st.error(f"❌ Failed to fetch sheet: {e}")

# ---------------------------------------------------------
#  SECTION 1 — Upload Excel & Update
# ---------------------------------------------------------
elif page == "📤   Update from Excel":
    st.markdown('<div class="section-header">📤 Update Inventory from Excel</div>', unsafe_allow_html=True)
    st.warning("⚠️ **Warning:** This will DROP the existing collection.")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        password1 = st.text_input("🔒 Password", type="password", key="pwd1")
    with col_b:
        uploaded_file = st.file_uploader("📁 Choose Item_Sheet.xlsx", type=["xlsx"])
    st.markdown("<br>", unsafe_allow_html=True)
    progress_ph = st.empty()
    result_ph = st.empty()

    if st.button("🚀 Update Inventory", type="primary", use_container_width=True):
        if password1.lower() == "kishan":
            st.success("👑 Welcome back, boss.")
        elif password1.lower() != "updatek":
            st.error(funny(WRONG_PASSWORD_LINES)); st.toast("🔐 Access denied!", icon="🚨")
        elif uploaded_file is None:
            st.warning(funny(NO_FILE_LINES))
        else:
            try:
                with progress_ph.container():
                    st.markdown('<div id="upload-progress-anchor"></div>', unsafe_allow_html=True)
                    st.info("⏳ Upload in progress…")
                auto_scroll_to("upload-progress-anchor", delay=150)

                with st.spinner("Updating..."):
                    ops.download_excel_data('old')
                    collection.drop()
                    df = pd.read_excel(uploaded_file)
                    inserted, duplicates = 0, 0
                    progress = st.progress(0)

                    for index, row in df.iterrows():
                        data = row.to_dict()
                        data["_id"] = str(data["Item_code"]).strip()
                        data["Item_code"] = str(data["Item_code"]).strip()
                        data["Item_name"] = str(data.get("Item_name", "")).strip().upper()
                        data["Quantity"] = int(data["Quantity"])
                        data["Updated_date"] = now_ist().strftime("%d-%m-%Y %H:%M:%S")
                        try:
                            collection.insert_one(data)
                            log_history(data["Item_code"], data["Item_name"], 0, int(data["Quantity"]), "Excel upload")
                            inserted += 1
                        except:
                            duplicates += 1
                        progress.progress((index + 1) / len(df))

                progress_ph.empty()
                with result_ph.container():
                    st.markdown('<div id="upload-success-anchor"></div>', unsafe_allow_html=True)
                    show_upload_success_animated(inserted, duplicates, len(df))
                auto_scroll_to("upload-success-anchor", delay=400)
                maybe_send_low_stock_alert("Excel re-upload")
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

# ---------------------------------------------------------
#  SECTION 2 — Update by DN-60
# ---------------------------------------------------------
elif page == "⚙️   Update by DN-60":
    st.markdown('<div class="section-header">⚙️ Update by DN-60 Valve Count</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns([2, 1])
    with col_a:
        password2 = st.text_input("🔒 Password", type="password", key="pwd2")
    with col_b:
        dn60_count = st.number_input("🔧 Number of valves", min_value=1, value=10)
    st.markdown("<br>", unsafe_allow_html=True)
    dn60_result_ph = st.empty()

    if st.button("⚙️ Build Valves", type="primary", use_container_width=True):
        if password2.lower() == "kishan":
            st.success("👑 Right away, boss.")
        elif password2.lower() != "dn60k":
            st.error(funny(WRONG_PASSWORD_LINES)); st.toast("🔐 Access denied!", icon="🚨")
        else:
            big_msg = big_order_message(dn60_count)
            if big_msg: st.info(big_msg)
            try:
                errors = []
                for part_num, per_valve in DN60_PART_NUM.items():
                    doc = collection.find_one({"Item_code": part_num})
                    if not doc: errors.append(f"Part {part_num} not found"); continue
                    if int(doc['Quantity']) < dn60_count * per_valve: errors.append(
                        f"[{part_num}] need {dn60_count * per_valve}, have {int(doc['Quantity'])}")

                if errors:
                    st.error("❌ Insufficient stock:");
                    [st.write(f"• {e}") for e in errors]
                else:
                    ops.download_excel_data('old')
                    today = now_ist().strftime("%d-%m-%Y")
                    rows = []
                    for part_num in sorted(DN60_PART_NUM, key=int):
                        per_valve = DN60_PART_NUM[part_num]
                        doc = collection.find_one({"Item_code": part_num})
                        old_c, new_c = int(doc['Quantity']), int(doc['Quantity']) - (dn60_count * per_valve)
                        collection.update_one({"Item_code": part_num},
                                              {"$set": {"Quantity": new_c, "Updated_date": today}})
                        log_history(part_num, doc['Item_name'], old_c, new_c, f"Build {dn60_count} DN-60")
                        rows.append(
                            {"#": part_num, "Item Name": doc['Item_name'], "Old": old_c, "Used": dn60_count * per_valve,
                             "New": new_c})

                    with dn60_result_ph.container():
                        st.markdown('<div id="dn60-result-anchor"></div>', unsafe_allow_html=True)
                        st.success(f"✅ Stock updated for building **{dn60_count}** valves!")
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    auto_scroll_to("dn60-result-anchor", delay=350)
                    maybe_send_low_stock_alert(f"DN-60 build ({dn60_count})")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

# ---------------------------------------------------------
#  SECTION 3 — Check Production
# ---------------------------------------------------------
elif page == "📊   Check Production":
    st.markdown('<div class="section-header">📊 DN-60 Production Capacity</div>', unsafe_allow_html=True)
    prod_result_ph = st.empty()
    if st.button("🔄 Check Capacity", type="primary", use_container_width=True):
        try:
            limits, available, part_names = {}, {}, {}
            for part, qty_per in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                stock = int(item.get("Quantity", 0)) if item else 0
                limits[part], available[part], part_names[part] = stock // qty_per, stock, item.get("Item_name",
                                                                                                    f"Part {part}") if item else f"Part {part} (not found)"

            max_valves, limiting_part = min(limits.values()), min(limits, key=limits.get)
            if available[limiting_part] == 0: st.toast(funny(ZERO_STOCK_LINES), icon="😬")

            with prod_result_ph.container():
                st.markdown('<div id="prod-result-anchor"></div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(
                    f'<div class="metric-card"><p class="metric-label">Max Valves</p><p class="metric-value gold">{max_valves}</p></div>',
                    unsafe_allow_html=True)
                with c2: st.markdown(
                    f'<div class="metric-card"><p class="metric-label">Limiting Part</p><p class="metric-value warn" style="font-size:1rem;">{part_names[limiting_part]}</p></div>',
                    unsafe_allow_html=True)
                with c3: st.markdown(
                    f'<div class="metric-card"><p class="metric-label">Stock of Limiting Part</p><p class="metric-value danger">{available[limiting_part]}</p></div>',
                    unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                rows = [{"Part": p, "Part Name": part_names[p], "Stock": available[p], "Per Valve": DN60_PART_NUM[p],
                         "Can Make": limits[p], "Status": "⚠️ LIMITING" if p == limiting_part else "✅ OK"} for p in
                        sorted(DN60_PART_NUM, key=int)]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.info(
                    f"**Bottleneck:** {part_names[limiting_part]} — need **{DN60_PART_NUM[limiting_part]}/valve**, have **{available[limiting_part]}**")
            auto_scroll_to("prod-result-anchor", delay=350)
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 4 — Required Items
# ---------------------------------------------------------
elif page == "🧮   Required Items":
    st.markdown('<div class="section-header">🧮 Parts Required for Target Quantity</div>', unsafe_allow_html=True)
    target = st.number_input("🎯 Target number of DN-60 valves", min_value=1, value=100)
    req_result_ph = st.empty()
    if st.button("🧮 Calculate", type="primary", use_container_width=True):
        try:
            rows, total_short = [], 0
            for part, per in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                stock = int(item.get("Quantity", 0)) if item else 0
                shortfall = max(0, per * target - stock)
                if shortfall > 0: total_short += 1
                rows.append({"Part": part,
                             "Part Name": item.get("Item_name", f"Part {part}") if item else f"Part {part} (not found)",
                             "Per": per, "Stock": stock, "Needed": per * target, "Order": shortfall,
                             "Status": "🛒 ORDER" if shortfall > 0 else "✅ OK"})

            with req_result_ph.container():
                st.markdown('<div id="req-result-anchor"></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(
                        f'<div class="metric-card"><p class="metric-label">Target</p><p class="metric-value gold">{target}</p></div>',
                        unsafe_allow_html=True)
                with c2:
                    st.markdown(
                        f'<div class="metric-card"><p class="metric-label">Parts to Order</p><p class="metric-value danger">{total_short}</p></div>',
                        unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=600)

                if total_short == 0:
                    st.success("✅ You have enough stock!")
                else:
                    st.warning(f"🛒 **ORDER LIST:** — {total_short} parts to order.")
                    for r in [r for r in rows if r["Order"] > 0]:
                        st.write(f"• **{r['Part Name']}** → order **{r['Order']}** nos")
            auto_scroll_to("req-result-anchor", delay=350)
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 5 — View Inventory
# ---------------------------------------------------------
elif page == "📋   View Inventory":
    if st.session_state.pop("clear_inv_filters", False):
        st.session_state["inv_search"] = ""
        st.session_state["inv_category"] = "All"
        st.session_state["inv_subcategory"] = "All"

    col_load, col_info = st.columns([1, 3])
    with col_load:
        load_clicked = st.button("🔄 Load Inventory", type="primary", use_container_width=True)
    with col_info:
        if "inv_data" in st.session_state: st.caption(f"✔️ Data loaded · {st.session_state.get('inv_loaded_at', '')}")

    if load_clicked or "inv_data" not in st.session_state:
        try:
            data = list(collection.find({}, {"_id": 0, "Item_code": 1, "Item_name": 1, "Item_category": 1,
                                             "Item_subcategory": 1, "Location": 1, "Quantity": 1,
                                             "Updated_date": 1}).sort("Item_code", 1))
            if not data: st.warning("⚠️ Inventory is empty."); st.session_state.pop("inv_data", None); st.stop()
            df = pd.DataFrame(data)
            df["Quantity"] = df["Quantity"].astype(int)
            st.session_state["inv_data"] = df
            st.session_state["inv_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M')
        except Exception as e:
            st.error(f"❌ Failed to load: {e}"); st.stop()

    df = st.session_state.get("inv_data")
    if df is None or df.empty: st.info("Click Load Inventory."); st.stop()

    st.markdown("<br>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([3, 1, 1])
    with fc1:
        search_text = st.text_input("Search", placeholder="🔎 Try: O-RING, BOLT, CIRCLIP, or a code like 94181553L",
                                    key="inv_search", label_visibility="collapsed")
    with fc2:
        category_opts = ["All"] + sorted([c for c in df["Item_category"].dropna().unique().tolist() if str(c).strip()])
        if st.session_state.get("inv_category") not in category_opts: st.session_state["inv_category"] = "All"
        selected_category = st.selectbox("Category", category_opts, key="inv_category", label_visibility="collapsed")
    with fc3:
        sub_pool = df["Item_subcategory"].dropna().unique().tolist() if selected_category == "All" else df.loc[
            df["Item_category"] == selected_category, "Item_subcategory"].dropna().unique().tolist()
        subcategory_opts = ["All"] + sorted([s for s in sub_pool if str(s).strip()])
        if st.session_state.get("inv_subcategory") not in subcategory_opts: st.session_state["inv_subcategory"] = "All"
        selected_subcategory = st.selectbox("Subcategory", subcategory_opts, key="inv_subcategory",
                                            label_visibility="collapsed")

    filtered = df.copy()
    if search_text.strip(): filtered = filtered[
        filtered["Item_name"].astype(str).str.lower().str.contains(search_text.strip().lower(), na=False) | filtered[
            "Item_code"].astype(str).str.lower().str.contains(search_text.strip().lower(), na=False)]
    if selected_category != "All": filtered = filtered[filtered["Item_category"] == selected_category]
    if selected_subcategory != "All": filtered = filtered[filtered["Item_subcategory"] == selected_subcategory]

    sc1, sc2 = st.columns([4, 1])
    with sc1:
        st.caption(f"Showing **{len(filtered)}** of **{len(df)}** items")
    with sc2:
        if len(filtered) < len(df):
            if st.button("🧹 Clear", key="clear_filters", use_container_width=True): st.session_state[
                "clear_inv_filters"] = True; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("🔍 No items match.")
    else:
        display_df = filtered.copy().fillna("—").astype(str).replace(
            {"nan": "—", "NaN": "—", "None": "—", "none": "—", "NaT": "—", "": "—"})
        display_df = display_df.rename(
            columns={"Item_code": "Code", "Item_name": "Item Name", "Item_category": "Category",
                     "Item_subcategory": "Subcategory", "Quantity": "Qty", "Updated_date": "Updated (IST)"})
        st.markdown(
            f'<div class="inv-table-wrap">{display_df.to_html(index=False, classes="inv-table", escape=False, border=0)}</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header" style="font-size:0.95rem;">⚡ Quick Stock Adjustment</div>',
                unsafe_allow_html=True)

    adj_progress_ph = st.empty()
    flash_ph = st.empty()

    if st.session_state.pop("scroll_to_adj_flash", False): auto_scroll_to("adj-flash-anchor", delay=250)

    _flash = st.session_state.pop("adj_flash", None)
    if _flash:
        with flash_ph.container():
            st.markdown('<div id="adj-flash-anchor"></div>', unsafe_allow_html=True)
            if _flash["status"] == "ok":
                st.markdown(
                    f'<div style="background: #ECFDF5; border: 1.5px solid #059669; border-left: 5px solid #047857; padding: 0.9rem 1.15rem; border-radius: 10px;"><div style="font-weight:700; color:#065F46;">✅ Stock Updated Successfully</div><div style="color:#047857; font-size:0.88rem; margin-top:4px;"><span style="font-family:monospace; font-weight:700;">{_flash["code"]}</span> — {_flash["name"]}<br>Qty: {_flash["old"]} → <strong>{_flash["new"]}</strong> ({_flash["diff"]})<br>Reason: {_flash["reason"]}</div></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#EFF6FF; border:1.5px solid #3B82F6; padding:0.85rem 1.1rem; border-radius:10px; color:#1E40AF;">ℹ️ No change — <code>{_flash["code"]}</code> is still {_flash["new"]}.</div>',
                    unsafe_allow_html=True)

    _flash_err = st.session_state.pop("adj_flash_err", None)
    if _flash_err: st.markdown(
        f'<div style="background:#FEF2F2; border:1.5px solid #DC2626; padding:0.85rem 1.1rem; border-radius:10px; color:#991B1B;">🚨 {_flash_err}</div>',
        unsafe_allow_html=True)

    if not filtered.empty:
        adj_c1, adj_c2, adj_c3 = st.columns([1.2, 3, 1.2])
        with adj_c1:
            adj_pwd = st.text_input("🔒 Password", type="password", key="adj_pwd")
        with adj_c2:
            adj_item = st.selectbox("Item", ["— Select item —"] + filtered["Item_code"].astype(str).tolist(),
                                    key="adj_item")
        _current_qty = int(
            collection.find_one({"Item_code": adj_item}).get("Quantity", 0)) if adj_item != "— Select item —" else 0
        with adj_c3:
            adj_new_qty = st.number_input("Current Stock", min_value=0, max_value=10000000, value=_current_qty, step=1,
                                          key=f"adj_new_qty_{adj_item}")
        adj_reason = st.text_area("📝 Reason (required)", key="adj_reason_input", height=80, max_chars=300)

        if st.button("💾 Update Stock", type="primary", use_container_width=True):
            if adj_pwd.lower() not in ("updatek", "kishan"):
                st.session_state["adj_flash_err"] = funny(WRONG_PASSWORD_LINES);
                st.session_state.pop("inv_data", None);
                st.rerun()
            elif adj_item == "— Select item —":
                st.session_state["adj_flash_err"] = "Please select an item first.";
                st.session_state.pop("inv_data", None);
                st.rerun()
            elif not adj_reason.strip():
                st.session_state["adj_flash_err"] = "⚠️ Please enter a reason.";
                st.session_state.pop("inv_data", None);
                st.rerun()
            else:
                with adj_progress_ph.container():
                    st.markdown('<div id="adj-progress-anchor"></div>', unsafe_allow_html=True); st.info(
                        "⏳ Updating stock…")
                auto_scroll_to("adj-progress-anchor", delay=150)

                doc = collection.find_one({"Item_code": adj_item})
                old_qty, new_qty = int(doc.get("Quantity", 0)), int(adj_new_qty)
                collection.update_one({"Item_code": adj_item}, {
                    "$set": {"Quantity": new_qty, "Updated_date": now_ist().strftime("%d-%m-%Y %H:%M:%S")}})
                log_history(adj_item, doc.get("Item_name", ""), old_qty, new_qty, adj_reason.strip())

                st.session_state["adj_flash"] = {"code": adj_item, "name": doc.get("Item_name", ""), "old": old_qty,
                                                 "new": new_qty,
                                                 "diff": f"+{new_qty - old_qty}" if new_qty > old_qty else (
                                                     f"{new_qty - old_qty}" if new_qty < old_qty else "±0"),
                                                 "reason": adj_reason.strip(),
                                                 "status": "ok" if new_qty != old_qty else "same"}
                if is_low_stock(adj_item, new_qty): maybe_send_low_stock_alert(f"Adjust {adj_item}")
                st.session_state.pop("adj_reason_input", None);
                st.session_state.pop("inv_data", None)
                st.session_state["scroll_to_adj_flash"] = True
                time.sleep(1)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Current Stock")
    st.download_button(label=f"📥 Download Full Inventory ({len(df)} items)", data=buffer.getvalue(),
                       file_name=f"agt_full_inventory_{now_ist().strftime('%d-%m-%Y__%H-%M')}.xlsx",
                       use_container_width=True)

# ---------------------------------------------------------
#  SECTION 6 — Low Stock Items
# ---------------------------------------------------------
elif page == "⚠️   Low Stock Items":
    st.markdown('<div class="section-header">⚠️ Low Stock Items</div>', unsafe_allow_html=True)
    col_load, col_info = st.columns([1, 3])
    with col_load:
        low_load_clicked = st.button("🔄 Load Low Stock", type="primary", use_container_width=True)
    with col_info:
        if "low_data" in st.session_state: st.caption(f"✔️ Data loaded · {st.session_state.get('low_loaded_at', '')}")

    _LOW_CACHE_VERSION = 3
    if low_load_clicked or "low_data" not in st.session_state or st.session_state.get(
            "low_cache_version") != _LOW_CACHE_VERSION:
        try:
            _all = list(collection.find({}, {"_id": 0, "Item_code": 1, "Item_name": 1, "Item_category": 1,
                                             "Item_subcategory": 1, "Location": 1, "Quantity": 1, "Updated_date": 1}))
            df_all = pd.DataFrame(_all)
            if not df_all.empty:
                df_all["Quantity"] = df_all["Quantity"].astype(int)
                df = df_all[df_all.apply(lambda r: is_low_stock(r["Item_code"], r["Quantity"]), axis=1)].copy()
                df["Threshold"] = df["Item_code"].apply(low_stock_threshold)
                df = df.sort_values("Quantity", ascending=True).reset_index(drop=True)
            else:
                df = pd.DataFrame()
            st.session_state["low_data"] = df;
            st.session_state["low_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M');
            st.session_state["low_cache_version"] = _LOW_CACHE_VERSION
        except Exception as e:
            st.error(f"❌ Failed: {e}"); st.stop()

    df_low = st.session_state.get("low_data")
    if df_low is None or df_low.empty: st.success("🎉 No items are below thresholds!"); st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div style="background:#FEF3C7; border:2px solid #F59E0B; border-left:6px solid #D97706; border-radius:12px; padding:1.1rem 1.35rem;"><div style="font-size:1.3rem;">⚠️</div><p style="font-size:0.75rem; font-weight:700; color:#92400E; margin:0;">Low Stock Items</p><p style="font-size:1.9rem; font-weight:800; color:#B45309; margin:0.45rem 0 0 0;">{len(df_low)}</p></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div style="background:#FEE2E2; border:2px solid #EF4444; border-left:6px solid #DC2626; border-radius:12px; padding:1.1rem 1.35rem;"><div style="font-size:1.3rem;">🚫</div><p style="font-size:0.75rem; font-weight:700; color:#991B1B; margin:0;">Out of Stock (0)</p><p style="font-size:1.9rem; font-weight:800; color:#B91C1C; margin:0.45rem 0 0 0;">{int((df_low["Quantity"] == 0).sum())}</p></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    search_low = st.text_input("Search", placeholder="🔎 Filter by item name or code…", key="low_search",
                               label_visibility="collapsed")
    df_filtered = df_low.copy()
    if search_low.strip(): df_filtered = df_filtered[
        df_filtered["Item_name"].astype(str).str.lower().str.contains(search_low.strip().lower(), na=False) |
        df_filtered["Item_code"].astype(str).str.lower().str.contains(search_low.strip().lower(), na=False)]

    st.caption(f"Showing **{len(df_filtered)}** of **{len(df_low)}** low-stock items")
    st.markdown("<br>", unsafe_allow_html=True)
    if df_filtered.empty:
        st.info("🔍 No items match.")
    else:
        rows_html = [
            f"<tr><td>{r.get('Item_code', '—')}</td><td>{r.get('Item_name', '—')}</td><td>{r.get('Item_category', '—')}</td><td>{r.get('Location', '—')}</td><td style='text-align:right;'>{int(r.get('Quantity', 0))}</td><td style='text-align:right;'>{int(r.get('Threshold', 100))}</td><td style='text-align:right;'>{r.get('Updated_date', '—')}</td></tr>"
            for _, r in df_filtered.iterrows()]
        html_table = f'<div class="inv-table-wrap"><table class="inv-table"><thead><tr><th>Code</th><th>Item Name</th><th>Category</th><th>Location</th><th style="text-align:right;">Qty</th><th style="text-align:right;">Min</th><th style="text-align:right;">Updated</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
        st.markdown(html_table, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Low Stock")
    st.download_button(label=f"📥 Download Low-Stock Items", data=buffer.getvalue(),
                       file_name=f"agt_low_stock_{now_ist().strftime('%d-%m-%Y__%H-%M')}.xlsx",
                       use_container_width=True)

# ---------------------------------------------------------
#  SECTION 7 — Audit Log
# ---------------------------------------------------------
elif page == "📜   Audit Log":
    st.markdown('<div class="section-header">📜 Audit Log</div>', unsafe_allow_html=True)
    if not st.session_state.get("audit_authed", False):
        st.info("🔒 **Enter admin password.**")
        col_pwd, col_btn = st.columns([3, 1])
        with col_pwd:
            admin_pwd = st.text_input("Admin password", type="password", label_visibility="collapsed")
        with col_btn:
            if st.button("🔓 Unlock", type="primary", use_container_width=True):
                if admin_pwd == "admin@agt2026":
                    st.session_state["audit_authed"] = True; st.rerun()
                else:
                    st.error("❌ Wrong password."); st.toast("🔐 Access denied!", icon="🚨")
        st.stop()

    _, col_lock = st.columns([4, 1])
    with col_lock:
        if st.button("🔒 Lock", use_container_width=True): st.session_state["audit_authed"] = False; st.rerun()

    if history_collection is None: st.error("⚠️ History unavailable."); st.stop()

    col_load, col_info = st.columns([1, 3])
    with col_load:
        audit_load_clicked = st.button("🔄 Load Audit Log", type="primary", use_container_width=True)
    with col_info:
        if "audit_data" in st.session_state: st.caption(
            f"✔️ Data loaded · {st.session_state.get('audit_loaded_at', '')}")

    if audit_load_clicked or "audit_data" not in st.session_state:
        try:
            rows = list(history_collection.find({}, {"_id": 0}))
            df_audit = pd.DataFrame(rows)
            if not df_audit.empty:
                df_audit["Timestamp"] = pd.to_datetime(df_audit["Timestamp"], format="%d-%m-%Y %H:%M:%S",
                                                       errors="coerce")
                df_audit = df_audit.dropna(subset=["Timestamp"]).sort_values("Timestamp", ascending=False).reset_index(
                    drop=True)
            st.session_state["audit_data"] = df_audit;
            st.session_state["audit_loaded_at"] = now_ist().strftime('%d-%m-%Y %H:%M')
        except Exception as e:
            st.error(f"❌ Failed: {e}"); st.stop()

    df_audit = st.session_state.get("audit_data")
    if df_audit is None or df_audit.empty: st.info("📭 No entries yet."); st.stop()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card"><p class="metric-label">Total Entries</p><p class="metric-value primary">{len(df_audit)}</p></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="metric-card accent-gold"><p class="metric-label">Unique Items</p><p class="metric-value gold">{df_audit["Item_code"].nunique()}</p></div>',
            unsafe_allow_html=True)
    with c3:
        st.markdown(
            f'<div class="metric-card accent-ok"><p class="metric-label">Total Added</p><p class="metric-value success">+{int(df_audit[df_audit["Change"] > 0]["Change"].sum()):,}</p></div>',
            unsafe_allow_html=True)
    with c4:
        st.markdown(
            f'<div class="metric-card accent-danger"><p class="metric-label">Total Removed</p><p class="metric-value danger">{int(df_audit[df_audit["Change"] < 0]["Change"].sum()):,}</p></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2 = st.columns([3, 1])
    with f1:
        audit_search = st.text_input("Search", placeholder="🔎 Search item / reason…", key="audit_search_input",
                                     label_visibility="collapsed")
    with f2:
        audit_reason_filter = st.selectbox("Reason", ["All reasons"] + sorted(
            [r for r in df_audit["Reason"].dropna().unique().tolist() if str(r).strip()]), label_visibility="collapsed")

    df_view = df_audit.copy()
    if audit_search.strip(): df_view = df_view[
        df_view["Item_code"].astype(str).str.lower().str.contains(audit_search.strip().lower(), na=False) | df_view[
            "Item_name"].astype(str).str.lower().str.contains(audit_search.strip().lower(), na=False) | df_view[
            "Reason"].astype(str).str.lower().str.contains(audit_search.strip().lower(), na=False)]
    if audit_reason_filter != "All reasons": df_view = df_view[df_view["Reason"] == audit_reason_filter]

    st.caption(f"Showing **{len(df_view)}** of **{len(df_audit)}** entries")
    st.markdown("<br>", unsafe_allow_html=True)
    if df_view.empty:
        st.info("🔍 No entries match.")
    else:
        rows_html = []
        for _, r in df_view.iterrows():
            ts = r["Timestamp"].strftime("%d-%m-%Y %H:%M:%S") if pd.notna(r["Timestamp"]) else "—"
            delta = r.get("Change", 0)
            delta_str = f"+{int(delta)}" if int(delta) > 0 else str(int(delta))
            color = "color:#10B981; font-weight:700;" if int(delta) > 0 else (
                "color:#EF4444; font-weight:700;" if int(delta) < 0 else "color:#6B7280;")
            rows_html.append(
                f"<tr><td style='font-family:monospace; font-size:0.72rem;'>{ts}</td><td style='font-family:monospace; font-weight:600;'>{r.get('Item_code', '—')}</td><td>{r.get('Item_name', '—')}</td><td style='text-align:right;'>{r.get('Old_Qty', 0)}</td><td style='text-align:right;'>{r.get('New_Qty', 0)}</td><td style='{color}'>{delta_str}</td><td style='color:#6B7280; font-size:0.75rem;'>{r.get('Reason', '—')}</td></tr>")
        html_table = f'<div class="inv-table-wrap"><table class="inv-table"><thead><tr><th>When (IST)</th><th>Code</th><th>Item Name</th><th style="text-align:right;">Old</th><th style="text-align:right;">New</th><th style="text-align:right;">Δ</th><th>Reason</th></tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
        st.markdown(html_table, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    buffer_a = io.BytesIO()
    with pd.ExcelWriter(buffer_a, engine="openpyxl") as writer:
        df_view.to_excel(writer, index=False, sheet_name="Audit Log")
    st.download_button(label=f"📥 Download Audit Log", data=buffer_a.getvalue(),
                       file_name=f"agt_audit_log_{now_ist().strftime('%d-%m-%Y__%H-%M')}.xlsx",
                       use_container_width=True)

# =========================================================
#  📜 AUTO SCROLL ON PAGE NAVIGATION
# =========================================================
if st.session_state.get("_last_page") != page:
    st.session_state["_last_page"] = page
    scroll_to_top(delay=150)

_late = late_night_message()
if _late: st.toast(_late, icon="🌙")