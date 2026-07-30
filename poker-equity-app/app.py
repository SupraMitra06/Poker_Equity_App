import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="Poker Equity Calculator",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit custom CSS overrides to ensure full viewport utilization
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

BUILD_DIR = os.path.join(os.path.dirname(__file__), "frontend", "build")

if os.path.exists(BUILD_DIR):
    # Render production static build from React
    components.html(
        open(os.path.join(BUILD_DIR, "index.html"), "r").read(),
        height=950,
        scrolling=True
    )
else:
    # Development fallback pointing to local dev server
    components.iframe("http://localhost:3000", height=950, scrolling=True)