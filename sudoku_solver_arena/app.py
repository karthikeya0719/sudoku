"""Sudoku Solver Arena - Streamlit launcher.  Run:  streamlit run app.py

Shows the full redesigned UI (web/index.html): colourful theme, dark mode, Puzzles / Custom puzzle
panels, fast solver with search limit + Cancel, step-by-step player and algorithm comparison.
The original Python-solver Streamlit app is still available:  streamlit run app_classic.py
"""
from pathlib import Path

import streamlit as st

PAGE = Path(__file__).parent / "web" / "index.html"
HEIGHT = 1300

st.set_page_config(page_title="Sudoku Solver Arena", page_icon="🧩", layout="wide")
st.markdown(
    "<style>header,footer{display:none!important}"
    ".block-container{padding:0!important;max-width:100%!important}</style>",
    unsafe_allow_html=True,
)

if hasattr(st, "iframe"):                      # newer Streamlit
    st.iframe(PAGE, height=HEIGHT)
else:                                          # older Streamlit
    import streamlit.components.v1 as components
    components.html(PAGE.read_text(encoding="utf-8"), height=HEIGHT, scrolling=True)
