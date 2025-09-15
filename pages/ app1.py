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

    file_index = 0

    # Stream response
    for chunk in genai.generate_content_stream(
        model="gemini-2.5-flash-image-preview",
        contents=[prompt],
        generation_config={"response_modalities": ["IMAGE", "TEXT"]},
    ):
        if not chunk.candidates:
            continue

        part = chunk.candidates[0].content.parts[0]

        # ✅ If it's an image
        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            file_index += 1
            image_bytes = part.inline_data.data

            st.image(image_bytes, caption=f"Generated Image {file_index}")

        # ✅ If it's text
        elif hasattr(chunk, "text") and chunk.text:
            st.write(chunk.text)