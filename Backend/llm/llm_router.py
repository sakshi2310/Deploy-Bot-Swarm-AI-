import os
from dotenv import load_dotenv

load_dotenv()

def ask_llm(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider == "gemini":
        from llm.gemini_client import ask_gemini
        print("🤖 Using Gemini...")
        return ask_gemini(prompt)

    elif provider == "ollama":
        from llm.ollama_engine import ask_ollama
        print("🤖 Using Ollama...")
        return ask_ollama(prompt)

    elif provider == "openrouter":
        from llm.openrouter_client import ask_openrouter
        print("🤖 Using OpenRouter...")
        return ask_openrouter(prompt)

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Use 'gemini', 'ollama' or 'openrouter'")