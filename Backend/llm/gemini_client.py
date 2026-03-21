import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def ask_gemini(prompt: str) -> str:

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text