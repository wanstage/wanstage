#!/usr/bin/env python3
"""Read-only validator for BOATRACE/WANSTAGE control separation.

This validator performs static checks only. It does not create, modify, move,
or delete repository files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CONTRACT_RELATIVE_PATH = Path(
    "governance/domains/control_separation/"
    "boatrace_wanstage_control_separation.contract.json"
)
TEXT_SUFFIXES = {
    ".py", ".sh", ".zsh", ".bash", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".md", ".txt", ".csv", ".ps1",
}
SKIP_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
ROOT_SCAN_PATTERNS = (
    re.compile(r"find\s+[^\n]*(?:WANSTAGE_NEW|workspace_root|ROOT)[^\n]*-type\s+f", re.I),
    re.compile(r"rglob\s*\(\s*['\"]\*", re.I),
    re.compile(r"glob\s*\(\s*['\"]\*\*/\*", re.I),
)


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_relative(raw: str) -> str:
    return raw.replace("\\", "/").lstrip("./")


def is_under_prefix(path: str, prefix: str) -> bool:
    return normalize_relative(path).startswith(normalize_relative(prefix))


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == "MANIFEST.sha256":
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def validate_contract(contract: dict) -> list[Finding]:
    findings: list[Finding] = []
    required_layers = {
        "PATH_NAMESPACE",
        "MANIFEST_NAMESPACE",
        "SHA_NAMESPACE",
        "EXECUTION_AUTHORITY",
        "EVIDENCE_REGISTRY",
    }
    actual_layers = set(contract.get("separation_layers", []))
    if actual_layers != required_layers:
        findings.append(
            Finding("CONTRACT_LAYER_MISMATCH", str(CONTRACT_RELATIVE_PATH), repr(sorted(actual_layers)))
        )

    rules = contract.get("rules", {})
    fail_closed_rules = (
        "boatrace_recursive_scan_from_workspace_root",
        "boatrace_glob_all_json",
        "boatrace_glob_all_sha256",
        "boatrace_glob_all_reports",
        "manifest_cross_domain_entry_allowed",
        "manifest_parent_directory_escape_allowed",
        "manifest_absolute_foreign_path_allowed",
        "cross_domain_sha_reuse_allowed",
        "sha_lookup_by_hash_only",
        "sha_copied_from_chat_allowed",
        "sha_copied_from_other_manifest_allowed",
        "implicit_domain_inference_allowed",
        "shared_execution_entrypoint_allowed",
        "shared_evidence_registry_allowed",
    )
    for key in fail_closed_rules:
        if rules.get(key) is not False:
            findings.append(Finding("CONTRACT_RULE_NOT_FAIL_CLOSED", str(CONTRACT_RELATIVE_PATH), key))
    return findings


def validate_manifests(root: Path, contract: dict) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    checked = 0
    for domain_name, domain in contract["domains"].items():
        manifest_rel = Path(domain["manifest"])
        manifest_path = root / manifest_rel
        if not manifest_path.exists():
            continue
        checked += 1
        allowed_root = normalize_relative(domain["control_root"]) + "/"
        for line_no, raw_line in enumerate(read_text(manifest_path).splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                findings.append(Finding("MANIFEST_ENTRY_INVALID", str(manifest_rel), f"line={line_no}"))
                continue
            _, raw_listed_path = parts
            raw_normalized = raw_listed_path.replace("\\", "/")
            if raw_normalized.startswith("/") or "../" in raw_normalized:
                findings.append(Finding("MANIFEST_PATH_ESCAPE", str(manifest_rel), raw_listed_path))
                continue
            listed_path = normalize_relative(raw_listed_path)
            if not listed_path.startswith(allowed_root):
                findings.append(
                    Finding("CROSS_DOMAIN_MANIFEST_ENTRY", str(manifest_rel), f"{domain_name}:{listed_path}")
                )
    return findings, checked


def validate_references(root: Path, contract: dict) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    scanned = 0
    boatrace = contract["domains"]["BOATRACE"]
    wanstage = contract["domains"]["WANSTAGE_CONTROL"]
    denied = tuple(normalize_relative(p) for p in boatrace["denied_path_prefixes"])
    boatrace_allowed = tuple(
        normalize_relative(p) for p in boatrace["allowed_path_prefixes"]
    )
    foreign_registry = normalize_relative(wanstage["evidence_registry"])
    foreign_manifest = normalize_relative(wanstage["manifest"])

    for path in iter_text_files(root):
        relative = normalize_relative(str(path.relative_to(root)))
        if relative == normalize_relative(str(CONTRACT_RELATIVE_PATH)):
            continue
        text = read_text(path)
        scanned += 1

        if not any(is_under_prefix(relative, prefix) for prefix in boatrace_allowed):
            continue

        for prefix in denied:
            if prefix in text:
                findings.append(Finding("CROSS_DOMAIN_PATH_REFERENCE", relative, prefix))
        if foreign_manifest in text:
            findings.append(Finding("FOREIGN_MANIFEST_REFERENCE", relative, foreign_manifest))
        if foreign_registry in text:
            findings.append(Finding("SHARED_EVIDENCE_REGISTRY", relative, foreign_registry))
        for pattern in ROOT_SCAN_PATTERNS:
            if pattern.search(text):
                findings.append(Finding("UNSCOPED_RECURSIVE_SCAN", relative, pattern.pattern))
                break
    return findings, scanned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.environ.get("WANSTAGE_ROOT", "."))
    parser.add_argument("--json", action="store_true", dest="emit_json")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    contract_path = root / CONTRACT_RELATIVE_PATH
    if not contract_path.is_file():
        print("EXECUTION_STATUS=FAILED")
        print("DATA_STATUS=MISSING")
        print(f"MISSING_CONTRACT={contract_path}")
        print("DECISION=NO-GO")
        return 2

    contract = json.loads(read_text(contract_path))
    findings = validate_contract(contract)
    manifest_findings, manifest_count = validate_manifests(root, contract)
    reference_findings, scanned_count = validate_references(root, contract)
    findings.extend(manifest_findings)
    findings.extend(reference_findings)

    result = {
        "validator_mode": "READ_ONLY_STATIC",
        "workspace_root": str(root),
        "contract_path": str(CONTRACT_RELATIVE_PATH),
        "contract_sha256": sha256_file(contract_path),
        "text_files_scanned": scanned_count,
        "manifests_checked": manifest_count,
        "finding_count": len(findings),
        "findings": [finding.__dict__ for finding in findings],
        "boatrace_wanstage_control_separation_complete": len(findings) == 0,
        "decision": "GO" if not findings else "NO-GO",
    }

    if args.emit_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("EXECUTION_STATUS=COMPLETE")
        print("INVESTIGATION_STATUS=RESOLVED")
        print("DATA_STATUS=VERIFIED" if not findings else "DATA_STATUS=INVALID")
        for key, value in result.items():
            if key != "findings":
                print(f"{key.upper()}={value}")
        for finding in findings:
            print(f"FINDING={finding.code}|{finding.path}|{finding.detail}")
        print(f"DECISION={result['decision']}")

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
