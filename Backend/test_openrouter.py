import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import requests

def list_free_models():
    """Fetch all currently available FREE models from OpenRouter"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch models: {response.status_code}")
        return

    models = response.json().get("data", [])
    
    # Filter free models only
    free_models = [
        m for m in models
        if str(m.get("pricing", {}).get("prompt", "1")) == "0"
    ]

    print(f"\n✅ Found {len(free_models)} FREE models:\n")
    for m in free_models:
        print(f"  📦 {m['id']}")

def test_openrouter(model: str = None):
    from llm.openrouter_client import ask_openrouter
    
    if model:
        os.environ["OPENROUTER_MODEL"] = model

    current_model = os.getenv("OPENROUTER_MODEL", "not set")
    print(f"\n🔄 Testing model: {current_model}")

    try:
        response = ask_openrouter("Say 'DeployBot Swarm is ready!' and nothing else.")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    # Step 1: List all free models
    list_free_models()

    # Step 2: Test with your current model
    test_openrouter()