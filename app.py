# app.py
# ---------------------------------------------------------
#  STREAMLIT WEB UI — Enterprise Dashboard
#  Palette: #1F2A44 (Navy) · #E8DCC8 (Cream) · #C6A75E (Gold)
#  v17: Premium SaaS sidebar · 1rem fonts · single-line footer
#  Built with ❤️ for Kishan
# ---------------------------------------------------------
import io
import random
from datetime import datetime

import pandas as pd
import streamlit as st

import inventory_ops as ops
from inventory_ops import (
    DN60_PART_NUM,
    collection,
    download_excel_data,
    close_connection,
)

# =========================================================
#  😄 FUN ZONE — Kishan Edition
# =========================================================
FUN_MODE = False   # set to True to enable full joke rotation


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
    hour = datetime.now().hour
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
    /* ---------- Professional Typeface ---------- */
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
        font-size: 16px;
    }

    .stApp { background: #FAFAF7; }

    /* =========================================================
       HIDE STREAMLIT CHROME — KEEP SIDEBAR TOGGLE
       ========================================================= */
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

    /* -------- STATE 1: Sidebar CLOSED -------- */
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

    /* -------- STATE 2: Sidebar OPEN -------- */
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

    [data-testid="stSidebar"] {
        z-index: 999998 !important;
    }

    @media (max-width: 768px) {
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem !important;
        }
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

    /* =========================================================
       HERO
       ========================================================= */
    .hero {
        background: var(--navy);
        padding: 1.75rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
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
        color: #FFFFFF;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        line-height: 1.3;
    }
    .hero p {
        color: rgba(255,255,255,0.72);
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
        font-weight: 400;
        letter-spacing: 0.005em;
    }
    .hero .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(198,167,94,0.15);
        color: var(--gold);
        padding: 0.3rem 0.75rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 0.9rem;
        border: 1px solid rgba(198,167,94,0.35);
    }
    .hero .badge .dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #4ADE80;
        box-shadow: 0 0 6px rgba(74,222,128,0.8);
    }

    /* ---------- 3D Wireframe Cube ---------- */
    .hero-3d {
        width: 130px;
        height: 130px;
        perspective: 700px;
        opacity: 0.55;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .hero-3d .cube {
        position: relative;
        width: 70px;
        height: 70px;
        transform-style: preserve-3d;
        animation: hero-spin 24s linear infinite;
    }
    .hero-3d .cube .face {
        position: absolute;
        width: 70px;
        height: 70px;
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
        .hero { padding: 1.5rem 1.25rem; }
        .hero h1 { font-size: 1.3rem; }
    }

    /* =========================================================
       METRIC CARDS
       ========================================================= */
    .metric-card {
        background: var(--white);
        padding: 1.15rem 1.35rem;
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
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 0;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--ink);
        margin: 0.45rem 0 0 0;
        letter-spacing: -0.02em;
        line-height: 1.15;
        font-variant-numeric: tabular-nums;
    }
    .metric-value.primary { color: var(--navy); }
    .metric-value.gold    { color: var(--gold-700); }
    .metric-value.warn    { color: #B45309; }
    .metric-value.danger  { color: #B91C1C; }
    .metric-value.success { color: #047857; }

    .metric-icon {
        display: inline-block;
        font-size: 1.1rem;
        margin-bottom: 0.4rem;
        opacity: 0.85;
    }

    /* =========================================================
       SECTION HEADERS
       ========================================================= */
    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--ink);
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.01em;
        padding-left: 0.75rem;
        border-left: 3px solid var(--gold);
        line-height: 1.3;
    }
    .section-sub {
        color: var(--muted);
        font-size: 0.92rem;
        margin: 0 0 1.25rem 0.75rem;
        font-weight: 400;
    }

    /* =========================================================
       BUTTONS
       ========================================================= */
    .stButton > button {
        background: var(--navy);
        color: #FFFFFF;
        border: 1px solid var(--navy);
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.92rem;
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
        0% {
            box-shadow: 0 1px 2px rgba(31,42,68,0.06),
                        0 0 0 0 rgba(198,167,94,0.55);
        }
        70% {
            box-shadow: 0 1px 2px rgba(31,42,68,0.06),
                        0 0 0 10px rgba(198,167,94,0);
        }
        100% {
            box-shadow: 0 1px 2px rgba(31,42,68,0.06),
                        0 0 0 0 rgba(198,167,94,0);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            animation: none;
        }
    }

    /* ---------- Download button ---------- */
    .stDownloadButton > button {
        background: var(--gold);
        color: var(--navy);
        border: 1px solid var(--gold-700);
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.92rem;
        letter-spacing: 0.01em;
        box-shadow: 0 1px 2px rgba(31,42,68,0.06);
    }
    .stDownloadButton > button:hover {
        background: var(--gold-700);
        color: #FFFFFF;
        border-color: var(--gold-700);
    }

    /* =========================================================
       INPUTS
       ========================================================= */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #D1D5DB;
        background: var(--white);
        padding: 0.6rem 0.85rem;
        font-size: 0.97rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--gold);
        box-shadow: 0 0 0 3px rgba(198,167,94,0.18);
    }
    label, .stTextInput label, .stNumberInput label {
        font-weight: 600 !important;
        color: var(--ink) !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.02em;
        text-transform: none;
    }

    /* =========================================================
       INVENTORY HTML TABLE
       ========================================================= */
    .inv-table-wrap {
        max-height: 720px;
        overflow-y: auto;
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--white);
        box-shadow: 0 4px 16px -8px rgba(31,42,68,0.12);
    }
    .inv-table-wrap::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    .inv-table-wrap::-webkit-scrollbar-track {
        background: #F7F8FA;
        border-radius: 10px;
    }
    .inv-table-wrap::-webkit-scrollbar-thumb {
        background: #D1D5DB;
        border-radius: 10px;
        border: 2px solid #F7F8FA;
    }
    .inv-table-wrap::-webkit-scrollbar-thumb:hover {
        background: var(--gold);
    }

    .inv-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.9rem;
        background: var(--white);
        font-feature-settings: "tnum";
    }

    .inv-table thead th {
        position: sticky;
        top: 0;
        z-index: 5;
        background: var(--navy) !important;
        color: #FFFFFF !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        text-align: left !important;
        padding: 0.85rem 1rem !important;
        border: none !important;
        border-bottom: 3px solid var(--gold) !important;
        white-space: nowrap;
        user-select: none;
    }
    .inv-table thead th:first-child {
        border-top-left-radius: 12px;
    }
    .inv-table thead th:last-child {
        border-top-right-radius: 12px;
    }
    .inv-table thead th:nth-child(6),
    .inv-table thead th:nth-child(7) {
        text-align: right !important;
    }

    .inv-table tbody td {
        color: var(--ink) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        border: none !important;
        border-bottom: 1px solid #E5E7EB !important;
        vertical-align: middle;
        line-height: 1.4;
        background: transparent;
        transition: background 0.12s ease;
    }

    .inv-table tbody td:nth-child(1) {
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: var(--navy) !important;
        letter-spacing: -0.01em;
    }
    .inv-table tbody td:nth-child(2) {
        font-weight: 600 !important;
        color: var(--ink) !important;
    }
    .inv-table tbody td:nth-child(3),
    .inv-table tbody td:nth-child(4) {
        color: var(--muted) !important;
        font-size: 0.82rem !important;
    }
    .inv-table tbody td:nth-child(5) {
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-size: 0.82rem !important;
        color: var(--muted) !important;
    }
    .inv-table tbody td:nth-child(6) {
        text-align: right !important;
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        color: var(--navy) !important;
        font-variant-numeric: tabular-nums;
    }
    .inv-table tbody td:nth-child(7) {
        text-align: right !important;
        color: var(--muted) !important;
        font-size: 0.78rem !important;
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }

    .inv-table tbody tr:nth-child(even) td {
        background-color: #FAFBFD !important;
    }

    .inv-table tbody tr:hover td {
        background-color: rgba(198,167,94,0.10) !important;
    }

    .inv-table tbody tr:last-child td {
        border-bottom: 1px solid #E5E7EB !important;
    }
    .inv-table tbody tr:last-child td:first-child {
        border-bottom-left-radius: 12px;
    }
    .inv-table tbody tr:last-child td:last-child {
        border-bottom-right-radius: 12px;
    }

    @media (max-width: 768px) {
        .inv-table thead th,
        .inv-table tbody td {
            padding: 0.6rem 0.7rem !important;
            font-size: 0.8rem !important;
        }
        .inv-table thead th {
            font-size: 0.68rem !important;
        }
    }

    /* =========================================================
       SIDEBAR
       ========================================================= */
    [data-testid="stSidebar"] {
        background: var(--navy);
        border-right: 1px solid #16202F;
    }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }

    [data-testid="stSidebar"] .stMarkdown {
        margin-bottom: 0 !important;
    }

    /* Sidebar radio nav — 1rem */
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.15rem;
        display: flex;
        flex-direction: column;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        display: flex;
        align-items: center;
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #CBD5E1 !important;
        border-left: 3px solid transparent;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(198,167,94,0.10);
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
        display: none;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: rgba(198,167,94,0.16);
        color: #FFFFFF !important;
        border-left-color: var(--gold);
        font-weight: 600 !important;
    }

    /* =========================================================
       ALERTS
       ========================================================= */
    .stAlert {
        border-radius: 8px;
        border: 1px solid var(--border);
        box-shadow: none;
        font-size: 0.95rem;
    }

    /* =========================================================
       FILE UPLOADER
       ========================================================= */
    [data-testid="stFileUploader"] { border-radius: 8px; }
    [data-testid="stFileUploader"] section {
        border-radius: 8px;
        border: 1.5px dashed #D1D5DB;
        background: var(--white);
        transition: border-color 0.15s ease;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--gold);
    }

    /* =========================================================
       PROGRESS BAR
       ========================================================= */
    .stProgress > div > div > div > div {
        background: var(--gold);
    }

    /* =========================================================
       DIVIDERS
       ========================================================= */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.5rem 0;
    }

    /* =========================================================
       RESPONSIVE
       ========================================================= */
    @media (max-width: 900px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
        }
        [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
#  SIDEBAR — Premium SaaS · 1rem fonts
# =========================================================
with st.sidebar:

    # ---------- Brand header ----------
    st.markdown(
        '<div style="display:flex; align-items:center; gap:12px; '
        'padding:4px 0 14px 0;">'
        '<div style="width:38px; height:38px; border-radius:9px; '
        'background:linear-gradient(135deg,#C6A75E,#A98A44); '
        'display:flex; align-items:center; justify-content:center; '
        'font-size:20px; flex-shrink:0;">📦</div>'
        '<div style="min-width:0;">'
        '<div style="font-size:1rem; font-weight:700; color:#FFFFFF; '
        'letter-spacing:-0.01em; line-height:1.2;">Inventory Hub</div>'
        '<div style="font-size:1rem; color:#94A3B8; '
        'letter-spacing:0.02em; font-weight:500; line-height:1.3; '
        'margin-top:2px;">AGT Inventory Management System</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<hr style="border:none; border-top:1px solid rgba(198,167,94,0.18); '
        'margin:8px 0 16px 0;">',
        unsafe_allow_html=True,
    )

    # ---------- Navigation ----------
    st.markdown(
        '<div style="font-size:1rem; color:#94A3B8; letter-spacing:0.12em; '
        'text-transform:uppercase; font-weight:700; margin-bottom:10px; '
        'padding-left:2px;">Menu</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        label="Select section",
        options=[
            "📤  Update from Excel",
            "⚙️  Update by DN-60",
            "📊  Check Production",
            "🧮  Required Items",
            "📋  View Inventory",
        ],
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.markdown(
        '<hr style="border:none; border-top:1px solid rgba(198,167,94,0.18); '
        'margin:18px 0 16px 0;">',
        unsafe_allow_html=True,
    )

    # ---------- Footer — single line, no wrap ----------
    st.markdown(
        '<div style="margin-top:20px; display:flex; align-items:center; '
        'gap:8px; font-size:0.75rem; color:#94A3B8; '
        'padding-left:2px; white-space:nowrap; overflow:hidden;">'
        '<span style="width:7px; height:7px; border-radius:50%; '
        'flex-shrink:0; '
        'background:#22C55E; box-shadow:0 0 6px rgba(34,197,94,0.8);"></span>'
        '<span style="flex-shrink:0;">Online</span>'
        '<span style="opacity:0.4; flex-shrink:0;">·</span>'
        '<span style="flex-shrink:0;">© 2026 AASHDHA GLOBAL TECH</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# =========================================================
#  HERO HEADER
# =========================================================
st.markdown(f"""
<div class="hero">
    <div class="hero-content">
        <h1>AGT Inventory Management System</h1>
        <p>DN-60 Valve Production Tracker</p>
        <span class="badge"><span class="dot"></span> Live · {datetime.now().strftime('%d %b %Y, %H:%M')}</span>
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
    low_stock = collection.count_documents({"Quantity": {"$lt": 100}})
    total_qty_pipeline = list(collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$Quantity"}}}
    ]))
    total_qty = total_qty_pipeline[0]["total"] if total_qty_pipeline else 0
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
        <p class="metric-value" style="font-size:1.15rem;">{datetime.today().strftime('%d-%m-%Y %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
#  ROUTED CONTENT
# =========================================================

# ---------------------------------------------------------
#  SECTION 1 — Upload Excel & Update
# ---------------------------------------------------------
if page == "📤  Update from Excel":
    st.markdown('<div class="section-header">📤 Update Inventory from Excel</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload your Item_Sheet.xlsx to replace the entire inventory.</div>', unsafe_allow_html=True)

    st.warning("⚠️ **Warning:** This will DROP the existing collection and re-insert all items from the uploaded file.")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        password1 = st.text_input("🔒 Enter Password", type="password", key="pwd1", placeholder="Enter Password")
    with col_b:
        uploaded_file = st.file_uploader("📁 Choose Item_Sheet.xlsx", type=["xlsx"], key="uploader1")

    st.markdown("<br>", unsafe_allow_html=True)

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
                with st.spinner("Updating inventory..."):
                    ops.download_excel_data('old')
                    collection.drop()

                    df = pd.read_excel(uploaded_file)
                    st.info(f"📄 Total rows in file: {len(df)}")

                    inserted, duplicates = 0, 0
                    progress = st.progress(0)

                    for index, row in df.iterrows():
                        data = row.to_dict()
                        data["_id"]          = str(data["Item_code"])
                        data["Item_code"]    = str(data["Item_code"])
                        data["Quantity"]     = int(data["Quantity"])
                        data["Updated_date"] = datetime.today().strftime("%d-%m-%Y %H:%M:%S")
                        try:
                            collection.insert_one(data)
                            inserted += 1
                        except Exception:
                            duplicates += 1
                        progress.progress((index + 1) / len(df))

                    st.success(f"✅ Inventory updated — **{inserted}** items inserted, **{duplicates}** duplicates skipped.")

                    if inserted >= 100:
                        st.balloons()
                        st.toast(f"🎊 {inserted} items in one go, Kishan! Legendary upload.", icon="🏆")
                    elif inserted >= 30:
                        st.balloons()
                        st.toast("📦 Solid upload — nice work, Kishan.", icon="👍")
                    else:
                        st.toast("✅ Uploaded. Small batch, no drama.", icon="📎")
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

# ---------------------------------------------------------
#  SECTION 2 — Update by DN-60 valve count
# ---------------------------------------------------------
elif page == "⚙️  Update by DN-60":
    st.markdown('<div class="section-header">⚙️ Update by DN-60 Valve Count</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Subtract parts required to build a given number of DN-60 valves.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        password2 = st.text_input("🔒 Enter Password", type="password", key="pwd2", placeholder="Enter Password")
    with col_b:
        dn60_count = st.number_input("🔧 Number of valves", min_value=1, value=10, step=1, key="n2")

    st.markdown("<br>", unsafe_allow_html=True)

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
                    today = datetime.today().strftime("%d-%m-%Y")
                    rows = []

                    for part_num in sorted(DN60_PART_NUM, key=int):
                        per_valve = DN60_PART_NUM[part_num]
                        doc = collection.find_one({"Item_code": part_num})

                        old_count = int(doc['Quantity'])
                        used      = dn60_count * per_valve
                        new_count = old_count - used

                        collection.update_one(
                            {"Item_code": part_num},
                            {"$set": {"Quantity": new_count, "Updated_date": today}}
                        )

                        rows.append({
                            "#":         part_num,
                            "Item Name": doc['Item_name'],
                            "Old":       old_count,
                            "Used":      used,
                            "New":       new_count,
                        })

                    st.success(f"✅ Stock updated for building **{dn60_count}** valves!")
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

# ---------------------------------------------------------
#  SECTION 3 — Check DN-60 production capacity
# ---------------------------------------------------------
elif page == "📊  Check Production":
    st.markdown('<div class="section-header">📊 DN-60 Production Capacity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">How many DN-60 valves can be produced with the current stock?</div>', unsafe_allow_html=True)

    if st.button("🔄 Check Capacity", key="btn3", type="primary", use_container_width=True):
        try:
            limits, available, part_names = {}, {}, {}

            for part, qty_per_valve in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                if item:
                    stock = int(item.get("Quantity", 0))
                    name  = item.get("Item_name", f"Part {part}")
                else:
                    stock = 0
                    name  = f"Part {part} (not found)"

                available[part]  = stock
                limits[part]     = stock // qty_per_valve
                part_names[part] = name

            max_valves    = min(limits.values())
            limiting_part = min(limits, key=limits.get)

            if available[limiting_part] == 0:
                st.toast(funny(ZERO_STOCK_LINES), icon="😬")

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
                    <p class="metric-value warn" style="font-size:1.15rem;">{part_names[limiting_part]}</p>
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
                    "Part":       part,
                    "Part Name":  part_names[part],
                    "Stock":      available[part],
                    "Per Valve":  DN60_PART_NUM[part],
                    "Can Make":   limits[part],
                    "Status":     "⚠️ LIMITING" if part == limiting_part else "✅ OK",
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.info(f"**Bottleneck:** {part_names[limiting_part]} — need **{DN60_PART_NUM[limiting_part]}/valve**, have **{available[limiting_part]}**")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 4 — Required items for target
# ---------------------------------------------------------
elif page == "🧮  Required Items":
    st.markdown('<div class="section-header">🧮 Parts Required for Target Quantity</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Calculate how many parts to order to build N valves.</div>', unsafe_allow_html=True)

    target = st.number_input("🎯 Target number of DN-60 valves", min_value=1, value=100, step=1, key="target4")

    if st.button("🧮 Calculate", key="btn4", type="primary", use_container_width=True):
        try:
            rows, total_short = [], 0

            for part, per_valve in DN60_PART_NUM.items():
                item = collection.find_one({"Item_code": part})
                if item:
                    stock       = int(item.get("Quantity", 0))
                    name        = item.get("Item_name", f"Part {part}")
                    category    = item.get("Item_category", "—")
                    subcategory = item.get("Item_subcategory", "—")
                else:
                    stock       = 0
                    name        = f"Part {part} (not found)"
                    category    = "—"
                    subcategory = "—"

                needed    = per_valve * target
                shortfall = max(0, needed - stock)
                if shortfall > 0:
                    total_short += 1

                rows.append({
                    "Part":         part,
                    "Part Name":    name,
                    "Category":     category,
                    "Subcategory":  subcategory,
                    "Per":          per_valve,
                    "Stock":        stock,
                    "Needed":       needed,
                    "Order":        shortfall,
                    "Status":       "🛒 ORDER" if shortfall > 0 else "✅ OK",
                })

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
                    st.warning(f"🛒 **ORDER LIST:** — {total_short} parts to order. Kishan, your wallet just fainted.")
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
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------------------------------------------------
#  SECTION 5 — View current inventory + search + download
# ---------------------------------------------------------
elif page == "📋  View Inventory":
    if st.session_state.pop("clear_inv_filters", False):
        st.session_state["inv_search"] = ""
        st.session_state["inv_category"] = "All"
        st.session_state["inv_subcategory"] = "All"

    st.markdown('<div class="section-header">📋 Current Inventory Status</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">View all items, search, filter and download as Excel.</div>', unsafe_allow_html=True)

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
            st.session_state["inv_loaded_at"] = datetime.today().strftime('%d-%m-%Y %H:%M')

        except Exception as e:
            st.error(f"❌ Failed to load: {e}")
            st.stop()

    df = st.session_state.get("inv_data")
    if df is None or df.empty:
        st.info("Click **🔄 Load Inventory** to fetch current stock.")
        st.stop()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-header" style="font-size:1.05rem; margin-bottom:0.5rem;">'
        '🔍 Search & Filter</div>',
        unsafe_allow_html=True,
    )

    search_text = st.text_input(
        "Search by Item Name or Code",
        placeholder="🔎 Try: O-RING, BOLT, CIRCLIP, or a code like 94181553L",
        key="inv_search",
        help="Case-insensitive · partial match · searches both name and code",
        label_visibility="collapsed",
    )

    fc1, fc2, fc3 = st.columns([1, 1, 2])

    with fc1:
        category_opts = ["All"] + sorted(
            [c for c in df["Item_category"].dropna().unique().tolist() if str(c).strip()]
        )
        if st.session_state.get("inv_category") not in category_opts:
            st.session_state["inv_category"] = "All"
        selected_category = st.selectbox(
            "Category",
            options=category_opts,
            key="inv_category",
        )

    with fc2:
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
        display_df = filtered.fillna("—").astype(str).replace("None", "—")
        display_df = display_df.rename(columns={
            "Item_code":        "Code",
            "Item_name":        "Item Name",
            "Item_category":    "Category",
            "Item_subcategory": "Subcategory",
            "Location":         "Location",
            "Quantity":         "Qty",
            "Updated_date":     "Updated",
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

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="Current Stock")

    timestamp = datetime.today().strftime("%d-%m-%Y__%H-%M")

    if filtered.empty:
        st.button(
            "📥 Download as Excel",
            disabled=True,
            use_container_width=True,
            key="dl5_disabled",
            help="Nothing to download — no items match your filters.",
        )
    else:
        st.download_button(
            label=f"📥 Download {len(filtered)} filtered item(s) as Excel",
            data=buffer.getvalue(),
            file_name=f"agt_inventory_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl5",
            use_container_width=True,
        )

# =========================================================
#  🌙 LATE-NIGHT EASTER EGG
# =========================================================
_late = late_night_message()
if _late:
    st.toast(_late, icon="🌙")