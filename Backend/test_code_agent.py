import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from tools.github_tool import parse_github_url, get_repo_files, get_latest_commit_diff
from agents.code_agent import run_code_review
from llm.openrouter_client import ask_openrouter

def test_openrouter():
    print("🔄 Testing OpenRouter connection...")
    
    try:
        response = ask_openrouter("Say 'DeployBot Swarm is ready!' and nothing else.")
        print(f"✅ OpenRouter response: {response}")
    except Exception as e:
        print(f"❌ OpenRouter failed: {e}")

# In test_code_agent.py — update get_repo_from_user()
def get_repo_from_user() -> str:
    print("=" * 50)
    print("🔗 Enter GitHub Repository")
    print("=" * 50)
    url = input("📎 Paste GitHub URL here: ").strip()

    result = parse_github_url(url)

    # Handle both return formats (string or tuple)
    if isinstance(result, tuple):
        repo = result[0]
    else:
        repo = result

    print(f"✅ Parsed repo: {repo}")
    return repo

def test_github_connection(repo: str) -> bool:
    print("\n" + "=" * 50)
    print("🔄 TEST 1: GitHub API Connection")
    print("=" * 50)

    try:
        files = get_repo_files(repo)
        print(f"✅ Connected to GitHub! Found {len(files)} Python files in '{repo}'")
        for f in files[:3]:
            print(f"   📄 {f['name']}")
        return True
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        return False


def test_fetch_diff(repo: str) -> dict:
    print("\n" + "=" * 50)
    print("🔄 TEST 2: Fetch Latest Commit Diff")
    print("=" * 50)

    try:
        diff = get_latest_commit_diff(repo)
        print(f"✅ Fetched commit : [{diff['sha']}] by {diff['author']}")
        print(f"   Message        : {diff['message'][:60]}...")
        print(f"   Files changed  : {len(diff['files'])}")
        return diff
    except Exception as e:
        print(f"❌ Failed to fetch diff: {e}")
        return None


def test_code_review(diff: dict):
    print("\n" + "=" * 50)
    print("🔄 TEST 3: Code Review Agent")
    print("=" * 50)

    if not diff:
        print("⚠️  Skipping — no diff available")
        return

    try:
        print("🤖 Running Code Review Agent (this may take 20-40 seconds)...")
        result = run_code_review(diff)

        print("\n" + "─" * 50)
        print("📋 CODE REVIEW OUTPUT:")
        print("─" * 50)
        print(result)

        # ── Evaluation ──────────────────────────────────
        print("\n" + "─" * 50)
        print("📊 EVALUATION:")

        result_lower = result.lower()
        checks = {
            "Has Summary section"    : "summary"    in result_lower,
            "Has Bugs section"       : "bug"         in result_lower,
            "Has Security section"   : "security"    in result_lower,
            "Has Suggestions section": "suggestion"  in result_lower,
            "Has Overall Score"      : any(w in result_lower for w in
                                           ["score", "excellent", "good",
                                            "needs work", "poor"]),
            "Response is detailed"   : len(result) > 300,
        }

        passed = 0
        for check, ok in checks.items():
            print(f"  {'✅' if ok else '❌'} {check}")
            if ok:
                passed += 1

        print(f"\n🏆 Score: {passed}/{len(checks)} checks passed")

        if passed >= 4:
            print("\n✅ MODULE 2 TEST PASSED — Code Agent is working!")
        else:
            print("\n⚠️  Partial pass — review the output above")

    except Exception as e:
        print(f"❌ Code review agent failed: {e}")


if __name__ == "__main__":
    test_openrouter()
    print("🚀 Starting Module 2 Tests...\n")
    
    repo = get_repo_from_user()

    github_ok = test_github_connection(repo)
    if github_ok:
        diff = test_fetch_diff(repo)
        test_code_review(diff)

    print("\n✅ Done! Check results above.")