import streamlit as st

st.set_page_config(
    page_title="My App",
    page_icon="🌐",
    initial_sidebar_state="expanded"
)

# --- CSS to hide footer/header ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header .decoration {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---- Home Page ----
st.title("🌐 Welcome to My App")
st.write("Use the sidebar to navigate to the CSV AI Agent page.")