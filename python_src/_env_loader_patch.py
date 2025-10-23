import os
import pathlib


def ensure_openai_key():
    if os.environ.get("OPENAI_API_KEY"):
        return
    # $HOME/WANSTAGE/.env → ./../.env の順で見る
    candidates = [
        str(pathlib.Path.home() / "WANSTAGE" / ".env"),
        str((pathlib.Path(__file__).resolve().parent.parent) / ".env"),
    ]
    for p in candidates:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k == "OPENAI_API_KEY" and v:
                        os.environ.setdefault("OPENAI_API_KEY", v)
                        return
        except Exception:
            pass
