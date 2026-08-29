import os, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
env=os.environ.copy()
env["PYTHONPATH"]=str(ROOT/"backend")
env["MODEL_DIR"]=str(ROOT/"models")
env["DATABASE_URL"]=f"sqlite:///{ROOT}/data/runtime/backend_smoke.db"
env["CORS_ORIGINS"]="http://localhost:5173,http://127.0.0.1:5173"
env["TRUSTED_HOSTS"]="localhost,127.0.0.1"
env["TWINGUARD_INGEST_KEY"]="smoke-test"
env["TWINGUARD_NATIVE_ML"]="0"

p=subprocess.Popen(
    [sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8765"],
    cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
)
try:
    for _ in range(80):
        if p.poll() is not None:
            raise SystemExit("FAIL: backend process exited")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8765/health",timeout=.5) as r:
                if r.status==200:
                    print("PASS: backend health endpoint")
                    raise SystemExit(0)
        except Exception:
            time.sleep(.25)
    raise SystemExit("FAIL: backend did not become ready")
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except Exception:p.kill()
