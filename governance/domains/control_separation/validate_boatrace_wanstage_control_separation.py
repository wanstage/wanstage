#!/usr/bin/env python3
"""Fail-closed read-only BOATRACE/WANSTAGE separation validator."""
from __future__ import annotations
import argparse, hashlib, json, os, re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

CONTRACT_REL = Path("governance/domains/control_separation/boatrace_wanstage_control_separation.contract.json")
TEXT_SUFFIXES = {".py",".sh",".zsh",".bash",".json",".jsonl",".yaml",".yml",".toml",".ini",".cfg",".md",".txt",".csv",".ps1"}
SKIP_PARTS = {".git","__pycache__",".venv","venv","node_modules"}
ENTRYPOINT_SUFFIXES = {".py",".sh",".zsh",".bash",".ps1"}
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ROOT_SCAN_PATTERNS = (
    re.compile(r"find\s+[^\n]*(?:WANSTAGE_NEW|workspace_root|ROOT)[^\n]*-type\s+f", re.I),
    re.compile(r"rglob\s*\(\s*['\"]\*", re.I),
    re.compile(r"glob\s*\(\s*['\"]\*\*/\*", re.I),
)
BOATRACE_MARKERS = (
    re.compile(r"(?im)^\s*(?:DOMAIN|WANSTAGE_DOMAIN)\s*[:=]\s*['\"]?BOATRACE\b"),
    re.compile(r'(?i)"domain"\s*:\s*"BOATRACE"'),
    re.compile(r"(?im)^\s*BOATRACE_DOMAIN_CLASSIFICATION\s*=\s*True\b"),
)

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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_SUFFIXES or p.name == "MANIFEST.sha256":
            yield p


def validate_contract(contract: dict) -> list[Finding]:
    out = []
    required_layers = {"PATH_NAMESPACE","MANIFEST_NAMESPACE","SHA_NAMESPACE","EXECUTION_AUTHORITY","EVIDENCE_REGISTRY"}
    if set(contract.get("separation_layers", [])) != required_layers:
        out.append(Finding("CONTRACT_LAYER_MISMATCH", str(CONTRACT_REL), "invalid separation_layers"))
    if set(contract.get("domains", {})) != {"BOATRACE","WANSTAGE_CONTROL"}:
        out.append(Finding("CONTRACT_DOMAIN_MISMATCH", str(CONTRACT_REL), "domains must be BOATRACE and WANSTAGE_CONTROL"))
    fail_closed = (
        "boatrace_recursive_scan_from_workspace_root","boatrace_glob_all_json",
        "boatrace_glob_all_sha256","boatrace_glob_all_reports",
        "boatrace_artifact_outside_domain_root_allowed","required_domain_asset_missing_allowed",
        "manifest_cross_domain_entry_allowed","manifest_parent_directory_escape_allowed",
        "manifest_absolute_foreign_path_allowed","cross_domain_sha_reuse_allowed",
        "cross_domain_evidence_entry_allowed","sha_lookup_by_hash_only",
        "sha_copied_from_chat_allowed","sha_copied_from_other_manifest_allowed",
        "implicit_domain_inference_allowed","shared_execution_entrypoint_allowed",
        "shared_evidence_registry_allowed",
    )
    for key in fail_closed:
        if contract.get("rules", {}).get(key) is not False:
            out.append(Finding("CONTRACT_RULE_NOT_FAIL_CLOSED", str(CONTRACT_REL), key))
    return out


def required_assets(root: Path, contract: dict):
    out, roots, manifests, registries = [], 0, 0, 0
    for domain, cfg in contract["domains"].items():
        cr, mf, rg = norm(cfg["control_root"]), norm(cfg["manifest"]), norm(cfg["evidence_registry"])
        if (root / cr).is_dir(): roots += 1
        else: out.append(Finding("REQUIRED_CONTROL_ROOT_MISSING", cr, domain))
        if (root / mf).is_file(): manifests += 1
        else: out.append(Finding("REQUIRED_MANIFEST_MISSING", mf, domain))
        if (root / rg).is_file(): registries += 1
        else: out.append(Finding("REQUIRED_EVIDENCE_REGISTRY_MISSING", rg, domain))
    return out, roots, manifests, registries


def manifests(root: Path, contract: dict):
    out, rows = [], []
    for domain, cfg in contract["domains"].items():
        rel = norm(cfg["manifest"]); p = root / rel
        if not p.is_file(): continue
        allowed = norm(cfg["control_root"]).rstrip("/") + "/"
        for n, raw in enumerate(text(p).splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"): continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                out.append(Finding("MANIFEST_ENTRY_INVALID", rel, f"line={n}")); continue
            digest, raw_path = parts
            if not SHA_RE.fullmatch(digest):
                out.append(Finding("MANIFEST_SHA256_INVALID", rel, f"line={n}")); continue
            raw_norm = raw_path.replace("\\", "/")
            if raw_norm.startswith("/") or "../" in raw_norm:
                out.append(Finding("MANIFEST_PATH_ESCAPE", rel, f"line={n};path={raw_path}")); continue
            artifact = norm(raw_path); rows.append((domain, digest.lower(), artifact))
            if not artifact.startswith(allowed):
                out.append(Finding("CROSS_DOMAIN_MANIFEST_ENTRY", rel, f"{domain}:{artifact}"))
    sha_domains, path_domains = defaultdict(set), defaultdict(set)
    for domain, digest, artifact in rows:
        sha_domains[digest].add(domain); path_domains[artifact].add(domain)
    for digest, domains in sha_domains.items():
        if len(domains) > 1:
            out.append(Finding("CROSS_DOMAIN_SHA_BINDING", "MANIFEST.sha256", f"sha256={digest};domains={','.join(sorted(domains))}"))
    for artifact, domains in path_domains.items():
        if len(domains) > 1 and Path(artifact).suffix.lower() in ENTRYPOINT_SUFFIXES:
            out.append(Finding("SHARED_EXECUTION_ENTRYPOINT", artifact, f"domains={','.join(sorted(domains))}"))
    return out


def registries(root: Path, contract: dict):
    out, sha_domains = [], defaultdict(set)
    configured, resolved = defaultdict(list), defaultdict(list)
    for domain, cfg in contract["domains"].items():
        rel = norm(cfg["evidence_registry"]); p = root / rel
        configured[rel].append(domain)
        if p.exists(): resolved[str(p.resolve())].append(domain)
        if not p.is_file(): continue
        for n, raw in enumerate(text(p).splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"): continue
            try: rec = json.loads(line)
            except json.JSONDecodeError as exc:
                out.append(Finding("EVIDENCE_REGISTRY_ENTRY_INVALID", rel, f"line={n};error={exc.msg}")); continue
            if not isinstance(rec, dict):
                out.append(Finding("EVIDENCE_REGISTRY_ENTRY_INVALID", rel, f"line={n};type={type(rec).__name__}")); continue
            actual = rec.get("DOMAIN", rec.get("domain"))
            if actual != domain:
                out.append(Finding("CROSS_DOMAIN_EVIDENCE_ENTRY", rel, f"line={n};expected={domain};actual={actual}"))
            digest = rec.get("ARTIFACT_SHA256", rec.get("artifact_sha256"))
            if digest is None: continue
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                out.append(Finding("EVIDENCE_REGISTRY_SHA256_INVALID", rel, f"line={n}")); continue
            sha_domains[digest.lower()].add(domain)
    for rel, domains in configured.items():
        if len(domains) > 1: out.append(Finding("SHARED_EVIDENCE_REGISTRY", rel, f"domains={','.join(sorted(domains))}"))
    for rel, domains in resolved.items():
        if len(domains) > 1: out.append(Finding("SHARED_EVIDENCE_REGISTRY", rel, f"resolved_domains={','.join(sorted(domains))}"))
    for digest, domains in sha_domains.items():
        if len(domains) > 1: out.append(Finding("CROSS_DOMAIN_SHA_BINDING", "evidence_registry.jsonl", f"sha256={digest};domains={','.join(sorted(domains))}"))
    return out


def is_boatrace(rel: str, body: str) -> bool:
    return "boatrace" in rel.casefold() or any(p.search(body) for p in BOATRACE_MARKERS)


def references(root: Path, contract: dict):
    out, scanned = [], 0
    boatrace = contract["domains"]["BOATRACE"]; wanstage = contract["domains"]["WANSTAGE_CONTROL"]
    allowed = tuple(norm(x) for x in boatrace["allowed_path_prefixes"])
    denied = tuple(norm(x) for x in boatrace["denied_path_prefixes"])
    foreign_manifest, foreign_registry = norm(wanstage["manifest"]), norm(wanstage["evidence_registry"])
    for p in files(root):
        rel = norm(str(p.relative_to(root)))
        if rel == norm(str(CONTRACT_REL)): continue
        body = text(p); scanned += 1
        if under(rel, "governance/domains/control_separation/"): continue
        classified, in_scope = is_boatrace(rel, body), any(under(rel, x) for x in allowed)
        if classified and not in_scope:
            out.append(Finding("BOATRACE_ARTIFACT_OUTSIDE_DOMAIN_ROOT", rel, "not_under_allowed_boatrace_prefix"))
        if not classified and not in_scope: continue
        for prefix in denied:
            if prefix in body: out.append(Finding("CROSS_DOMAIN_PATH_REFERENCE", rel, prefix))
        if foreign_manifest in body: out.append(Finding("FOREIGN_MANIFEST_REFERENCE", rel, foreign_manifest))
        if foreign_registry in body: out.append(Finding("SHARED_EVIDENCE_REGISTRY", rel, foreign_registry))
        if any(pattern.search(body) for pattern in ROOT_SCAN_PATTERNS):
            out.append(Finding("UNSCOPED_RECURSIVE_SCAN", rel, "workspace-root recursive scan pattern"))
    return out, scanned


def counters(findings: list[Finding]) -> dict[str, int]:
    c = Counter(x.code for x in findings)
    return {
        "cross_domain_path_reference_count": c["CROSS_DOMAIN_PATH_REFERENCE"] + c["FOREIGN_MANIFEST_REFERENCE"],
        "cross_domain_manifest_entry_count": c["CROSS_DOMAIN_MANIFEST_ENTRY"],
        "cross_domain_sha_binding_count": c["CROSS_DOMAIN_SHA_BINDING"],
        "workspace_root_recursive_scan_count": c["UNSCOPED_RECURSIVE_SCAN"],
        "shared_execution_entrypoint_count": c["SHARED_EXECUTION_ENTRYPOINT"],
        "shared_evidence_registry_count": c["SHARED_EVIDENCE_REGISTRY"],
        "outside_domain_artifact_count": c["BOATRACE_ARTIFACT_OUTSIDE_DOMAIN_ROOT"],
        "required_control_root_missing_count": c["REQUIRED_CONTROL_ROOT_MISSING"],
        "required_manifest_missing_count": c["REQUIRED_MANIFEST_MISSING"],
        "required_evidence_registry_missing_count": c["REQUIRED_EVIDENCE_REGISTRY_MISSING"],
        "cross_domain_evidence_entry_count": c["CROSS_DOMAIN_EVIDENCE_ENTRY"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default=os.environ.get("WANSTAGE_ROOT", ".")); ap.add_argument("--json", action="store_true")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); contract_path = root / CONTRACT_REL
    if not contract_path.is_file():
        print("EXECUTION_STATUS=FAILED\nINVESTIGATION_STATUS=RESOLVED\nDATA_STATUS=MISSING")
        print(f"MISSING_CONTRACT={contract_path}\nBOATRACE_WANSTAGE_CONTROL_SEPARATION_COMPLETE=False\nDECISION=NO-GO"); return 2
    try: contract = json.loads(text(contract_path))
    except json.JSONDecodeError as exc:
        print("EXECUTION_STATUS=FAILED\nINVESTIGATION_STATUS=RESOLVED\nDATA_STATUS=INVALID")
        print(f"CONTRACT_JSON_ERROR={exc}\nBOATRACE_WANSTAGE_CONTROL_SEPARATION_COMPLETE=False\nDECISION=NO-GO"); return 2
    findings = validate_contract(contract)
    asset_findings, roots_checked, manifests_checked, registries_checked = required_assets(root, contract); findings += asset_findings
    findings += manifests(root, contract); findings += registries(root, contract)
    ref_findings, scanned = references(root, contract); findings += ref_findings
    findings = sorted(set(findings), key=lambda x: (x.code, x.path, x.detail))
    required = len(contract["domains"]); counts = counters(findings)
    assets_complete = roots_checked == required and manifests_checked == required and registries_checked == required
    complete = not findings and assets_complete; decision = "GO" if complete else "NO-GO"
    missing = counts["required_control_root_missing_count"] + counts["required_manifest_missing_count"] + counts["required_evidence_registry_missing_count"]
    data_status = "MISSING" if missing else ("VERIFIED" if complete else "INVALID")
    result = {
        "validator_mode":"READ_ONLY_STATIC_FAIL_CLOSED","workspace_root":str(root),"contract_path":str(CONTRACT_REL),"contract_sha256":sha256(contract_path),
        "text_files_scanned":scanned,"domains_required":required,"control_roots_checked":roots_checked,"manifests_required":required,"manifests_checked":manifests_checked,
        "evidence_registries_required":required,"evidence_registries_checked":registries_checked,**counts,"finding_count":len(findings),
        "findings":[asdict(x) for x in findings],"boatrace_wanstage_control_separation_complete":complete,"decision":decision,
    }
    if args.json: print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("EXECUTION_STATUS=COMPLETE\nINVESTIGATION_STATUS=RESOLVED"); print(f"DATA_STATUS={data_status}")
        for k,v in result.items():
            if k != "findings": print(f"{k.upper()}={v}")
        for x in findings: print(f"FINDING={x.code}|{x.path}|{x.detail}")
        print(f"DECISION={decision}")
    return 0 if complete else 1

if __name__ == "__main__":
    raise SystemExit(main())
