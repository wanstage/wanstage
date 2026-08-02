#!/usr/bin/env python3
"""Fail-closed read-only BOATRACE/WANSTAGE separation validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

CONTRACT_REL = Path(
    "governance/domains/control_separation/"
    "boatrace_wanstage_control_separation.contract.json"
)
TEXT_SUFFIXES = {
    ".py", ".sh", ".zsh", ".bash", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".md", ".txt", ".csv", ".ps1",
}
SKIP_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
ENTRYPOINT_SUFFIXES = {".py", ".sh", ".zsh", ".bash", ".ps1"}
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ROOT_SCAN_PATTERNS = (
    re.compile(
        r"find\s+[^\n]*(?:WANSTAGE_NEW|workspace_root|ROOT)"
        r"[^\n]*-type\s+f",
        re.I,
    ),
    re.compile(r"rglob\s*\(\s*['\"]\*", re.I),
    re.compile(r"glob\s*\(\s*['\"]\*\*/\*", re.I),
)
BOATRACE_MARKERS = (
    re.compile(
        r"(?im)^\s*(?:DOMAIN|WANSTAGE_DOMAIN)\s*[:=]\s*['\"]?BOATRACE\b"
    ),
    re.compile(r'(?i)"domain"\s*:\s*"BOATRACE"'),
    re.compile(
        r"(?im)^\s*BOATRACE_DOMAIN_CLASSIFICATION\s*=\s*True\b"
    ),
)
BOATRACE_PATH_TOKEN_RE = re.compile(
    r"(?i)(?:^|[/_.-])boatrace(?=$|[/_.-])"
)
NON_BOATRACE_PATH_TOKEN_RE = re.compile(
    r"(?i)(^|[/_.-])non[/_.-]?boatrace(?=$|[/_.-])"
)
DEFAULT_MAX_FINDINGS = 200


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str


def norm(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def under(path: str, prefix: str) -> bool:
    return norm(path).startswith(norm(prefix))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == "MANIFEST.sha256":
            yield path


def validate_contract(contract: dict) -> list[Finding]:
    findings: list[Finding] = []
    required_layers = {
        "PATH_NAMESPACE",
        "MANIFEST_NAMESPACE",
        "SHA_NAMESPACE",
        "EXECUTION_AUTHORITY",
        "EVIDENCE_REGISTRY",
    }
    if set(contract.get("separation_layers", [])) != required_layers:
        findings.append(
            Finding(
                "CONTRACT_LAYER_MISMATCH",
                str(CONTRACT_REL),
                "invalid separation_layers",
            )
        )
    if set(contract.get("domains", {})) != {"BOATRACE", "WANSTAGE_CONTROL"}:
        findings.append(
            Finding(
                "CONTRACT_DOMAIN_MISMATCH",
                str(CONTRACT_REL),
                "domains must be BOATRACE and WANSTAGE_CONTROL",
            )
        )

    fail_closed_rules = (
        "boatrace_recursive_scan_from_workspace_root",
        "boatrace_glob_all_json",
        "boatrace_glob_all_sha256",
        "boatrace_glob_all_reports",
        "boatrace_artifact_outside_domain_root_allowed",
        "required_domain_asset_missing_allowed",
        "manifest_cross_domain_entry_allowed",
        "manifest_parent_directory_escape_allowed",
        "manifest_absolute_foreign_path_allowed",
        "cross_domain_sha_reuse_allowed",
        "cross_domain_evidence_entry_allowed",
        "sha_lookup_by_hash_only",
        "sha_copied_from_chat_allowed",
        "sha_copied_from_other_manifest_allowed",
        "implicit_domain_inference_allowed",
        "shared_execution_entrypoint_allowed",
        "shared_evidence_registry_allowed",
    )
    for key in fail_closed_rules:
        if contract.get("rules", {}).get(key) is not False:
            findings.append(
                Finding("CONTRACT_RULE_NOT_FAIL_CLOSED", str(CONTRACT_REL), key)
            )
    return findings


def required_assets(root: Path, contract: dict):
    findings: list[Finding] = []
    roots_checked = 0
    manifests_checked = 0
    registries_checked = 0

    for domain, config in contract["domains"].items():
        control_root = norm(config["control_root"])
        manifest = norm(config["manifest"])
        registry = norm(config["evidence_registry"])

        if (root / control_root).is_dir():
            roots_checked += 1
        else:
            findings.append(
                Finding("REQUIRED_CONTROL_ROOT_MISSING", control_root, domain)
            )

        if (root / manifest).is_file():
            manifests_checked += 1
        else:
            findings.append(
                Finding("REQUIRED_MANIFEST_MISSING", manifest, domain)
            )

        if (root / registry).is_file():
            registries_checked += 1
        else:
            findings.append(
                Finding(
                    "REQUIRED_EVIDENCE_REGISTRY_MISSING",
                    registry,
                    domain,
                )
            )

    return findings, roots_checked, manifests_checked, registries_checked


def validate_manifests(root: Path, contract: dict) -> list[Finding]:
    findings: list[Finding] = []
    rows: list[tuple[str, str, str]] = []

    for domain, config in contract["domains"].items():
        relative = norm(config["manifest"])
        manifest_path = root / relative
        if not manifest_path.is_file():
            continue

        allowed = norm(config["control_root"]).rstrip("/") + "/"
        for line_number, raw in enumerate(text(manifest_path).splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                findings.append(
                    Finding(
                        "MANIFEST_ENTRY_INVALID",
                        relative,
                        f"line={line_number}",
                    )
                )
                continue

            digest, raw_path = parts
            if not SHA_RE.fullmatch(digest):
                findings.append(
                    Finding(
                        "MANIFEST_SHA256_INVALID",
                        relative,
                        f"line={line_number}",
                    )
                )
                continue

            raw_normalized = raw_path.replace("\\", "/")
            if raw_normalized.startswith("/") or "../" in raw_normalized:
                findings.append(
                    Finding(
                        "MANIFEST_PATH_ESCAPE",
                        relative,
                        f"line={line_number};path={raw_path}",
                    )
                )
                continue

            artifact = norm(raw_path)
            rows.append((domain, digest.lower(), artifact))
            if not artifact.startswith(allowed):
                findings.append(
                    Finding(
                        "CROSS_DOMAIN_MANIFEST_ENTRY",
                        relative,
                        f"{domain}:{artifact}",
                    )
                )

    sha_domains: dict[str, set[str]] = defaultdict(set)
    path_domains: dict[str, set[str]] = defaultdict(set)
    for domain, digest, artifact in rows:
        sha_domains[digest].add(domain)
        path_domains[artifact].add(domain)

    for digest, domains in sha_domains.items():
        if len(domains) > 1:
            findings.append(
                Finding(
                    "CROSS_DOMAIN_SHA_BINDING",
                    "MANIFEST.sha256",
                    f"sha256={digest};domains={','.join(sorted(domains))}",
                )
            )

    for artifact, domains in path_domains.items():
        if (
            len(domains) > 1
            and Path(artifact).suffix.lower() in ENTRYPOINT_SUFFIXES
        ):
            findings.append(
                Finding(
                    "SHARED_EXECUTION_ENTRYPOINT",
                    artifact,
                    f"domains={','.join(sorted(domains))}",
                )
            )

    return findings


def validate_registries(root: Path, contract: dict) -> list[Finding]:
    findings: list[Finding] = []
    sha_domains: dict[str, set[str]] = defaultdict(set)
    configured: dict[str, list[str]] = defaultdict(list)
    resolved: dict[str, list[str]] = defaultdict(list)

    for domain, config in contract["domains"].items():
        relative = norm(config["evidence_registry"])
        registry_path = root / relative
        configured[relative].append(domain)

        if registry_path.exists():
            resolved[str(registry_path.resolve())].append(domain)
        if not registry_path.is_file():
            continue

        for line_number, raw in enumerate(text(registry_path).splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                findings.append(
                    Finding(
                        "EVIDENCE_REGISTRY_ENTRY_INVALID",
                        relative,
                        f"line={line_number};error={exc.msg}",
                    )
                )
                continue

            if not isinstance(record, dict):
                findings.append(
                    Finding(
                        "EVIDENCE_REGISTRY_ENTRY_INVALID",
                        relative,
                        f"line={line_number};type={type(record).__name__}",
                    )
                )
                continue

            actual_domain = record.get("DOMAIN", record.get("domain"))
            if actual_domain != domain:
                findings.append(
                    Finding(
                        "CROSS_DOMAIN_EVIDENCE_ENTRY",
                        relative,
                        (
                            f"line={line_number};expected={domain};"
                            f"actual={actual_domain}"
                        ),
                    )
                )

            digest = record.get(
                "ARTIFACT_SHA256",
                record.get("artifact_sha256"),
            )
            if digest is None:
                continue
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                findings.append(
                    Finding(
                        "EVIDENCE_REGISTRY_SHA256_INVALID",
                        relative,
                        f"line={line_number}",
                    )
                )
                continue
            sha_domains[digest.lower()].add(domain)

    for relative, domains in configured.items():
        if len(domains) > 1:
            findings.append(
                Finding(
                    "SHARED_EVIDENCE_REGISTRY",
                    relative,
                    f"domains={','.join(sorted(domains))}",
                )
            )

    for relative, domains in resolved.items():
        if len(domains) > 1:
            findings.append(
                Finding(
                    "SHARED_EVIDENCE_REGISTRY",
                    relative,
                    f"resolved_domains={','.join(sorted(domains))}",
                )
            )

    for digest, domains in sha_domains.items():
        if len(domains) > 1:
            findings.append(
                Finding(
                    "CROSS_DOMAIN_SHA_BINDING",
                    "evidence_registry.jsonl",
                    f"sha256={digest};domains={','.join(sorted(domains))}",
                )
            )

    return findings


def path_declares_boatrace(relative: str) -> bool:
    scrubbed = NON_BOATRACE_PATH_TOKEN_RE.sub(r"\1non_domain", relative)
    return BOATRACE_PATH_TOKEN_RE.search(scrubbed) is not None


def body_declares_boatrace(body: str) -> bool:
    return any(pattern.search(body) for pattern in BOATRACE_MARKERS)


def validate_references(root: Path, contract: dict):
    findings: list[Finding] = []
    scanned = 0
    non_boatrace_path_exclusions = 0

    boatrace = contract["domains"]["BOATRACE"]
    wanstage = contract["domains"]["WANSTAGE_CONTROL"]
    allowed = tuple(norm(value) for value in boatrace["allowed_path_prefixes"])
    denied = tuple(norm(value) for value in boatrace["denied_path_prefixes"])
    foreign_manifest = norm(wanstage["manifest"])
    foreign_registry = norm(wanstage["evidence_registry"])

    for path in files(root):
        relative = norm(str(path.relative_to(root)))
        if relative == norm(str(CONTRACT_REL)):
            continue

        body = text(path)
        scanned += 1

        if under(relative, "governance/domains/control_separation/"):
            continue

        path_classified = path_declares_boatrace(relative)
        body_classified = body_declares_boatrace(body)
        in_scope = any(under(relative, prefix) for prefix in allowed)

        if (
            NON_BOATRACE_PATH_TOKEN_RE.search(relative)
            and not path_classified
            and not body_classified
        ):
            non_boatrace_path_exclusions += 1

        classified = path_classified or body_classified
        if classified and not in_scope:
            source = (
                "path_and_content"
                if path_classified and body_classified
                else "path_token"
                if path_classified
                else "content_marker"
            )
            findings.append(
                Finding(
                    "BOATRACE_ARTIFACT_OUTSIDE_DOMAIN_ROOT",
                    relative,
                    (
                        f"classification={source};"
                        "not_under_allowed_boatrace_prefix"
                    ),
                )
            )

        if not classified and not in_scope:
            continue

        for prefix in denied:
            if prefix in body:
                findings.append(
                    Finding("CROSS_DOMAIN_PATH_REFERENCE", relative, prefix)
                )

        if foreign_manifest in body:
            findings.append(
                Finding(
                    "FOREIGN_MANIFEST_REFERENCE",
                    relative,
                    foreign_manifest,
                )
            )

        if foreign_registry in body:
            findings.append(
                Finding(
                    "SHARED_EVIDENCE_REGISTRY",
                    relative,
                    foreign_registry,
                )
            )

        if (
            path.suffix.lower() in ENTRYPOINT_SUFFIXES
            and any(pattern.search(body) for pattern in ROOT_SCAN_PATTERNS)
        ):
            findings.append(
                Finding(
                    "UNSCOPED_RECURSIVE_SCAN",
                    relative,
                    "workspace-root recursive scan pattern",
                )
            )

    return findings, scanned, non_boatrace_path_exclusions


def counters(findings: list[Finding]) -> dict[str, int]:
    count = Counter(finding.code for finding in findings)
    return {
        "cross_domain_path_reference_count": (
            count["CROSS_DOMAIN_PATH_REFERENCE"]
            + count["FOREIGN_MANIFEST_REFERENCE"]
        ),
        "cross_domain_manifest_entry_count": count[
            "CROSS_DOMAIN_MANIFEST_ENTRY"
        ],
        "cross_domain_sha_binding_count": count["CROSS_DOMAIN_SHA_BINDING"],
        "workspace_root_recursive_scan_count": count[
            "UNSCOPED_RECURSIVE_SCAN"
        ],
        "shared_execution_entrypoint_count": count[
            "SHARED_EXECUTION_ENTRYPOINT"
        ],
        "shared_evidence_registry_count": count[
            "SHARED_EVIDENCE_REGISTRY"
        ],
        "outside_domain_artifact_count": count[
            "BOATRACE_ARTIFACT_OUTSIDE_DOMAIN_ROOT"
        ],
        "required_control_root_missing_count": count[
            "REQUIRED_CONTROL_ROOT_MISSING"
        ],
        "required_manifest_missing_count": count[
            "REQUIRED_MANIFEST_MISSING"
        ],
        "required_evidence_registry_missing_count": count[
            "REQUIRED_EVIDENCE_REGISTRY_MISSING"
        ],
        "cross_domain_evidence_entry_count": count[
            "CROSS_DOMAIN_EVIDENCE_ENTRY"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=os.environ.get("WANSTAGE_ROOT", "."),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--max-findings",
        type=int,
        default=DEFAULT_MAX_FINDINGS,
    )
    args = parser.parse_args()

    if args.max_findings < 0:
        parser.error("--max-findings must be zero or greater")

    root = Path(args.root).expanduser().resolve()
    contract_path = root / CONTRACT_REL

    if not contract_path.is_file():
        print(
            "EXECUTION_STATUS=FAILED\n"
            "INVESTIGATION_STATUS=RESOLVED\n"
            "DATA_STATUS=MISSING"
        )
        print(
            f"MISSING_CONTRACT={contract_path}\n"
            "BOATRACE_WANSTAGE_CONTROL_SEPARATION_COMPLETE=False\n"
            "DECISION=NO-GO"
        )
        return 2

    try:
        contract = json.loads(text(contract_path))
    except json.JSONDecodeError as exc:
        print(
            "EXECUTION_STATUS=FAILED\n"
            "INVESTIGATION_STATUS=RESOLVED\n"
            "DATA_STATUS=INVALID"
        )
        print(
            f"CONTRACT_JSON_ERROR={exc}\n"
            "BOATRACE_WANSTAGE_CONTROL_SEPARATION_COMPLETE=False\n"
            "DECISION=NO-GO"
        )
        return 2

    findings = validate_contract(contract)

    asset_findings, roots_checked, manifests_checked, registries_checked = (
        required_assets(root, contract)
    )
    findings += asset_findings
    findings += validate_manifests(root, contract)
    findings += validate_registries(root, contract)

    reference_findings, scanned, non_boatrace_path_exclusions = (
        validate_references(root, contract)
    )
    findings += reference_findings

    findings = sorted(
        set(findings),
        key=lambda finding: (finding.code, finding.path, finding.detail),
    )

    required = len(contract["domains"])
    counts = counters(findings)
    assets_complete = (
        roots_checked == required
        and manifests_checked == required
        and registries_checked == required
    )
    complete = not findings and assets_complete
    decision = "GO" if complete else "NO-GO"

    missing = (
        counts["required_control_root_missing_count"]
        + counts["required_manifest_missing_count"]
        + counts["required_evidence_registry_missing_count"]
    )
    data_status = (
        "MISSING"
        if missing
        else "VERIFIED"
        if complete
        else "INVALID"
    )

    finding_code_counts = dict(
        sorted(Counter(finding.code for finding in findings).items())
    )
    returned_findings = findings[: args.max_findings]
    truncated = len(returned_findings) < len(findings)

    result = {
        "validator_mode": "READ_ONLY_STATIC_FAIL_CLOSED",
        "workspace_root": str(root),
        "contract_path": str(CONTRACT_REL),
        "contract_sha256": sha256(contract_path),
        "execution_status": "COMPLETE",
        "investigation_status": "RESOLVED",
        "data_status": data_status,
        "text_files_scanned": scanned,
        "non_boatrace_path_exclusion_count": non_boatrace_path_exclusions,
        "domains_required": required,
        "control_roots_checked": roots_checked,
        "manifests_required": required,
        "manifests_checked": manifests_checked,
        "evidence_registries_required": required,
        "evidence_registries_checked": registries_checked,
        **counts,
        "finding_count": len(findings),
        "finding_code_counts": finding_code_counts,
        "findings_returned": len(returned_findings),
        "findings_truncated": truncated,
        "findings": [asdict(finding) for finding in returned_findings],
        "boatrace_wanstage_control_separation_complete": complete,
        "decision": decision,
    }

    if args.json:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for key, value in result.items():
            if key not in {"findings", "finding_code_counts"}:
                print(f"{key.upper()}={value}")
        print(
            "FINDING_CODE_COUNTS="
            + json.dumps(finding_code_counts, sort_keys=True)
        )
        for finding in returned_findings:
            print(
                f"FINDING={finding.code}|{finding.path}|{finding.detail}"
            )
        print(f"DECISION={decision}")

    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
