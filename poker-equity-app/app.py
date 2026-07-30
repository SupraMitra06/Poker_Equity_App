import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Poker Equity Calculator",
    page_icon="♠️",
    layout="wide"
)

# Hide Streamlit header padding
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0rem; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Locate App.js in the source directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_JS_PATH = os.path.join(BASE_DIR, "frontend", "src", "App.js")

if os.path.exists(APP_JS_PATH):
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        react_code = f.read()

    # Adapt component export for Babel execution
    react_code = react_code.replace("export default function PokerEquity()", "function PokerEquity()")
    react_code = react_code.replace("export default PokerEquity;", "")

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
          body {{ margin: 0; background-color: #08211a; color: #e8f3ec; font-family: sans-serif; }}
        </style>
      </head>
      <body>
        <div id="root"></div>
        <script type="text/babel">
          {react_code}

          const root = ReactDOM.createRoot(document.getElementById('root'));
          root.render(<PokerEquity />);
        </script>
      </body>
    </html>
    """

    components.html(html_code, height=950, scrolling=True)
else:
    st.error("Could not find frontend/src/App.js on GitHub!")
