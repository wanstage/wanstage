#!/usr/bin/env zsh
set -e
echo "[1] python path: $(which python)"
python -V || true
echo "[2] pip path: $(which pip)"
pip -V || true
echo "[3] typing_extensions import check"
python - <<'PY'
try:
    import typing_extensions
    print("typing_extensions: OK")
except Exception as e:
    print("typing_extensions: NG ->", e)
    raise SystemExit(1)
PY
echo "[4] run hello_env.py"
python /Users/okayoshiyuki/WANSTAGE/hello_env.py
echo "[OK] doctor passed"
