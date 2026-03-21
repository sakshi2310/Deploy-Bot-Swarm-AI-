import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import requests
from tools.github_tool import parse_github_url, get_repo_files, get_file_content
from agents.test_agent import run_test_generation, save_tests_to_file


def get_repo_from_user() -> str:
    print("=" * 50)
    print("🔗 Enter GitHub Repository")
    print("=" * 50)
    print("Examples:")
    print("  https://github.com/psf/requests")
    print("  https://github.com/sakshi2310/Review-Analysis-Auto-Response-System")
    print()
    url = input("📎 Paste GitHub URL here: ").strip()
    repo = parse_github_url(url)
    print(f"✅ Parsed repo: {repo}")
    return repo


def fetch_raw_file(repo: str, filename: str) -> str:
    """
    Fetch raw file content directly from GitHub raw URL
    Works for public repos without token
    """
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{filename}"
    response = requests.get(raw_url)

    if response.status_code == 200:
        return response.text

    # Try master branch if main doesn't work
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/{filename}"
    response = requests.get(raw_url)

    if response.status_code == 200:
        return response.text

    raise Exception(f"Could not fetch {filename} from {repo}")


def test_fetch_python_files(repo: str) -> list:
    print("\n" + "=" * 50)
    print("🔄 TEST 1: Fetch Python Files from Repo")
    print("=" * 50)

    try:
        files = get_repo_files(repo)
        if not files:
            print("⚠️  No Python files found in root.")
            return []

        print(f"✅ Found {len(files)} Python file(s):")
        for i, f in enumerate(files):
            print(f"   [{i}] 📄 {f['name']}")
        return files

    except Exception as e:
        print(f"❌ Failed to fetch files: {e}")
        return []


def test_fetch_file_content(files: list) -> tuple:
    print("\n" + "=" * 50)
    print("🔄 TEST 2: Select & Fetch File Content")
    print("=" * 50)

    try:
        if len(files) > 1:
            choice = input(f"\n👆 Pick a file to test [0-{len(files)-1}]: ").strip()
            try:
                index = int(choice)
            except ValueError:
                index = 0
        else:
            index = 0
            print("   Auto-selecting only file found.")

        target_file = files[index]
        content = get_file_content(target_file["download_url"])

        print(f"✅ Fetched  : {target_file['name']}")
        print(f"   Size     : {len(content)} characters")
        print(f"   Preview  : {content[:150].strip()}...")

        return target_file["name"], content

    except Exception as e:
        print(f"❌ Failed to fetch file content: {e}")
        return None, None


def test_generate_tests(repo: str, filename: str, content: str):
    print("\n" + "=" * 50)
    print("🔄 TEST 3: Test Generation Agent")
    print("=" * 50)

    if not content:
        print("⚠️  Skipping — no content available")
        return

    try:
        # ✅ STEP 1 — Save the GitHub source file locally
        os.makedirs("generated_tests", exist_ok=True)
        source_path = os.path.join("generated_tests", filename)

        with open(source_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 Source file saved: {source_path}")

        # ✅ STEP 2 — Generate tests using LLM
        print(f"🤖 Generating tests for '{filename}' (20-40 seconds)...")
        result = run_test_generation(content, filename)
        saved_path = save_tests_to_file(result, filename)

        print("\n" + "─" * 50)
        print("📋 GENERATED TEST PREVIEW:")
        print("─" * 50)
        print(result[:800])
        if len(result) > 800:
            print(f"\n... (full file at {saved_path})")

        # ✅ STEP 3 — Always run fix_tests.py to guarantee clean imports
        print("\n🔧 Running fix_tests.py to clean up imports...")
        os.system("python fix_tests.py")

        # ✅ STEP 4 — Auto run pytest and show results
        print("\n" + "─" * 50)
        print("🧪 Running pytest automatically...")
        print("─" * 50)
        exit_code = os.system("pytest generated_tests/test_app.py -v -p no:warnings")

        print("\n" + "─" * 50)
        print("📊 EVALUATION:")

        result_lower = result.lower()
        checks = {
            "Has test_ functions"     : "def test_" in result_lower,
            "Has assert statements"   : "assert" in result_lower,
            "Has docstrings"          : '"""' in result or "'''" in result,
            "Source file saved"       : os.path.exists(source_path),
            "Test file saved"         : os.path.exists(saved_path),
            "pytest passed"           : exit_code == 0,
            "Response is detailed"    : len(result) > 500,
        }

        passed = 0
        for check, ok in checks.items():
            print(f"  {'✅' if ok else '❌'} {check}")
            if ok:
                passed += 1

        print(f"\n🏆 Score: {passed}/{len(checks)} checks passed")

        if passed >= 5:
            print("\n✅ MODULE 3 COMPLETE — Test Generation Agent working!")
        else:
            print("\n⚠️  Partial pass — check output above")

    except Exception as e:
        print(f"❌ Test generation failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Module 3 Tests...\n")

    repo     = get_repo_from_user()
    files    = test_fetch_python_files(repo)

    if files:
        filename, content = test_fetch_file_content(files)
        if content:
            test_generate_tests(repo, filename, content)  # 👈 pass repo too

    print("\n✅ Done! Check results above.")