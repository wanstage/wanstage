set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y jq zip
python -m pip install --upgrade pip
python -m pip install pre-commit black ruff \
  openai requests python-dotenv gspread google-auth google-auth-oauthlib pandas
npm --version >/dev/null 2>&1 || true
