import streamlit as st
import google.generativeai as genai

# ✅ Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# App title
st.title("🖼️ Gemini Image + Text Generator")

# User input
prompt = st.text_area("Enter your prompt:", "A futuristic city skyline at sunset")

# Button to trigger generation
if st.button("Generate"):
    st.write("### Generated Output:")

    # Initialize the model
    model = "gemini-2.5-flash-image-preview"

    # Stream response
    response = genai.generate_content(
        model=model,
        contents=[prompt],
        generation_config={"response_modalities": ["IMAGE", "TEXT"]},
    )

    # Display each part of the response
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            # If it's an image
            st.image(part.inline_data.data, caption="Generated Image")
        elif hasattr(part, "text") and part.text:
            # If it's text
            st.write(part.text)