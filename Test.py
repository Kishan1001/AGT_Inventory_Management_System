# Test.py
# ---------------------------------------------------------
#  🎬 PROFESSIONAL ANIMATION TEST PANEL
#  All animations are pure CSS + SVG — no CDN needed.
#  Run: streamlit run Test.py
# ---------------------------------------------------------
import streamlit as st
from datetime import datetime, timedelta, timezone

st.set_page_config(
    page_title="Animation Test Panel",
    page_icon="🎬",
    layout="wide",
)

# ---------- IST timezone ----------
IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.now(IST)


# =========================================================
#  1️⃣  CHECKMARK DRAW + CARD RISE  (Recommended)
# =========================================================
def show_checkmark_draw(inserted: int, duplicates: int, total: int):
    """SVG checkmark draws in + card rises smoothly."""
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
                            letter-spacing:-0.01em; line-height:1.3;">Upload Complete</div>
                <div style="font-size:0.82rem; color:#6B7280; margin-top:2px;">
                    Inventory synchronized · {timestamp}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px;
                    padding-top:1rem; border-top:1px solid #E8DCC8;">
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Inserted</div>
                <div style="font-size:1.5rem; font-weight:800; color:#1F2A44;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{inserted:,}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Skipped</div>
                <div style="font-size:1.5rem; font-weight:800;
                            color:{'#B45309' if duplicates > 0 else '#1F2A44'};
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{duplicates:,}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Total</div>
                <div style="font-size:1.5rem; font-weight:800; color:#A98A44;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{total:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  2️⃣  GOLD PROGRESS BAR COMPLETION
# =========================================================
def show_progress_bar(inserted: int, duplicates: int, total: int):
    """Gold progress bar fills to 100%, then summary fades in."""
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    uid = int(datetime.now().timestamp() * 1000)

    st.markdown(f"""
    <style>
        @keyframes bar-fill-{uid} {{
            0%   {{ width: 0%; }}
            100% {{ width: 100%; }}
        }}
        @keyframes shimmer-{uid} {{
            0%   {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}
        @keyframes fade-up-{uid} {{
            0%   {{ opacity: 0; transform: translateY(8px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    <div style="
        background: #FFFFFF;
        border: 1.5px solid #E8DCC8;
        border-radius: 14px;
        padding: 1.8rem 2rem;
        margin: 1rem 0 1.5rem 0;
        font-family: 'Inter', sans-serif;
        animation: fade-up-{uid} 0.4s ease-out;
    ">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    margin-bottom:1rem;">
            <div style="font-size:1rem; font-weight:700; color:#1F2A44;">✅ Upload Complete</div>
            <div style="font-size:0.75rem; color:#6B7280;">{timestamp}</div>
        </div>

        <div style="height:8px; background:#F4F6FA; border-radius:4px;
                    overflow:hidden; margin-bottom:1.2rem;">
            <div style="
                height:100%; width:0%;
                background: linear-gradient(90deg,
                    #C6A75E 0%, #E8D4A5 50%, #C6A75E 100%);
                background-size: 200% 100%;
                border-radius: 4px;
                animation: bar-fill-{uid} 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards,
                           shimmer-{uid} 1.5s linear 1.2s infinite;
            "></div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px;
                    opacity:0;
                    animation: fade-up-{uid} 0.5s ease-out 1s forwards;">
            <div>
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Inserted</div>
                <div style="font-size:1.4rem; font-weight:800; color:#1F2A44;
                            font-family:'JetBrains Mono',monospace; margin-top:4px;">
                    {inserted:,}</div>
            </div>
            <div>
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Skipped</div>
                <div style="font-size:1.4rem; font-weight:800;
                            color:{'#B45309' if duplicates > 0 else '#1F2A44'};
                            font-family:'JetBrains Mono',monospace; margin-top:4px;">
                    {duplicates:,}</div>
            </div>
            <div>
                <div style="font-size:0.68rem; font-weight:700; color:#6B7280;
                            text-transform:uppercase; letter-spacing:0.08em;">Total</div>
                <div style="font-size:1.4rem; font-weight:800; color:#A98A44;
                            font-family:'JetBrains Mono',monospace; margin-top:4px;">
                    {total:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  3️⃣  DARK NAVY CARD (Count-up styled, no JS)
# =========================================================
def show_navy_card(inserted: int, duplicates: int, total: int):
    """Premium navy card with gold accents — no count-up JS."""
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    uid = int(datetime.now().timestamp() * 1000)

    st.markdown(f"""
    <style>
        @keyframes card-in-{uid} {{
            0%   {{ opacity: 0; transform: scale(0.94) translateY(12px); }}
            100% {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}
        @keyframes pop-{uid} {{
            0%   {{ transform: scale(0); }}
            60%  {{ transform: scale(1.15); }}
            100% {{ transform: scale(1); }}
        }}
    </style>
    <div style="
        background: linear-gradient(135deg, #1F2A44 0%, #2A3856 100%);
        border: 1.5px solid #C6A75E;
        border-radius: 14px;
        padding: 1.8rem 2.2rem;
        margin: 1rem 0 1.5rem 0;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 8px 28px -8px rgba(31,42,68,0.5);
        animation: card-in-{uid} 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    ">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:1.4rem;">
            <div style="
                width:44px; height:44px; border-radius:50%;
                background: linear-gradient(135deg, #C6A75E 0%, #A98A44 100%);
                display:flex; align-items:center; justify-content:center;
                font-size:22px; flex-shrink:0;
                box-shadow: 0 0 0 6px rgba(198,167,94,0.15);
                animation: pop-{uid} 0.6s cubic-bezier(0.34,1.56,0.64,1) 0.15s both;
            ">✓</div>
            <div>
                <div style="font-size:1.15rem; font-weight:700; color:#FFFFFF;
                            letter-spacing:-0.01em;">Upload Successful</div>
                <div style="font-size:0.8rem; color:rgba(255,255,255,0.6);
                            margin-top:2px;">{timestamp}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:16px;
                    padding-top:1.2rem; border-top:1px solid rgba(198,167,94,0.25);">
            <div>
                <div style="font-size:0.68rem; font-weight:700;
                            color:rgba(255,255,255,0.55);
                            text-transform:uppercase; letter-spacing:0.1em;">
                    Inserted</div>
                <div style="font-size:1.8rem; font-weight:800; color:#C6A75E;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{inserted:,}</div>
            </div>
            <div>
                <div style="font-size:0.68rem; font-weight:700;
                            color:rgba(255,255,255,0.55);
                            text-transform:uppercase; letter-spacing:0.1em;">
                    Skipped</div>
                <div style="font-size:1.8rem; font-weight:800;
                            color:{'#F59E0B' if duplicates > 0 else '#C6A75E'};
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{duplicates:,}</div>
            </div>
            <div>
                <div style="font-size:0.68rem; font-weight:700;
                            color:rgba(255,255,255,0.55);
                            text-transform:uppercase; letter-spacing:0.1em;">
                    Total</div>
                <div style="font-size:1.8rem; font-weight:800; color:#FFFFFF;
                            font-family:'JetBrains Mono',monospace;
                            margin-top:4px; line-height:1;">{total:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  4️⃣  MULTI-STAGE CHECKLIST ANIMATION
# =========================================================
def show_checklist(inserted: int, duplicates: int, total: int):
    """Steps light up one by one — enterprise pipeline feel."""
    timestamp = now_ist().strftime("%d %b %Y, %H:%M IST")
    uid = int(datetime.now().timestamp() * 1000)

    dup_row = ""
    if duplicates > 0:
        dup_row = f"""
        <div style="opacity:0; animation: step-in-{uid} 0.4s ease-out 0.6s forwards;
                    display:flex; align-items:center; gap:12px;">
            <div style="width:22px; height:22px; border-radius:50%;
                        background:#F59E0B; display:flex; align-items:center;
                        justify-content:center; color:#FFF; font-size:12px;
                        font-weight:700; flex-shrink:0;">!</div>
            <div style="font-size:0.88rem; color:#B45309; font-weight:500;">
                <strong style="font-family:'JetBrains Mono',monospace;">{duplicates:,}</strong>
                duplicates skipped
            </div>
        </div>"""
        last_delay = "0.8s"
    else:
        last_delay = "0.6s"

    st.markdown(f"""
    <style>
        @keyframes step-in-{uid} {{
            0%   {{ opacity: 0; transform: translateX(-12px); }}
            100% {{ opacity: 1; transform: translateX(0); }}
        }}
        @keyframes pulse-{uid} {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.5); }}
            50%      {{ box-shadow: 0 0 0 8px rgba(34,197,94,0); }}
        }}
        @keyframes card-{uid} {{
            0%   {{ opacity: 0; transform: translateY(12px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    <div style="
        background: #FFFFFF;
        border: 1.5px solid #E8DCC8;
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin: 1rem 0 1.5rem 0;
        font-family: 'Inter', sans-serif;
        animation: card-{uid} 0.4s ease-out;
    ">
        <div style="font-size:1.1rem; font-weight:700; color:#1F2A44;
                    margin-bottom:1.3rem; letter-spacing:-0.01em;">
            📤 Upload Pipeline
        </div>
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div style="opacity:0; animation: step-in-{uid} 0.4s ease-out 0s forwards;
                        display:flex; align-items:center; gap:12px;">
                <div style="width:22px; height:22px; border-radius:50%;
                            background:#22C55E; display:flex; align-items:center;
                            justify-content:center; color:#FFF; font-size:12px;
                            font-weight:700; flex-shrink:0;
                            animation: pulse-{uid} 1.5s ease-in-out 0.6s;">
                    ✓</div>
                <div style="font-size:0.88rem; color:#1F2A44; font-weight:500;">
                    File received &amp; validated
                </div>
            </div>
            <div style="opacity:0; animation: step-in-{uid} 0.4s ease-out 0.2s forwards;
                        display:flex; align-items:center; gap:12px;">
                <div style="width:22px; height:22px; border-radius:50%;
                            background:#22C55E; display:flex; align-items:center;
                            justify-content:center; color:#FFF; font-size:12px;
                            font-weight:700; flex-shrink:0;">✓</div>
                <div style="font-size:0.88rem; color:#1F2A44; font-weight:500;">
                    <strong style="font-family:'JetBrains Mono',monospace;">{total:,}</strong>
                    rows parsed
                </div>
            </div>
            <div style="opacity:0; animation: step-in-{uid} 0.4s ease-out 0.4s forwards;
                        display:flex; align-items:center; gap:12px;">
                <div style="width:22px; height:22px; border-radius:50%;
                            background:#22C55E; display:flex; align-items:center;
                            justify-content:center; color:#FFF; font-size:12px;
                            font-weight:700; flex-shrink:0;">✓</div>
                <div style="font-size:0.88rem; color:#1F2A44; font-weight:500;">
                    <strong style="font-family:'JetBrains Mono',monospace;">{inserted:,}</strong>
                    records inserted
                </div>
            </div>
            {dup_row}
            <div style="opacity:0;
                        animation: step-in-{uid} 0.4s ease-out {last_delay} forwards;
                        display:flex; align-items:center; gap:12px;">
                <div style="width:22px; height:22px; border-radius:50%;
                            background: linear-gradient(135deg, #C6A75E 0%, #A98A44 100%);
                            display:flex; align-items:center; justify-content:center;
                            color:#FFF; font-size:12px; font-weight:700;
                            flex-shrink:0;">✓</div>
                <div style="font-size:0.88rem; color:#1F2A44; font-weight:600;">
                    Audit log updated · {timestamp}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  5️⃣  EXECUTIVE BANNER (compact, minimal)
# =========================================================
def show_executive_banner(inserted: int, duplicates: int):
    """Compact one-line executive banner."""
    uid = int(datetime.now().timestamp() * 1000)
    st.markdown(f"""
    <style>
        @keyframes banner-in-{uid} {{
            0%   {{ opacity: 0; transform: translateX(-20px); }}
            100% {{ opacity: 1; transform: translateX(0); }}
        }}
    </style>
    <div style="
        background: #1F2A44;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        display: flex; align-items: center; gap: 16px;
        border-left: 4px solid #C6A75E;
        box-shadow: 0 4px 16px -8px rgba(31,42,68,0.4);
        font-family: 'Inter', sans-serif;
        animation: banner-in-{uid} 0.5s ease-out;
    ">
        <div style="
            background: linear-gradient(135deg, #C6A75E 0%, #A98A44 100%);
            color: #1F2A44;
            padding: 5px 12px; border-radius: 6px;
            font-size: 0.72rem; font-weight: 800;
            letter-spacing: 0.1em; text-transform: uppercase;
            flex-shrink: 0;
        ">✓ Success</div>
        <div style="color: #FFFFFF; font-size: 0.95rem; font-weight: 500;">
            <strong style="font-family:'JetBrains Mono',monospace; color:#C6A75E;">
                {inserted:,}</strong> items uploaded
            {'<span style="opacity:0.6; margin: 0 8px;">·</span><span style="opacity:0.7;">' + str(duplicates) + ' skipped</span>' if duplicates > 0 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
#  🎬  TEST UI
# =========================================================
st.markdown("""
<div style="
    background: #1F2A44;
    padding: 1.6rem 1.9rem;
    border-radius: 12px;
    border-left: 4px solid #C6A75E;
    margin-bottom: 1.4rem;
">
    <h1 style="color:#FFFFFF; margin:0; font-size:1.4rem; font-weight:700;">
        🎬 Professional Animation Test Panel
    </h1>
    <p style="color:rgba(255,255,255,0.72); margin:0.35rem 0 0 0; font-size:0.85rem;">
        All animations use pure CSS + SVG · No CDN · Works everywhere
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### ⚙️ Test Data")
col_a, col_b, col_c = st.columns(3)
with col_a:
    inserted = st.number_input("Inserted", min_value=0, value=248, step=1, key="t_ins")
with col_b:
    duplicates = st.number_input("Skipped", min_value=0, value=3, step=1, key="t_dup")
with col_c:
    total = st.number_input("Total", min_value=0, value=251, step=1, key="t_tot")

st.markdown("---")

# ---- Row 1: Recommended animations ----
st.markdown("### 🏆 Recommended")

c1, c2 = st.columns(2)
with c1:
    if st.button("1️⃣  Checkmark Draw + Card Rise",
                 key="b_check", use_container_width=True, type="primary"):
        show_checkmark_draw(inserted, duplicates, total)
with c2:
    if st.button("2️⃣  Gold Progress Bar",
                 key="b_prog", use_container_width=True, type="primary"):
        show_progress_bar(inserted, duplicates, total)

c3, c4 = st.columns(2)
with c3:
    if st.button("3️⃣  Navy Premium Card",
                 key="b_navy", use_container_width=True, type="primary"):
        show_navy_card(inserted, duplicates, total)
with c4:
    if st.button("4️⃣  Upload Pipeline Checklist",
                 key="b_list", use_container_width=True, type="primary"):
        show_checklist(inserted, duplicates, total)

# ---- Row 2: Compact ----
st.markdown("### 📋 Compact")

c5, c6 = st.columns(2)
with c5:
    if st.button("5️⃣  Executive Banner",
                 key="b_exec", use_container_width=True):
        show_executive_banner(inserted, duplicates)
with c6:
    if st.button("🎬  Show ALL (stacked)",
                 key="b_all", use_container_width=True):
        show_checkmark_draw(inserted, duplicates, total)

st.markdown("---")
st.caption("💡 Tip: Click a button, then scroll up/down to see the animation. "
           "Each card animates on render. Reload the page to replay from scratch.")