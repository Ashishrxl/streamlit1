import os
import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CSS to hide the footer and header links ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Configure Gemini using Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("no api keys")
    st.stop()

MODEL = "gemini-1.5-flash"

# ---- Agent ----
class CSVAgent:
    def __init__(self, model_name=MODEL):
        self.model = genai.GenerativeModel(model_name)
        self.history = []

    def ask(self, user_input: str, df: pd.DataFrame) -> str:
        # Convert the DataFrame to a string (e.g., CSV format)
        df_string = df.to_csv(index=False)
        
        # Craft a comprehensive prompt including the data
        full_prompt = f"""
        You are a data analysis assistant.
        The following is a dataset in CSV format:
        
        {df_string}
        
        Based on this data, answer the following question:
        {user_input}
        """
        
        # Add the crafted prompt to the history
        self.history.append({"role": "user", "parts": [full_prompt]})

        # Generate content with the full prompt
        response = self.model.generate_content(self.history)
        text = response.text.strip()
        
        # Append the AI's response to history
        self.history.append({"role": "model", "parts": [text]})
        
        return text

# ---- Streamlit UI ----
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
        # Pass the DataFrame directly to the ask method
        with st.spinner("Analyzing data..."):
            reply = st.session_state.agent.ask(query, df)
        st.subheader("🤖 AI Agent Answer")
        st.write(reply)
