import os, hmac, hashlib, time, subprocess
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

load_dotenv()
SIGNING_SECRET = (os.getenv("SLACK_SIGNING_SECRET") or "").encode()
PORT = int(os.getenv("PORT", "8088"))
ROOT = os.getenv("ROOT_DIR") or os.path.expanduser("~/WANSTAGE")

CMD_MAP = {
    "post": os.getenv("CMD_POST", f"{ROOT}/full_auto_post_flow.sh"),
    "flex": os.getenv("CMD_FLEX", f"{ROOT}/wanstage_flex_notify_and_dbgen.sh"),
}

app = FastAPI()

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

def verify_slack(req: Request, body: bytes):
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        raise HTTPException(status_code=401, detail="no headers")
    if abs(time.time() - int(ts)) > 60*5:
        raise HTTPException(status_code=401, detail="timestamp expired")
    basestring = b"v0:" + ts.encode() + b":" + body
    digest = "v0=" + hmac.new(SIGNING_SECRET, basestring, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, sig):
        raise HTTPException(status_code=401, detail="bad signature")

def run_allowed(cmd_key: str):
    path = CMD_MAP.get(cmd_key)
    if not path:
        return f"NG: unknown command '{cmd_key}'"
    if not os.path.exists(path):
        return f"NG: script not found: {path}"
    subprocess.Popen(
        ["/bin/bash","-lc",f"source {ROOT}/.env 2>/dev/null || true; {path} >> {ROOT}/logs/remote_exec.log 2>&1"]
    )
    return f"OK: started {cmd_key}"

@app.post("/slack/command", response_class=PlainTextResponse)
async def slack_command(request: Request):
    body = await request.body()
    verify_slack(request, body)
    form = dict((await request.form()).items())
    text = (form.get("text") or "").strip()
    key = (text.split() or [""])[0].lower()
    return run_allowed(key)
