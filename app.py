import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="My App", page_icon="🌐", initial_sidebar_state="expanded")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Home", "CSV Agent"])

# ---- HOME ----
if page == "Home":
    st.title("🌐 Welcome to My App")
    st.write("Use the sidebar to navigate between pages.")

# ---- CSV AGENT ----
elif page == "CSV Agent":
    st.title("📊 CSV AI Agent")

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except KeyError:
        st.error("No API keys found in Streamlit secrets")
        st.stop()

    MODEL = "gemini-1.5-flash"

    class CSVAgent:
        def __init__(self, model_name=MODEL):
            self.model = genai.GenerativeModel(model_name)
            self.history = []

        def ask(self, user_input: str, df: pd.DataFrame) -> str:
            df_string = df.to_csv(index=False)
            full_prompt = f"""
            You are a data analysis assistant.
            The following is a dataset in CSV format:
            
            {df_string}
            
            Based on this data, answer the following question:
            {user_input}
            """
            self.history.append({"role": "user", "parts": [full_prompt]})
            response = self.model.generate_content(self.history)
            text = response.text.strip()
            self.history.append({"role": "model", "parts": [text]})
            return text

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