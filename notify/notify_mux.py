import json

#!/usr/bin/env python3
import os
import pathlib
import sys

from notify_line_messaging import send_line
from notify_slack import send_slack

# moved: from notify_line_messaging import send_line
# moved: from notify_slack import send_slack

# moved: from notify_line_messaging import send_line
# moved: from notify_slack import send_slack


# --- ensure local imports ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

BASE = os.path.expanduser("~/WANSTAGE")
ENV_PATH = os.path.join(BASE, ".env")


def load_env_file():
    if not os.path.exists(ENV_PATH):
        return {}
    out = {}
    for line in pathlib.Path(ENV_PATH).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip("'").strip('"')
    return out


# ensure env vars from .env if not exported
envf = load_env_file()
for k in ("LINE_CHANNEL_ACCESS_TOKEN", "LINE_TO_USER", "SLACK_WEBHOOK_URL"):
    if envf.get(k) and not os.getenv(k):
        os.environ[k] = envf[k]

# moved to top: from notify_line_messaging import send_line
# moved to top: from notify_slack import send_slack


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "WANSTAGE notify"
    ok1, log1 = send_line(msg)
    ok2, log2 = send_slack(msg)
    print(
        json.dumps(
            {"line": {"ok": ok1, "log": log1}, "slack": {"ok": ok2, "log": log2}},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
