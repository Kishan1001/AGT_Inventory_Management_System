# inventory_ops.py
# ---------------------------------------------------------
#  INVENTORY OPERATIONS  (Logic only — no UI, no print spam)
# ---------------------------------------------------------
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi


# =========================================================
#  MONGODB ATLAS CONNECTION (from Streamlit secrets)
# =========================================================
def _get_mongo_uri():
    """Read URI from Streamlit secrets, fall back to env var."""
    try:
        return st.secrets["mongo"]["uri"]
    except Exception:
        return os.getenv("MONGO_URI", "")


MONGO_URI       = _get_mongo_uri()
DB_NAME         = "AGT"
COLLECTION_NAME = "Item_Inventory"

if not MONGO_URI:
    st.error("❌ MONGO_URI not configured. Add it to Streamlit secrets.")
    st.stop()

try:
    client = MongoClient(
        MONGO_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=8000,
    )
    client.admin.command('ping')
except Exception as e:
    st.error(f"❌ MongoDB connection failed: {e}")
    st.stop()

db         = client[DB_NAME]
collection = db[COLLECTION_NAME]


def close_connection():
    try:
        client.close()
    except Exception:
        pass


# =========================================================
#  PORTABLE PATHS (used only for local runs)
# =========================================================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FILES_DIR   = os.path.join(BASE_DIR, "Files")
OLD_DIR     = os.path.join(FILES_DIR, "old")
SHEET_PATH  = os.path.join(BASE_DIR, "Item_Sheet.xlsx")
CURRENT_XLS = os.path.join(FILES_DIR, "CURRENT_STOCK.xlsx")


def ensure_folders():
    os.makedirs(OLD_DIR, exist_ok=True)


# =========================================================
#  DN-60 BILL OF MATERIALS
# =========================================================
DN60_PART_NUM = {
    '1':  1,   # CIRCLIP
    '2':  2,   # BIG BLACK O-RING
    '3':  1,   # SMALL BLACK O-RING (MAIN HUB)
    '4':  1,   # BLACK O-RING
    '5':  1,   # RED O-RING
    '6':  2,   # PLACTIC BUSH
    '7':  2,   # HEXA NUT
    '8':  1,   # 3 DOT RUBBER BUSH
    '9':  1,   # RUBBER BUSH
    '10': 1,   # SMALL BLACK O-RING (SHAFT)
    '11': 3,   # ALLEN KEY BOLT
    '12': 1,   # CONICAL RUBBER CAP
}


# =========================================================
#  EXPORT CURRENT INVENTORY TO EXCEL (local only — safe wrapper)
# =========================================================
def download_excel_data(status):
    """Save current inventory to Excel (used only for local backup)."""
    try:
        ensure_folders()

        columns = [
            "Item_code", "Item_name", "Item_category",
            "Item_subcategory", "Location", "Quantity"
        ]

        data = list(collection.find({}, {
            "_id": 0, "Item_code": 1, "Item_name": 1,
            "Item_category": 1, "Item_subcategory": 1,
            "Location": 1, "Quantity": 1,
        }))

        df = pd.DataFrame(data)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns].fillna("")

        if status == 'old':
            timestamp   = datetime.today().strftime('%d-%m-%Y__%H-%M')
            output_file = os.path.join(OLD_DIR, f"data_{timestamp}.xlsx")
        else:
            output_file = CURRENT_XLS

        df.to_excel(output_file, index=False, sheet_name="Item Inventory")
    except Exception:
        # Silently ignore — cloud may not have writable disk
        pass