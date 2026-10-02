import os
import sys

# Ensure root and src directories are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

# Load secrets into os.environ if available (Streamlit Cloud compatibility)
try:
    import streamlit as st
    for key, val in st.secrets.items():
        if isinstance(val, str):
            os.environ[key] = val
except Exception:
    pass

# Execute the main dashboard
dashboard_file = os.path.join(BASE_DIR, "src", "4_dashboard.py")
with open(dashboard_file, "r", encoding="utf-8") as f:
    code = f.read()

exec(code, globals())
