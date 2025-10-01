#!/usr/bin/env zsh
set -Eeuo pipefail

# Usage: wan-clean.sh [-n] [TARGET_DIR]
dry_run=false
if [[ "${1:-}" == "-n" ]]; then dry_run=true; shift; fi

ROOT="${1:-$HOME/WANSTAGE}"
BACKUP_DIR="$ROOT/_secrets_backup"

ts(){ date '+%F %T'; }
log(){ printf '[%s] %s\n' "$(ts)" "$*"; }

[[ -d "$ROOT" ]] || { echo "ERROR: $ROOT not found" >&2; exit 1; }

log "TARGET: $ROOT  (dry-run=$dry_run)"
log "STEP1: backup root-level .env.bak* -> $BACKUP_DIR (0600)"

if [[ "$dry_run" == false ]]; then
  mkdir -p "$BACKUP_DIR"; chmod 700 "$BACKUP_DIR" || true
fi

# root直下の .env.bak* を退避（元は残す）
if compgen -G "$ROOT/.env.bak*" >/dev/null 2>&1; then
  if [[ "$dry_run" == true ]]; then
    ls -l "$ROOT"/.env.bak* || true
  else
    find "$ROOT" -maxdepth 1 -type f -name '.env.bak*' -print0 \
      | xargs -0 -I{} install -m 600 -v "{}" "$BACKUP_DIR"/
  fi
else
  log "no .env.bak* at root"
fi

log "STEP2: delete tmp/swp/bak files (excluding $BACKUP_DIR)"

# 削除対象を null 区切りで列挙し、xargs rm で削除（-prune と -delete の衝突を回避）
del_expr=( -type f \( -name '*.tmp' -o -name '*.tmp.*' -o -name '*.swp' -o -name '*.bak' -o -name '*.bak.*' \) ! -name '.env.bak*' )
if [[ "$dry_run" == true ]]; then
  find "$ROOT" -path "$BACKUP_DIR" -prune -o \( "${del_expr[@]}" -print \)
else
  find "$ROOT" -path "$BACKUP_DIR" -prune -o \( "${del_expr[@]}" -print0 \) \
    | xargs -0 -r rm -f
fi

log "STEP3: report residual matches (should be empty except backups)"
find "$ROOT" \( -name '*.tmp' -o -name '*.tmp.*' -o -name '*.swp' -o -name '*.bak' -o -name '*.bak.*' \) -print \
  | sed 's/^/RESIDUAL: /' || true

log "DONE. If only _secrets_backup/*.env.bak* remains, it's clean ✓"
