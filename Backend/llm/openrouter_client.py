import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Free models on OpenRouter (pick one):
# "meta-llama/llama-3.1-8b-instruct:free"
# "mistralai/mistral-7b-instruct:free"
# "google/gemma-3-27b-it:free"
# "deepseek/deepseek-r1-distill-llama-70b:free"

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

def ask_openrouter(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",   # required by OpenRouter
        "X-Title": "DeployBot Swarm"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(f"OpenRouter error: {response.status_code} - {response.text}")

    return response.json()["choices"][0]["message"]["content"]