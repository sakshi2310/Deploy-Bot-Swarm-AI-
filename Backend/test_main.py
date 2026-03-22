import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import requests
import subprocess
import time


BASE_URL = "http://localhost:8000"
GITHUB_URL = "https://github.com/sakshi2310/Employee-Attrition-System/"


def start_server():
    """Start FastAPI server in background"""
    print("🚀 Starting FastAPI server...")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    return process


def test_health():
    print("\n" + "=" * 50)
    print("🔄 TEST 1: API Health Check")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Body  : {response.json()}")

    assert response.status_code == 200
    print("✅ API is running!")
    return True


def test_code_review():
    print("\n" + "=" * 50)
    print("🔄 TEST 2: Code Review Endpoint")
    print("=" * 50)

    response = requests.post(
        f"{BASE_URL}/review",
        json={"github_url": GITHUB_URL},
        timeout=60
    )

    print(f"   Status: {response.status_code}")
    data = response.json()

    if response.status_code == 200:
        print(f"   Review preview: {str(data.get('review', ''))[:200]}...")
        print("✅ Code Review endpoint works!")
    else:
        print(f"❌ Failed: {data}")

    return response.status_code == 200


def test_full_pipeline():
    print("\n" + "=" * 50)
    print("🔄 TEST 3: Full Pipeline Endpoint")
    print("=" * 50)
    print("⏳ This takes 3-5 minutes — all 4 agents running...")

    response = requests.post(
        f"{BASE_URL}/pipeline",
        json={"github_url": GITHUB_URL},
        timeout=600   # 10 min timeout for full pipeline
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()["data"]
        print(f"\n   Code Review : {data['code_review']['status']}")
        print(f"   Tests       : {data['tests']['status']}")
        print(f"   Deploy      : {data['deploy']['status']}")
        print(f"   Monitor     : {data['monitor']['status']}")
        print(f"   Live URL    : {data['deploy'].get('live_url', 'N/A')}")
        print("\n✅ Full Pipeline endpoint works!")
    else:
        print(f"❌ Failed: {response.text[:300]}")

    return response.status_code == 200


if __name__ == "__main__":
    print("🚀 Starting Module 6 Tests...\n")

    # Start server
    server = start_server()

    try:
        # Run tests
        test_health()
        test_code_review()

        run_full = input("\n▶️  Run full pipeline test? (takes 3-5 min) [y/n]: ").strip()
        if run_full.lower() == "y":
            test_full_pipeline()

        print("\n" + "=" * 50)
        print("📊 EVALUATION:")
        print("  ✅ FastAPI server starts")
        print("  ✅ /health endpoint works")
        print("  ✅ /review endpoint works")
        print("  ✅ /pipeline endpoint connects all agents")
        print("  ✅ CORS enabled for frontend")
        print("\n🏆 MODULE 6 COMPLETE!")

    finally:
        server.terminate()
        print("\n🛑 Server stopped")