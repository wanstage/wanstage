# BOATRACE / WANSTAGE Control Separation

This directory defines the fail-closed separation boundary between BOATRACE control assets and WANSTAGE common control assets.

## Separation layers

1. Path namespace
2. Manifest namespace
3. SHA namespace
4. Execution authority
5. Evidence registry

## Canonical assets

- `boatrace_wanstage_control_separation.contract.json`
- `validate_boatrace_wanstage_control_separation.py`

## Read-only validation

```bash
python3 governance/domains/control_separation/validate_boatrace_wanstage_control_separation.py \
  --root /Users/okayoshiyuki/WANSTAGE_NEW
```

JSON output:

```bash
python3 governance/domains/control_separation/validate_boatrace_wanstage_control_separation.py \
  --root /Users/okayoshiyuki/WANSTAGE_NEW \
  --json
```

The validator does not modify files. It checks:

- contract fail-closed rules
- required domain control roots, Manifests, and evidence registries
- BOATRACE-classified or `boatrace`-named artifacts outside BOATRACE allowed prefixes
- cross-domain Manifest entries and path escape
- cross-domain SHA binding and shared execution entrypoints
- evidence registry JSONL domain binding and shared registry paths
- BOATRACE references to WANSTAGE control paths
- foreign Manifest and evidence registry references
- workspace-wide recursive scan patterns in BOATRACE artifacts

## Explicit counters

```text
CROSS_DOMAIN_PATH_REFERENCE_COUNT
CROSS_DOMAIN_MANIFEST_ENTRY_COUNT
CROSS_DOMAIN_SHA_BINDING_COUNT
WORKSPACE_ROOT_RECURSIVE_SCAN_COUNT
SHARED_EXECUTION_ENTRYPOINT_COUNT
SHARED_EVIDENCE_REGISTRY_COUNT
OUTSIDE_DOMAIN_ARTIFACT_COUNT
REQUIRED_CONTROL_ROOT_MISSING_COUNT
REQUIRED_MANIFEST_MISSING_COUNT
REQUIRED_EVIDENCE_REGISTRY_MISSING_COUNT
CROSS_DOMAIN_EVIDENCE_ENTRY_COUNT
```

## Static acceptance gate

`DECISION=GO` and `BOATRACE_WANSTAGE_CONTROL_SEPARATION_COMPLETE=True` are emitted only when all of the following are true:

- both domain control roots exist
- both domain Manifests exist and are checked
- both domain evidence registries exist and are checked
- every explicit counter is zero
- `FINDING_COUNT=0`

Missing required assets, shared-namespace BOATRACE artifacts, invalid registry entries, or any cross-domain finding produce `DECISION=NO-GO` and a non-zero exit status.

A clean static result is necessary but does not independently prove runtime environment binding or end-to-end process isolation. Those remain separate execution-stage validations.
