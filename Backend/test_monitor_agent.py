import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from agents.monitor_agent import run_monitor_agent


def get_url_from_user() -> str:
    print("=" * 50)
    print("🔗 Enter Deployed App URL to Monitor")
    print("=" * 50)
    print("Examples:")
    print("  https://huggingface.co/spaces/username/app")
    print("  http://localhost:8000")
    print("  https://your-app.up.railway.app")
    print()
    url = input("📎 Paste URL here: ").strip()
    return url


def test_health_check(url: str):
    print("\n" + "=" * 50)
    print("🔄 TEST 1: Health Check")
    print("=" * 50)

    from agents.monitor_agent import check_app_health
    health = check_app_health(url, retries=3)

    print(f"\n   Overall Status : {health['status']}")
    print(f"   Healthy Checks : {health['healthy_count']}/{health['total_checks']}")
    print(f"   Avg Response   : {health['avg_response_ms']}ms")

    return health


def test_full_monitor(url: str):
    print("\n" + "=" * 50)
    print("🔄 TEST 2: Full Monitor Pipeline")
    print("=" * 50)

    try:
        result = run_monitor_agent(url, auto_rollback=True)

        print("\n" + "─" * 50)
        print("📋 MONITORING REPORT:")
        print("─" * 50)
        print(result["report"])

        # ── Evaluation ──────────────────────────────────
        print("\n" + "─" * 50)
        print("📊 EVALUATION:")

        checks = {
            "Health check ran"       : result["health"]["total_checks"] > 0,
            "Metrics analyzed"       : result["metrics"]["availability"] is not None,
            "Performance rated"      : result["metrics"]["performance"] in
                                       ["Excellent", "Good", "Slow", "Critical"],
            "Rollback logic works"   : result["rollback"] is not None
                                       or result["health"]["healthy"],
            "Report generated"       : len(result["report"]) > 50,
            "Status determined"      : result["status"] in ["healthy", "unhealthy"],
        }

        passed = 0
        for check, ok in checks.items():
            print(f"  {'✅' if ok else '❌'} {check}")
            if ok:
                passed += 1

        print(f"\n🏆 Score: {passed}/{len(checks)} checks passed")

        if passed >= 4:
            print("\n✅ MODULE 5 TEST PASSED — Monitor Agent is working!")
        else:
            print("\n⚠️  Partial pass — check output above")

        return result

    except Exception as e:
        print(f"❌ Monitor agent failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Starting Module 5 Tests...\n")

    url = get_url_from_user()

    test_health_check(url)
    test_full_monitor(url)

    print("\n✅ Done! Check results above.")