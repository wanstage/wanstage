#!/usr/bin/env python3
"""WANSTAGE_NEW Mac HQ defensive adversary audit.

Read-only local audit. No exploit, auth attempt, credential access,
configuration change, persistence, packet capture, or external scanning.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_ID = "wanstage_new_mac_hq_adversary_audit"
DEFAULT_ROOT = Path.home() / "WANSTAGE_NEW"
STALE_SECONDS = 180


def run(argv: list[str], *, env: dict[str, str] | None = None, timeout: int = 8) -> dict[str, Any]:
    try:
        p = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, check=False, env=env)
        return {"argv": argv, "returncode": p.returncode, "stdout": p.stdout,
                "stderr": p.stderr, "error": None}
    except FileNotFoundError as e:
        return {"argv": argv, "returncode": None, "stdout": "", "stderr": "",
                "error": f"COMMAND_NOT_FOUND:{e.filename}"}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "returncode": None, "stdout": "", "stderr": "",
                "error": "TIMEOUT"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_route(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("gateway:"):
            out["gateway"] = line.split(":", 1)[1].strip()
        elif line.startswith("interface:"):
            out["interface"] = line.split(":", 1)[1].strip()
    return out


def parse_ps(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    procs: list[dict[str, Any]] = []
    daemons: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*)$", line)
        if not m:
            continue
        pid, ppid, user, etime, command = m.groups()
        row = {"pid": int(pid), "ppid": int(ppid), "user": user,
               "etime": etime, "command": command}
        procs.append(row)
        if "PM2" in command and "God Daemon" in command:
            hm = re.search(r"\(([^)]+)\)", command)
            daemons.append({**row, "pm2_home": hm.group(1) if hm else None})
    return procs, daemons


def parse_lsof(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line in lines[1:] if lines and lines[0].startswith("COMMAND") else lines:
        parts = line.split()
        if len(parts) < 9 or not parts[1].isdigit():
            continue
        endpoint = " ".join(parts[8:]).replace(" (LISTEN)", "")
        pm = re.search(r":(\d+)$", endpoint)
        bind = endpoint.rsplit(":", 1)[0] if pm else endpoint
        out.append({"command": parts[0], "pid": int(parts[1]), "user": parts[2],
                    "endpoint": endpoint, "port": int(pm.group(1)) if pm else None,
                    "all_interfaces": bind in {"*", "0.0.0.0", "::", "[::]"} or bind.startswith("*")})
    return out


def cwd(pid: int) -> str | None:
    r = run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], timeout=3)
    for line in r["stdout"].splitlines():
        if line.startswith("n/"):
            return line[1:]
    return None


def pm2_jlist(pm2_home: Path, daemons: list[dict[str, Any]]) -> dict[str, Any]:
    home = str(pm2_home)
    present = any(d.get("pm2_home") == home for d in daemons)
    if not present:
        return {"pm2_home": home, "daemon_present": False, "processes": []}
    env = os.environ.copy()
    env["PM2_HOME"] = home
    env["PM2_SILENT"] = "true"
    r = run(["pm2", "jlist"], env=env)
    try:
        raw = json.loads(r["stdout"]) if r["returncode"] == 0 else []
    except json.JSONDecodeError:
        raw = []
    processes = []
    for item in raw if isinstance(raw, list) else []:
        env_data = item.get("pm2_env", {}) if isinstance(item, dict) else {}
        processes.append({"name": item.get("name"), "pid": item.get("pid"),
                          "status": env_data.get("status"), "cwd": env_data.get("pm_cwd"),
                          "script": env_data.get("pm_exec_path")})
    return {"pm2_home": home, "daemon_present": True, "processes": processes}


def git_roots(root: Path) -> list[str]:
    found: list[str] = []
    for current, dirs, _files in os.walk(root):
        p = Path(current)
        try:
            depth = len(p.relative_to(root).parts)
        except ValueError:
            continue
        if depth > 4:
            dirs[:] = []
            continue
        if ".git" in dirs:
            found.append(str(p))
            dirs.remove(".git")
    return sorted(found)


def parse_arp(text: str) -> list[dict[str, str]]:
    out = []
    for line in text.splitlines():
        m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at (\S+) on (\S+)", line)
        if m:
            out.append({"ip": m.group(1), "mac": m.group(2), "interface": m.group(3)})
    return out


def identity_evidence(root: Path) -> dict[str, Any]:
    records = []
    inspected = 0
    markers = ("windows", "windows_node", "compute_node", "secondary")
    ip_re = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
    for sub in ("registry", "status", "reports"):
        base = root / "governance" / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json")):
            if inspected >= 1000:
                break
            inspected += 1
            try:
                if path.stat().st_size > 2_000_000:
                    continue
                text = path.read_text(encoding="utf-8")
                json.loads(text)
            except Exception:
                continue
            low = (str(path.relative_to(root)) + " " + text).lower()
            if not any(m in low for m in markers):
                continue
            records.append({"file": str(path.relative_to(root)),
                            "modified_at": dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
                            .isoformat(timespec="seconds").replace("+00:00", "Z"),
                            "ipv4_candidates": sorted(set(ip_re.findall(text)))})
    return {"inspected_json_file_count": inspected, "records": records[:100]}


def path_record(path_id: str, title: str, evidence: list[dict[str, Any]],
                counterevidence: list[dict[str, Any]], missing: list[str]) -> dict[str, Any]:
    if evidence and counterevidence:
        status = "WATCH_CONTRADICTORY_EVIDENCE"
    elif evidence and missing:
        status = "WATCH_HYPOTHESIS"
    elif evidence:
        status = "WATCH_EVIDENCE_REQUIRES_INDEPENDENT_CONFIRMATION"
    else:
        status = "GO_REJECTED_NO_SUPPORTING_EVIDENCE"
    return {"path_id": path_id, "title": title, "status": status,
            "evidence": evidence, "counterevidence": counterevidence,
            "missing_edges": missing}


def collect(root: Path) -> dict[str, Any]:
    route_r = run(["route", "-n", "get", "default"], timeout=3)
    ps_r = run(["ps", "-axo", "pid=,ppid=,user=,etime=,command="], timeout=5)
    _procs, daemons = parse_ps(ps_r["stdout"])
    lsof_r = run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"])
    listeners = parse_lsof(lsof_r["stdout"])
    for item in listeners:
        item["cwd"] = cwd(item["pid"])
    isolated = pm2_jlist(root / "runtime" / "pm2" / "isolated_pm2_home", daemons)
    normal = pm2_jlist(Path.home() / ".pm2", daemons)
    arp_r = run(["arp", "-an"], timeout=5)
    identity = identity_evidence(root) if root.is_dir() else {"records": []}

    facts = {"collected_at_utc": utc_now(), "host": platform.node(),
             "platform": platform.system(), "root": str(root),
             "terminal_role": os.environ.get("WANSTAGE_TERMINAL_ROLE"),
             "default_route": parse_route(route_r["stdout"]),
             "pm2_daemons": daemons, "pm2": {"isolated": isolated, "normal": normal},
             "listeners": listeners, "git_roots": git_roots(root) if root.is_dir() else [],
             "arp": parse_arp(arp_r["stdout"]), "identity_evidence": identity}

    new_pids = {p.get("pid") for p in isolated["processes"]}
    new_all = [x for x in listeners if x.get("pid") in new_pids and x.get("all_interfaces")]
    legacy = [x for x in listeners if str(x.get("cwd") or "").startswith(str(Path.home() / "WANSTAGE"))]
    both_pm2 = isolated["daemon_present"] and normal["daemon_present"]
    identity_ips = sorted({ip for r in identity["records"] for ip in r.get("ipv4_candidates", [])})

    matrix = [
        path_record("PATH_F", "All-interface WANSTAGE_NEW listener", [{"source": "lsof", "fact": new_all}] if new_all else [],
                    [{"source": "pm2", "fact": isolated["processes"]}] if isolated["processes"] else [],
                    ["EXECUTION_EDGE", "IMPACT", "RECOVERY_GAP"]),
        path_record("PATH_G", "Normal and isolated PM2 context confusion", [{"source": "ps", "fact": daemons}] if both_pm2 else [],
                    [{"source": "isolated_pm2", "fact": isolated["processes"]}] if isolated["processes"] else [],
                    ["EXECUTION_EDGE", "IMPACT", "RECOVERY_GAP"]),
        path_record("PATH_H", "Windows Node identity ambiguity", [{"source": "arp", "fact": facts["arp"]}] if len(facts["arp"]) > 2 and not identity_ips else [],
                    [{"source": "registry", "fact": identity_ips}] if identity_ips else [],
                    ["EXECUTION_EDGE", "IMPACT", "RECOVERY_GAP"]),
        path_record("PATH_I", "Local Git binding missing", [{"source": "filesystem", "fact": str(root)}] if not facts["git_roots"] else [],
                    [{"source": "filesystem", "fact": facts["git_roots"]}] if facts["git_roots"] else [],
                    ["EXECUTION_EDGE", "IMPACT"]),
        path_record("PATH_J", "Single watcher blind spot", [{"source": "pm2", "fact": isolated["processes"]}] if len(isolated["processes"]) == 1 else [],
                    [], ["EXECUTION_EDGE", "IMPACT", "RECOVERY_GAP"]),
        path_record("PATH_L", "Legacy WANSTAGE authority contamination", [{"source": "lsof", "fact": legacy}] if legacy else [],
                    [{"source": "isolated_pm2", "fact": isolated["processes"]}] if isolated["processes"] else [],
                    ["EXECUTION_EDGE", "IMPACT", "RECOVERY_GAP"]),
    ]
    decision = "WATCH" if any(x["status"].startswith("WATCH") for x in matrix) else "GO"
    return {"schema_version": "1.0", "tool_id": TOOL_ID, "decision": decision,
            "policy": {"attacker_perspective": "MAXIMUM_HYPOTHESIS_DEPTH",
                       "claim_authority": "EVIDENCE_ONLY",
                       "execution_authority": "DEFENSIVE_READ_ONLY_ONLY",
                       "fail_closed": True, "user_dependency": False},
            "attack_path_matrix": matrix, "facts": facts}


def self_test() -> int:
    sample = path_record("PATH_X", "sample", [{"source": "x", "fact": True}], [], ["EXECUTION_EDGE"])
    assert sample["status"] == "WATCH_HYPOTHESIS"
    print("SELF_TEST=GO")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(os.environ.get("WANSTAGE_ROOT", DEFAULT_ROOT)))
    p.add_argument("--output", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return self_test()
    root = args.root.expanduser().resolve()
    if platform.system() != "Darwin" or not root.is_dir():
        print(json.dumps({"decision": "HOLD_SCOPE_GATE_FAILED", "platform": platform.system(),
                          "root": str(root)}, indent=2))
        return 2
    payload = collect(root)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        out = args.output.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"REPORT={out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
