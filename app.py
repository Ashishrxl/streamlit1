import streamlit as st
import pandas as pd
import google.generativeai as genai

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

# ---- Configure Gemini ----
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("❌ No API key found in Streamlit secrets")
    st.stop()

MODEL = "gemini-1.5-flash"

# ---- CSV Agent ----
class CSVAgent:
    def __init__(self, model_name=MODEL):
        self.model = genai.GenerativeModel(model_name)
        self.history = []

    def ask(self, user_input: str, df: pd.DataFrame) -> str:
        df_string = df.to_csv(index=False)
        full_prompt = f"""
        You are a data analysis assistant.
        Dataset (CSV format):

        {df_string}

        Question: {user_input}
        """
        self.history.append({"role": "user", "parts": [full_prompt]})
        response = self.model.generate_content(self.history)
        text = response.text.strip()
        self.history.append({"role": "model", "parts": [text]})
        return text

# ---- Custom Sidebar ----
st.sidebar.title("📌 Extra Navigation")
custom_page = st.sidebar.radio("Go to:", ["🏠 Home", "📊 CSV AI Agent", "⚙️ Settings"])

# ---- Home ----
if custom_page == "🏠 Home":
    st.title("🌐 Welcome to My App")
    st.write("Use this custom menu for special pages, or the default sidebar for pages in `/pages`.")

# ---- CSV AI Agent ----
elif custom_page == "📊 CSV AI Agent":
    st.title("📊 CSV AI Agent")

    uploaded_file = st.file_uploader("Upload your CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("✅ File loaded! Here's a preview:")
        st.dataframe(df.head())

        if "agent" not in st.session_state:
            st.session_state.agent = CSVAgent()

        query = st.text_input("Ask a question about your CSV:")
        if query:
            with st.spinner("Analyzing data..."):
                reply = st.session_state.agent.ask(query, df)
            st.subheader("🤖 AI Agent Answer")
            st.write(reply)

# ---- Settings ----
elif custom_page == "⚙️ Settings":
    st.title("⚙️ Settings")
    theme = st.selectbox("Choose a theme:", ["Light", "Dark", "System"])
    st.write(f"Theme set to: {theme}")