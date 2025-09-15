import base64
import mimetypes
import os
import streamlit as st
import google.generativeai as genai
from google.generativeai import types


def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


def generate():
    # ✅ Correct way to set API key
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    model = "gemini-2.5-flash-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="""INSERT_INPUT_HERE""")],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    file_index = 0
    # ✅ Use genai.generate_content_stream instead of client.models.generate_content_stream
    for chunk in genai.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            not chunk.candidates
            or not chunk.candidates[0].content
            or not chunk.candidates[0].content.parts
        ):
            continue

        part = chunk.candidates[0].content.parts[0]

        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            file_name = f"generated_file_{file_index}"
            file_index += 1
            inline_data = part.inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        elif hasattr(chunk, "text") and chunk.text:
            print(chunk.text)


if __name__ == "__main__":
    generate()