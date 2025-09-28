#!/usr/bin/env zsh
set -euo pipefail
echo "== GH CLI =="
gh auth status || true
echo "== CF Secrets (GH Actions) =="
gh secret list | grep -E 'CF_API_TOKEN|CF_ACCOUNT_ID' || echo "GH Secrets 未設定の可能性"
echo "== Wrangler =="
npx -y wrangler@3 --version || true
echo "== Repo remote =="
git remote -v
echo "== SSH check =="
ssh -T git@github.com || true
