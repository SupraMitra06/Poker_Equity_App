import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Poker Equity Calculator",
    page_icon="♠️",
    layout="wide"
)

# Hide default Streamlit padding
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0rem; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Determine the directory where app.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to index.html in the React build folder
INDEX_PATH = os.path.join(BASE_DIR, "frontend", "build", "index.html")

# Fallback path if files were uploaded inside a nested directory
NESTED_INDEX_PATH = os.path.join(BASE_DIR, "build", "index.html")

if os.path.exists(INDEX_PATH) and os.path.isfile(INDEX_PATH):
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.components.v1.html(html_data, height=900, scrolling=True)
elif os.path.exists(NESTED_INDEX_PATH) and os.path.isfile(NESTED_INDEX_PATH):
    with open(NESTED_INDEX_PATH, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.components.v1.html(html_data, height=900, scrolling=True)
else:
    st.error(f"Could not find `index.html` inside `frontend/build/`. Please verify that the React build files are uploaded to GitHub under `frontend/build/`.")
