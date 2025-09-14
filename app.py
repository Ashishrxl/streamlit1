import sys
import subprocess

# Ensure the bad 'google' package is removed and the right one is installed
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "google"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "google-generativeai"], check=False)



import os
import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-1.5-flash"

# ---- Tool: Pandas executor ----
def run_pandas(df: pd.DataFrame, command: str) -> str:
    """
    Execute a pandas command safely on the dataframe.
    Example command: df['column'].mean()
    """
    try:
        # Restrict globals for safety
        allowed_locals = {"df": df, "pd": pd}
        result = eval(command, {"__builtins__": {}}, allowed_locals)

        # Convert result nicely
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
        # Add user input
        self.history.append({"role": "user", "parts": [user_input]})

        # System-style instruction
        system_prompt = """
        You are a data analysis assistant. 
        You can answer directly in natural language OR suggest Python pandas commands 
        to run on the dataframe 'df'. 
        If you want me to run code, write it as: code: <pandas_expression>
        Example: code: df['Age'].mean()
        """

        # Combine system + history
        full_input = [{"role": "user", "parts": [system_prompt]}] + self.history

        # Get Gemini response
        response = self.model.generate_content(full_input)
        text = response.text.strip()

        # If Gemini suggests code, run it
        if text.lower().startswith("code:"):
            command = text[5:].strip()
            tool_result = run_pandas(df, command)

            # Add tool result back
            self.history.append({"role": "tool", "parts": [f"Result: {tool_result}"]})

            # Ask Gemini to explain the result
            follow_up = self.model.generate_content(self.history)
            self.history.append({"role": "model", "parts": [follow_up.text]})
            return f"Ran `{command}`\n\n{follow_up.text}"

        # Normal text answer
        self.history.append({"role": "model", "parts": [text]})
        return text

# ---- Streamlit UI ----
st.title("📊 Gemini CSV Agent with Pandas Tools")

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