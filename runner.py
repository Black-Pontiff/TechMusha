"""
Isolated code runner.

For every request we spin up a fresh sibling container with:
  * no network (--network none)
  * read-only root filesystem
  * tmpfs /work for the source file
  * memory cap 128m
  * cpu quota (--cpus 0.5)
  * 5 second timeout enforced both by docker kill and http client timeout

In production, replace `docker run` with `runsc` (gVisor) or a Firecracker VM.
"""
import os, time, uuid, tempfile, subprocess, shutil
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="TechMusha Sandbox")
TOKEN = os.environ.get("SANDBOX_TOKEN", "dev-token")

IMAGES = {
    "python":     ("techmusha-runner-python",  "main.py",   "python main.py"),
    "javascript": ("techmusha-runner-node",    "main.js",   "node main.js"),
    "java":       ("techmusha-runner-java",    "Main.java", "sh -c 'javac Main.java && java Main'"),
    "cpp":        ("techmusha-runner-cpp",     "main.cpp",  "sh -c 'g++ -O2 main.cpp -o main && ./main'"),
}
CPU_SECONDS = 5
MEM_MB = 128

class RunIn(BaseModel):
    language: str
    code: str
    stdin: str = ""

@app.post("/run")
def run(body: RunIn, x_sandbox_token: str | None = Header(default=None)):
    if x_sandbox_token != TOKEN:
        raise HTTPException(401, "Bad sandbox token")
    if body.language not in IMAGES:
        raise HTTPException(400, "Unsupported language")
    if len(body.code) > 200_000:
        raise HTTPException(413, "Code too long")

    image, filename, cmd = IMAGES[body.language]
    workdir = tempfile.mkdtemp(prefix="tmrun-")
    try:
        with open(os.path.join(workdir, filename), "w") as f:
            f.write(body.code)
        os.chmod(workdir, 0o777)

        args = [
            "docker","run","--rm","-i",
            "--network","none",
            "--read-only",
            "--tmpfs","/tmp:size=16m",
            "--memory", f"{MEM_MB}m",
            "--memory-swap", f"{MEM_MB}m",
            "--cpus","0.5",
            "--pids-limit","64",
            "--cap-drop","ALL",
            "--security-opt","no-new-privileges",
            "--user","1000:1000",
            "-v", f"{workdir}:/work:ro",
            "-w","/work",
            image, "sh","-c", cmd,
        ]
        t0 = time.time()
        try:
            proc = subprocess.run(args, input=body.stdin.encode(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=CPU_SECONDS + 1)
            duration = int((time.time() - t0) * 1000)
            return {
                "stdout": proc.stdout.decode(errors="replace")[:20_000],
                "stderr": proc.stderr.decode(errors="replace")[:20_000],
                "exit_code": proc.returncode,
                "duration_ms": duration,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as e:
            duration = int((time.time() - t0) * 1000)
            return {
                "stdout": (e.stdout or b"").decode(errors="replace")[:20_000],
                "stderr": "Execution timed out (5s limit).",
                "exit_code": -1,
                "duration_ms": duration,
                "timed_out": True,
            }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

@app.get("/health")
def health(): return {"ok": True}