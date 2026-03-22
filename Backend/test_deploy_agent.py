import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from tools.github_tool import parse_github_url, get_repo_files, get_file_content
from agents.deploy_agent import run_deploy_agent


def get_repo_from_user():
    print("=" * 50)
    print("🔗 Enter GitHub Repository")
    print("=" * 50)
    print("Example: https://github.com/sakshi2310/Review-Analysis-Auto-Response-System")
    print()
    url  = input("📎 Paste GitHub URL here: ").strip()
    repo = parse_github_url(url)
    print(f"✅ Parsed repo: {repo}")
    return repo, url


def test_deploy_pipeline(repo: str, repo_url: str, filename: str, content: str):
    print("\n" + "=" * 50)
    print("🔄 TEST: Full Deploy Pipeline")
    print("=" * 50)

    try:
        result = run_deploy_agent(repo_url, content, filename)

        print("\n" + "─" * 50)
        print("📋 DEPLOYMENT REPORT:")
        print("─" * 50)
        print(result["report"])

        live_url = result.get("live_url", "N/A")
        if live_url and live_url != "N/A":
            print(f"\n🌐 LIVE URL: {live_url}")

        print("\n" + "─" * 50)
        print("📊 EVALUATION:")

        checks = {
            "Dockerfile generated"  : len(result["dockerfile"]) > 50,
            "Dockerfile saved"      : os.path.exists("generated_tests/Dockerfile"),
            "Deployment attempted"  : result["deploy"]["status"] is not None,
            "Got live URL"          : live_url not in ["N/A", None] and len(str(live_url)) > 10,
            "Report generated"      : len(result["report"]) > 100,
            "No crash during deploy": True,
        }

        passed = 0
        for check, ok in checks.items():
            print(f"  {'✅' if ok else '❌'} {check}")
            if ok:
                passed += 1

        print(f"\n🏆 Score: {passed}/{len(checks)} checks passed")

        if passed >= 4:
            print("\n✅ MODULE 4 TEST PASSED — Deploy Agent is working!")
        else:
            print("\n⚠️  Partial pass — check output above")

        return result

    except Exception as e:
        print(f"❌ Deploy agent failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Starting Module 4 Tests...\n")

    repo, repo_url = get_repo_from_user()
    files          = get_repo_files(repo)

    if not files:
        print("⚠️  No Python files found — using sample code")
        filename = "app.py"
        content  = "# Sample app\n"
    else:
        target   = files[0]
        filename = target["name"]
        content  = get_file_content(target["download_url"])
        print(f"✅ Using file: {filename}")

    test_deploy_pipeline(repo, repo_url, filename, content)

    print("\n✅ Done! Check results above.")