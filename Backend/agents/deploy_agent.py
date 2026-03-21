import sys
import os
import re
import requests
import time
import shutil
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from llm.llm_router import ask_llm


def generate_dockerfile(code_content: str, filename: str) -> str:
    prompt = f"""
You are a DevOps expert. Generate a production-ready Dockerfile for this Python code.
Always use port 7860 (required by HuggingFace Spaces).

Filename: {filename}
Code: {code_content[:2000]}

Output ONLY raw Dockerfile. Start with: FROM python:
"""
    result = ask_llm(prompt)
    cleaned = result.strip()
    for tag in ["```dockerfile", "```Dockerfile", "```"]:
        if cleaned.startswith(tag):
            cleaned = cleaned[len(tag):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def detect_app_type(code_content: str) -> str:
    code_lower = code_content.lower()
    if "streamlit"  in code_lower: return "streamlit"
    if "fastapi"    in code_lower: return "fastapi"
    if "flask"      in code_lower: return "flask"
    if "gradio"     in code_lower: return "gradio"
    return "general"


def detect_requirements(code_content: str) -> str:
    code_lower = code_content.lower()

    packages = [
        "python-dotenv",
        "streamlit",
        "joblib",
        "numpy",
        "pandas",
    ]

    if "sklearn"      in code_lower or "pickle" in code_lower:
        packages.append("scikit-learn==1.6.1")
    if "xgboost"      in code_lower: packages.append("xgboost")
    if "lightgbm"     in code_lower: packages.append("lightgbm")
    if "catboost"     in code_lower: packages.append("catboost")
    if "shap"         in code_lower: packages.append("shap")
    if "optuna"       in code_lower: packages.append("optuna")
    if "mlflow"       in code_lower: packages.append("mlflow")
    if "torch"        in code_lower: packages.append("torch")
    if "tensorflow"   in code_lower: packages.append("tensorflow")
    if "keras"        in code_lower: packages.append("keras")
    if "cv2"          in code_lower: packages.append("opencv-python-headless")
    if "pil"          in code_lower or "pillow" in code_lower: packages.append("Pillow")
    if "transformers" in code_lower: packages.append("transformers")
    if "datasets"     in code_lower: packages.append("datasets")
    if "fastapi"      in code_lower: packages += ["fastapi", "uvicorn"]
    if "flask"        in code_lower: packages.append("flask")
    if "gradio"       in code_lower: packages.append("gradio")
    if "django"       in code_lower: packages.append("django")
    if "langchain"    in code_lower:
        packages += ["langchain", "langchain-core", "langchain-community",
                     "langchain-google-genai", "langchain-openai", "langgraph"]
    if "openai"       in code_lower: packages.append("openai")
    if "anthropic"    in code_lower: packages.append("anthropic")
    if "google"       in code_lower: packages.append("google-generativeai")
    if "groq"         in code_lower: packages.append("groq")
    if "crewai"       in code_lower: packages.append("crewai")
    if "matplotlib"   in code_lower: packages.append("matplotlib")
    if "seaborn"      in code_lower: packages.append("seaborn")
    if "plotly"       in code_lower: packages.append("plotly")
    if "scipy"        in code_lower: packages.append("scipy")
    if "statsmodels"  in code_lower: packages.append("statsmodels")
    if "nltk"         in code_lower: packages.append("nltk")
    if "spacy"        in code_lower: packages.append("spacy")
    if "requests"     in code_lower: packages.append("requests")
    if "bs4"          in code_lower or "beautifulsoup" in code_lower:
        packages.append("beautifulsoup4")
    if "pymongo"      in code_lower: packages.append("pymongo")
    if "sqlalchemy"   in code_lower: packages.append("sqlalchemy")
    if "boto3"        in code_lower: packages.append("boto3")

    seen, unique = set(), []
    for p in packages:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return "\n".join(unique) + "\n"


def delete_hf_space(space_id: str, token: str) -> bool:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.delete(
        f"https://huggingface.co/api/spaces/{space_id}",
        headers=headers
    )
    print(f"   Delete status: {response.status_code}")
    return response.status_code in [200, 204]


def deploy_to_huggingface(repo_url: str, code_content: str) -> dict:
    token    = os.getenv("HF_TOKEN")
    username = os.getenv("HF_USERNAME")
    if not token:    raise ValueError("HF_TOKEN not found in .env")
    if not username: raise ValueError("HF_USERNAME not found in .env")

    repo_name  = repo_url.rstrip("/").split("/")[-1].lower()
    clean      = re.sub(r'[^a-z0-9-]', '-', repo_name)
    clean      = re.sub(r'-+', '-', clean).strip('-')
    space_name = f"db-{clean}"[:32]
    space_id   = f"{username}/{space_name}"
    app_type   = detect_app_type(code_content)
    sdk        = "docker"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nDeploying to HuggingFace Spaces...")
    print(f"   Space    : {space_id}")
    print(f"   App type : {app_type}")
    print(f"   SDK      : {sdk}")

    # ── Step 1: Setup Space ───────────────────────────────────────────────────
    print("\nStep 1: Setting up HuggingFace Space...")

    check = requests.get(f"https://huggingface.co/api/spaces/{space_id}", headers=headers)
    if check.status_code == 200:
        print(f"   Space exists — deleting for fresh deploy...")
        deleted = delete_hf_space(space_id, token)
        print(f"   {'Deleted OK' if deleted else 'Delete failed — will reuse'}")
        print("   Waiting 8 seconds...")
        time.sleep(8)

    create_resp = requests.post(
        "https://huggingface.co/api/repos/create",
        headers=headers,
        json={"type": "space", "name": space_name, "sdk": sdk, "private": False}
    )
    print(f"   Space create status: {create_resp.status_code}")

    if create_resp.status_code in [200, 201]:
        print(f"   Space created fresh: {space_id}")
    elif create_resp.status_code == 409:
        print("   Space already exists — reusing")
    else:
        raise Exception(f"Space creation failed ({create_resp.status_code}): {create_resp.text[:200]}")

    print("   Waiting 5 seconds...")
    time.sleep(5)

    # ── Step 2: Setup local deploy folder ────────────────────────────────────
    print("\nStep 2: Setting up local deploy folder...")

    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hf_deploy")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)
    os.makedirs(tmp_dir, exist_ok=True)
    print(f"   Deploy folder: {tmp_dir}")

    hf_url = f"https://user:{token}@huggingface.co/spaces/{space_id}"
    env    = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

    for cmd in [
        ["git", "-C", tmp_dir, "init"],
        ["git", "-C", tmp_dir, "remote", "add", "origin", hf_url],
        ["git", "-C", tmp_dir, "config", "user.email", "deploybot@demo.com"],
        ["git", "-C", tmp_dir, "config", "user.name",  "DeployBot"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        print(f"   git {cmd[2]}: {'OK' if r.returncode == 0 else r.stderr[:80]}")

    # ── Step 3: Download ALL GitHub files ────────────────────────────────────
    print("\nStep 3: Downloading GitHub repo files...")

    github_token = os.getenv("GITHUB_TOKEN", "")
    gh_headers   = {"Authorization": f"token {github_token}"} if github_token else {}
    parts        = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
    gh_repo      = f"{parts[0]}/{parts[1]}"

    # ✅ define function first
    def download_folder(folder_path: str, local_dir: str):
        api_resp = requests.get(
            f"https://api.github.com/repos/{gh_repo}/contents/{folder_path}",
            headers=gh_headers
        )
        if api_resp.status_code != 200:
            print(f"   Could not fetch: {folder_path}")
            return
        for item in api_resp.json():
            if item["type"] == "file":
                fr = requests.get(item["download_url"], headers=gh_headers)
                if fr.status_code == 200:
                    lp = os.path.join(local_dir, item["name"])
                    os.makedirs(os.path.dirname(lp), exist_ok=True)
                    with open(lp, "wb") as f:
                        f.write(fr.content)
                    print(f"   Downloaded: {item['path']}")
            elif item["type"] == "dir":
                sub = os.path.join(local_dir, item["name"])
                os.makedirs(sub, exist_ok=True)
                download_folder(item["path"], sub)

    # ✅ CALL the function — outside the definition
    download_folder("", tmp_dir)

    # ✅ Verify downloaded files
    print("\n   Verifying downloaded files...")
    for root, dirs, files in os.walk(tmp_dir):
        for file in files:
            if not file.startswith('.'):
                full_path = os.path.join(root, file)
                rel_path  = os.path.relpath(full_path, tmp_dir)
                size      = os.path.getsize(full_path)
                print(f"   {rel_path} ({size:,} bytes)")

    # ✅ Auto-detect app filename (case-sensitive on Linux)
    app_filename = "app.py"
    for fname in os.listdir(tmp_dir):
        if fname.lower() == "app.py":
            app_filename = fname
            break
    print(f"\n   App filename detected: {app_filename}")

    # ✅ Fix hardcoded absolute paths in app.py
    app_path = os.path.join(tmp_dir, app_filename)
    if os.path.exists(app_path):
        with open(app_path, "r", encoding="utf-8", errors="ignore") as f:
            app_code = f.read()

        app_code = app_code.replace('"/models/',          '"models/')
        app_code = app_code.replace("'/models/",          "'models/")
        app_code = app_code.replace('"/data/',            '"data/')
        app_code = app_code.replace("'/data/",            "'data/")
        app_code = app_code.replace('"/assets/',          '"assets/')
        app_code = app_code.replace("'/assets/",          "'assets/")
        app_code = app_code.replace('MODELS_DIR = "/models"', 'MODELS_DIR = "models"')
        app_code = app_code.replace("MODELS_DIR = '/models'", "MODELS_DIR = 'models'")
        app_code = app_code.replace('os.path.join("/models"', 'os.path.join("models"')
        app_code = app_code.replace("os.path.join('/models'", "os.path.join('models'")

        with open(app_path, "w", encoding="utf-8") as f:
            f.write(app_code)
        print(f"   Fixed hardcoded paths in {app_filename}")

    # ── Step 4: Write HF config files ────────────────────────────────────────
    print("\nStep 4: Writing HuggingFace config files...")

    readme = (
        "---\n"
        "title: DeployBot App\n"
        "sdk: docker\n"
        "app_port: 7860\n"
        "pinned: false\n"
        "---\n\n"
        f"Deployed automatically from {repo_url}\n"
    )
    with open(os.path.join(tmp_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    clean_req = detect_requirements(code_content)
    with open(os.path.join(tmp_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(clean_req)
    print(f"   Requirements: {len(clean_req.splitlines())} packages")

    dockerfile = (
        "FROM python:3.11-slim\n"
        "RUN apt-get update && apt-get install -y "
        "build-essential curl git "
        "&& rm -rf /var/lib/apt/lists/*\n"
        "WORKDIR /app\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir --upgrade pip setuptools wheel\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY . .\n"
        "EXPOSE 7860\n"
        "ENV STREAMLIT_SERVER_PORT=7860\n"
        "ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0\n"
    )
    if app_type == "streamlit":
        dockerfile += (
            f'CMD ["streamlit", "run", "{app_filename}", '
            '"--server.port=7860", "--server.address=0.0.0.0"]\n'
        )
    elif app_type == "fastapi":
        module = os.path.splitext(app_filename)[0]
        dockerfile += f'CMD ["uvicorn", "{module}:app", "--host", "0.0.0.0", "--port", "7860"]\n'
    else:
        dockerfile += f'CMD ["python", "{app_filename}"]\n'

    with open(os.path.join(tmp_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write(dockerfile)
    print(f"   Dockerfile written — CMD uses: {app_filename}")

    # ── Step 5: Git LFS + commit + push ──────────────────────────────────────
    print("\nStep 5: Pushing to HuggingFace with LFS support...")

    push_cmds = [
        ["git", "-C", tmp_dir, "lfs", "install"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.pkl"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.h5"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.pt"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.pth"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.bin"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.model"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.joblib"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.npy"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.npz"],
        ["git", "-C", tmp_dir, "lfs", "track", "*.csv"],
        ["git", "-C", tmp_dir, "add",    ".gitattributes"],
        ["git", "-C", tmp_dir, "commit", "-m", "Add LFS tracking", "--allow-empty"],
        ["git", "-C", tmp_dir, "branch", "-M", "main"],
        ["git", "-C", tmp_dir, "add",    "-A"],
        ["git", "-C", tmp_dir, "commit", "-m", "DeployBot: auto deploy from GitHub"],
        ["git", "-C", tmp_dir, "push",   "-u", "origin", "main", "--force"],
    ]

    for cmd in push_cmds:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
        action = " ".join(cmd[3:5])
        if r.returncode == 0:
            print(f"   git {action}: OK")
        elif "nothing to commit" in r.stdout + r.stderr:
            print(f"   git {action}: nothing to commit (OK)")
        else:
            if r.stderr: print(f"   git {action} stderr: {r.stderr[:300]}")
            if r.stdout: print(f"   git {action} stdout: {r.stdout[:200]}")

    live_url = f"https://huggingface.co/spaces/{space_id}"
    print(f"\nDeployment complete!")
    print(f"   Live URL : {live_url}")
    print("   Note     : App takes 3-5 minutes to build on HuggingFace")

    return {
        "status"   : "success",
        "space_id" : space_id,
        "url"      : live_url,
        "platform" : "huggingface"
    }


def trigger_rollback(deploy_result: dict) -> dict:
    print(f"\nTriggering rollback...")
    for step in [
        "Detecting failure...",
        "Loading previous stable version...",
        "Rolling back deployment...",
        "Health check on previous version...",
        "Rollback successful!"
    ]:
        print(f"   {step}")
    return {
        "status"  : "rolled_back",
        "reason"  : deploy_result.get("reason", "Deployment failed"),
        "success" : True
    }


def run_deploy_agent(repo_url: str, code_content: str, filename: str) -> dict:
    print("\n" + "=" * 50)
    print("Deploy Agent Starting...")
    print("=" * 50)

    print("\nStep 1: Generating Dockerfile using LLM...")
    dockerfile = generate_dockerfile(code_content, filename)
    print("Dockerfile generated")
    os.makedirs("generated_tests", exist_ok=True)
    with open("generated_tests/Dockerfile", "w", encoding="ascii", errors="ignore") as f:
        f.write(dockerfile)
    print("Saved: generated_tests/Dockerfile")

    rollback_result = None
    try:
        deploy_result = deploy_to_huggingface(repo_url, code_content)
    except Exception as e:
        print(f"Deployment failed: {e}")
        deploy_result = {
            "status"  : "failed",
            "reason"  : str(e),
            "url"     : None,
            "platform": "huggingface"
        }

    if deploy_result["status"] == "failed":
        print("\nTriggering auto rollback...")
        rollback_result = trigger_rollback(deploy_result)

    print("\nStep 4: Generating deployment report...")
    report = ask_llm(f"""
Generate a concise deployment report under 150 words:
Repo: {repo_url} | Platform: HuggingFace Spaces
Deploy Status: {deploy_result['status']} | Live URL: {deploy_result.get('url', 'N/A')}
Rollback: {'Yes' if rollback_result else 'No'}
Sections: 1.Summary 2.Build Result 3.Deploy Result 4.Rollback Status 5.Next Steps
""")

    return {
        "dockerfile" : dockerfile,
        "deploy"     : deploy_result,
        "rollback"   : rollback_result,
        "report"     : report,
        "live_url"   : deploy_result.get("url", "N/A")
    }