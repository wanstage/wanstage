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
- cross-domain Manifest entries
- path escape in Manifest entries
- BOATRACE references to WANSTAGE control paths
- foreign Manifest and evidence registry references
- workspace-wide recursive scan patterns in BOATRACE scope

## Acceptance conditions

```text
CROSS_DOMAIN_PATH_REFERENCE_COUNT=0
CROSS_DOMAIN_MANIFEST_ENTRY_COUNT=0
CROSS_DOMAIN_SHA_BINDING_COUNT=0
WORKSPACE_ROOT_RECURSIVE_SCAN_COUNT=0
SHARED_EXECUTION_ENTRYPOINT_COUNT=0
SHARED_EVIDENCE_REGISTRY_COUNT=0
```

A zero-finding static result is necessary but does not prove runtime isolation. Runtime execution, environment binding, and actual domain Manifests remain separate validation stages.
