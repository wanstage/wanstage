set -euo pipefail
VENV="/Users/okayoshiyuki/WANSTAGE/venv"
source "$VENV/bin/activate"
python -V
pip install --upgrade pip
pip install typing_extensions debugpy
echo "[OK] venv repaired."
