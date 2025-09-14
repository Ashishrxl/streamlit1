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
# ---------------------------------------------

# Configure Gemini using Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set your Gemini API key in `secrets.toml`.")
    st.stop()

MODEL = "gemini-1.5-flash"

# ---- Tool: Pandas executor ----
def run_pandas(df: pd.DataFrame, command: str) -> str:
    """Execute a pandas command safely on the dataframe."""
    try:
        allowed_locals = {"df": df, "pd": pd}
        result = eval(command, {"__builtins__": {}}, allowed_locals)
        if isinstance(result, (pd.DataFrame, pd.Series)):
            return result.to_string()
        return str(result)
    except Exception as e:
        return f"Error running command: {e}"

# ---- Agent ----
class CSVAgent:
    def __init__(self, model_name=MODEL):
        self.model = genai.GenerativeModel(model_name)
        self.history = []

    def ask(self, user_input: str, df: pd.DataFrame) -> str:
        self.history.append({"role": "user", "parts": [user_input]})

        system_prompt = """
        You are a data analysis assistant.
        You can answer directly in natural language OR suggest Python pandas commands
        to run on the dataframe 'df'.
        If you want me to run code, write it as: code: <pandas_expression>
        Example: code: df['Age'].mean()
        """

        full_input = [{"role": "user", "parts": [system_prompt]}] + self.history

        response = self.model.generate_content(full_input)
        text = response.text.strip()

        if text.lower().startswith("code:"):
            command = text[5:].strip()
            tool_result = run_pandas(df, command)

            follow_up_prompt = f"""
            The command `{command}` was executed on the dataframe and returned the following output:
            
            ```
            {tool_result}
            ```
            
            Based on this, provide a concise, natural language answer to the user's original question. Do not ask for the dataframe again.
            """
            
            follow_up_history = self.history + [{"role": "user", "parts": [follow_up_prompt]}]
            
            follow_up_response = self.model.generate_content(follow_up_history)
            final_response = follow_up_response.text.strip()
            
            self.history.append({"role": "model", "parts": [final_response]})
            
            return f"Ran `{command}`\n\n{final_response}"

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
        reply = st.session_state.agent.ask(query, df)
        st.subheader("🤖 Gemini Answer")
        st.write(reply)



