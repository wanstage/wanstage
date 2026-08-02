#!/usr/bin/env python3
"""Fail-closed receiver-aware BOATRACE/WANSTAGE separation validator."""
from __future__ import annotations

import ast
import importlib.util
import os
import re
import shlex
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

LEGACY_PATH = Path(__file__).with_name(
    "validate_boatrace_wanstage_control_separation_legacy.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "_wanstage_control_separation_legacy",
    LEGACY_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load legacy validator: {LEGACY_PATH}")
_legacy = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _legacy
_SPEC.loader.exec_module(_legacy)

for _name in dir(_legacy):
    if not _name.startswith("__"):
        globals().setdefault(_name, getattr(_legacy, _name))

_ORIGINAL_VALIDATE_REFERENCES = _legacy.validate_references
_ORIGINAL_COUNTERS = _legacy.counters

WORKSPACE_ROOT_DIRECT = "WORKSPACE_ROOT_DIRECT"
DOMAIN_SCOPED = "DOMAIN_SCOPED"
LEGACY_ROOT = "LEGACY_ROOT"
UNRESOLVED = "UNRESOLVED"
LEGACY_ROOTS = (Path("/Users/okayoshiyuki/WANSTAGE"),)
PYTHON_FALLBACK_RE = re.compile(
    r"(?P<receiver>[A-Za-z_][A-Za-z0-9_.\[\]()/-]*)\."
    r"(?P<method>rglob|glob)\s*\(\s*['\"](?P<pattern>\*[^'\"]*)['\"]"
)
SHELL_ASSIGNMENT_RE = re.compile(
    r"^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*)$"
)
SHELL_VAR_RE = re.compile(
    r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|"
    r"(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)


@dataclass(frozen=True)
class RecursiveScan:
    path: str
    line: int
    language: str
    receiver: str
    pattern: str
    classification: str
    resolved_paths: tuple[str, ...] = ()


_LAST_RECURSIVE_SCANS: list[RecursiveScan] = []


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _classify(paths: set[Path] | None, workspace_root: Path) -> str:
    if not paths:
        return UNRESOLVED
    workspace_root = workspace_root.resolve(strict=False)
    classes: set[str] = set()
    for raw in paths:
        path = raw.expanduser().resolve(strict=False)
        if path == workspace_root:
            classes.add(WORKSPACE_ROOT_DIRECT)
        elif _is_within(path, workspace_root):
            classes.add(DOMAIN_SCOPED)
        elif any(
            path == legacy or _is_within(path, legacy)
            for legacy in LEGACY_ROOTS
        ):
            classes.add(LEGACY_ROOT)
        else:
            classes.add(UNRESOLVED)
    return next(iter(classes)) if len(classes) == 1 else UNRESOLVED


def _literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                return None
        return "".join(parts)
    return None


def _call_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _eval_paths(
    node: ast.AST,
    env: dict[str, set[Path] | None],
    source_path: Path,
    workspace_root: Path,
) -> set[Path] | None:
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return {source_path}
        if node.id in {"WANSTAGE_ROOT", "WORKSPACE_ROOT"} and node.id not in env:
            return {workspace_root}
        return env.get(node.id)

    literal = _literal(node)
    if literal is not None:
        path = Path(os.path.expanduser(literal))
        return {path} if path.is_absolute() else None

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        result: set[Path] = set()
        for element in node.elts:
            paths = _eval_paths(element, env, source_path, workspace_root)
            if not paths:
                return None
            result.update(paths)
        return result

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _eval_paths(node.left, env, source_path, workspace_root)
        right = _literal(node.right)
        if not left or right is None:
            return None
        return {path / right for path in left}

    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
            base = _eval_paths(
                node.value.value, env, source_path, workspace_root
            )
            index = (
                node.slice.value
                if isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, int)
                else None
            )
            if not base or index is None or index < 0:
                return None
            result: set[Path] = set()
            for path in base:
                try:
                    result.add(path.parents[index])
                except IndexError:
                    return None
            return result
        return None

    if isinstance(node, ast.Attribute):
        base = _eval_paths(node.value, env, source_path, workspace_root)
        if not base:
            return None
        if node.attr == "parent":
            return {path.parent for path in base}
        return None

    if isinstance(node, ast.Call):
        call_name = _call_name(node.func)
        if call_name in {"Path", "pathlib.Path"}:
            return (
                _eval_paths(node.args[0], env, source_path, workspace_root)
                if node.args
                else None
            )
        if call_name in {"Path.home", "pathlib.Path.home"}:
            return {Path.home()}
        if call_name in {"os.environ.get", "os.getenv"} and node.args:
            key = _literal(node.args[0])
            if key == "WANSTAGE_ROOT":
                return {workspace_root}
            return (
                _eval_paths(node.args[1], env, source_path, workspace_root)
                if len(node.args) > 1
                else None
            )
        if call_name == "os.path.join" and node.args:
            result = _eval_paths(
                node.args[0], env, source_path, workspace_root
            )
            if not result:
                return None
            for argument in node.args[1:]:
                part = _literal(argument)
                if part is None:
                    return None
                result = {path / part for path in result}
            return result
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            base = _eval_paths(
                node.func.value, env, source_path, workspace_root
            )
            if method in {"resolve", "absolute", "expanduser"}:
                if not base:
                    return None
                if method == "expanduser":
                    return {path.expanduser() for path in base}
                return {path.resolve(strict=False) for path in base}
            if method == "joinpath":
                if not base:
                    return None
                result = set(base)
                for argument in node.args:
                    part = _literal(argument)
                    if part is None:
                        return None
                    result = {path / part for path in result}
                return result
    return None


def _target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            names.extend(_target_names(element))
        return names
    return []


def _recursive_call(call: ast.Call) -> tuple[str, str] | None:
    if not isinstance(call.func, ast.Attribute) or not call.args:
        return None
    method = call.func.attr
    pattern = _literal(call.args[0])
    if pattern is None:
        return None
    if method == "rglob" and pattern.startswith("*"):
        return method, pattern
    if method == "glob" and pattern.startswith("**/"):
        return method, pattern
    return None


class _PythonAnalyzer:
    def __init__(self, path: Path, relative: str, root: Path):
        self.path = path
        self.relative = relative
        self.root = root
        self.scans: list[RecursiveScan] = []

    def analyze(self, body: str) -> list[RecursiveScan]:
        try:
            tree = ast.parse(body, filename=str(self.path))
        except SyntaxError:
            return self._fallback(body)
        self._block(tree.body, {})
        return self.scans

    def _fallback(self, body: str) -> list[RecursiveScan]:
        scans: list[RecursiveScan] = []
        for line_number, line in enumerate(body.splitlines(), 1):
            for match in PYTHON_FALLBACK_RE.finditer(line):
                scans.append(
                    RecursiveScan(
                        self.relative,
                        line_number,
                        "PYTHON_FALLBACK",
                        match.group("receiver"),
                        match.group("pattern"),
                        UNRESOLVED,
                    )
                )
        return scans

    def _block(
        self,
        statements: list[ast.stmt],
        inherited: dict[str, set[Path] | None],
    ) -> None:
        env = dict(inherited)
        for statement in statements:
            if isinstance(statement, ast.Assign):
                value = _eval_paths(statement.value, env, self.path, self.root)
                for target in statement.targets:
                    for name in _target_names(target):
                        env[name] = value
            elif isinstance(statement, ast.AnnAssign):
                value = (
                    _eval_paths(statement.value, env, self.path, self.root)
                    if statement.value is not None
                    else None
                )
                for name in _target_names(statement.target):
                    env[name] = value
            elif isinstance(statement, (ast.For, ast.AsyncFor)):
                iterable = _eval_paths(statement.iter, env, self.path, self.root)
                loop_env = dict(env)
                for name in _target_names(statement.target):
                    loop_env[name] = iterable
                self._inspect(statement.iter, env)
                self._block(statement.body, loop_env)
                self._block(statement.orelse, env)
                continue
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._block(statement.body, env)
                continue
            elif isinstance(statement, ast.If):
                self._inspect(statement.test, env)
                self._block(statement.body, env)
                self._block(statement.orelse, env)
                continue
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    self._inspect(item.context_expr, env)
                self._block(statement.body, env)
                continue
            elif isinstance(statement, ast.Try):
                self._block(statement.body, env)
                for handler in statement.handlers:
                    self._block(handler.body, env)
                self._block(statement.orelse, env)
                self._block(statement.finalbody, env)
                continue
            self._inspect(statement, env)

    def _inspect(
        self, node: ast.AST, env: dict[str, set[Path] | None]
    ) -> None:
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            candidate = _recursive_call(child)
            if candidate is None:
                continue
            method, pattern = candidate
            receiver_node = child.func.value
            paths = _eval_paths(receiver_node, env, self.path, self.root)
            self.scans.append(
                RecursiveScan(
                    self.relative,
                    getattr(child, "lineno", 0),
                    "PYTHON",
                    ast.unparse(receiver_node),
                    f"{method}:{pattern}",
                    _classify(paths, self.root),
                    tuple(sorted(str(path) for path in paths or set())),
                )
            )


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        return value[1:-1]
    return value


def _shell_paths(
    value: str,
    env: dict[str, set[Path] | None],
    root: Path,
) -> set[Path] | None:
    value = _strip_quotes(value.strip())
    if value in {"$WANSTAGE_ROOT", "${WANSTAGE_ROOT}"}:
        return {root}
    matches = list(SHELL_VAR_RE.finditer(value))
    if not matches:
        path = Path(os.path.expanduser(value))
        return {path} if path.is_absolute() else None
    current_values = {value}
    for match in matches:
        name = match.group("braced") or match.group("plain")
        replacements = env.get(name)
        if replacements is None and name == "WANSTAGE_ROOT":
            replacements = {root}
        if not replacements:
            return None
        token = match.group(0)
        current_values = {
            current.replace(token, str(replacement))
            for current in current_values
            for replacement in replacements
        }
    result: set[Path] = set()
    for current in current_values:
        path = Path(os.path.expanduser(_strip_quotes(current)))
        if not path.is_absolute():
            return None
        result.add(path)
    return result


def _shell_scans(body: str, relative: str, root: Path) -> list[RecursiveScan]:
    env: dict[str, set[Path] | None] = {"WANSTAGE_ROOT": {root}}
    scans: list[RecursiveScan] = []
    for line_number, raw in enumerate(body.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assignment = SHELL_ASSIGNMENT_RE.match(raw)
        if assignment:
            env[assignment.group("name")] = _shell_paths(
                assignment.group("value"), env, root
            )
            continue
        try:
            tokens = shlex.split(raw, comments=True, posix=True)
        except ValueError:
            tokens = []
        if not tokens:
            continue
        try:
            index = tokens.index("find")
        except ValueError:
            continue
        if index + 1 >= len(tokens) or "-type" not in tokens:
            continue
        receiver = tokens[index + 1]
        paths = _shell_paths(receiver, env, root)
        scans.append(
            RecursiveScan(
                relative,
                line_number,
                "SHELL",
                receiver,
                "find:-type",
                _classify(paths, root),
                tuple(sorted(str(path) for path in paths or set())),
            )
        )
    return scans


def _recursive_scans(
    path: Path, relative: str, body: str, root: Path
) -> list[RecursiveScan]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        if ".rglob(" not in body and ".glob(" not in body:
            return []
        return _PythonAnalyzer(path, relative, root).analyze(body)
    if suffix in {".sh", ".zsh", ".bash"}:
        if not re.search(
            r"(?m)^\s*(?:sudo\s+|command\s+)?find\s+", body
        ):
            return []
        return _shell_scans(body, relative, root)
    return []


def _eligible_recursive_files(root: Path, contract: dict):
    boatrace = contract["domains"]["BOATRACE"]
    allowed = tuple(_legacy.norm(value) for value in boatrace["allowed_path_prefixes"])
    for path in _legacy.files(root):
        relative = _legacy.norm(str(path.relative_to(root)))
        if relative == _legacy.norm(str(_legacy.CONTRACT_REL)):
            continue
        if _legacy.under(relative, "governance/domains/control_separation/"):
            continue
        if path.suffix.lower() not in _legacy.ENTRYPOINT_SUFFIXES:
            continue
        body = _legacy.text(path)
        classified = (
            _legacy.path_declares_boatrace(relative)
            or _legacy.body_declares_boatrace(body)
        )
        in_scope = any(_legacy.under(relative, prefix) for prefix in allowed)
        if classified or in_scope:
            yield path, relative, body


def validate_references(root: Path, contract: dict):
    global _LAST_RECURSIVE_SCANS
    findings, scanned, exclusions = _ORIGINAL_VALIDATE_REFERENCES(root, contract)
    findings = [
        finding
        for finding in findings
        if finding.code != "UNSCOPED_RECURSIVE_SCAN"
    ]
    scans: list[RecursiveScan] = []
    for path, relative, body in _eligible_recursive_files(root, contract):
        scans.extend(_recursive_scans(path, relative, body, root))
    _LAST_RECURSIVE_SCANS = scans

    for scan in scans:
        detail = (
            f"line={scan.line};language={scan.language};"
            f"receiver={scan.receiver};pattern={scan.pattern}"
        )
        if scan.classification == WORKSPACE_ROOT_DIRECT:
            findings.append(
                _legacy.Finding(
                    "UNSCOPED_RECURSIVE_SCAN",
                    scan.path,
                    detail,
                )
            )
        elif scan.classification == LEGACY_ROOT:
            findings.append(
                _legacy.Finding(
                    "LEGACY_ROOT_RECURSIVE_SCAN",
                    scan.path,
                    detail,
                )
            )
        elif scan.classification == UNRESOLVED:
            findings.append(
                _legacy.Finding(
                    "RECURSIVE_SCOPE_UNRESOLVED",
                    scan.path,
                    detail,
                )
            )

    return findings, scanned, exclusions


def counters(findings: list) -> dict:
    result = _ORIGINAL_COUNTERS(findings)
    classes = Counter(scan.classification for scan in _LAST_RECURSIVE_SCANS)
    unresolved = classes[UNRESOLVED]
    result.update(
        {
            "recursive_scan_syntax_candidate_count": len(_LAST_RECURSIVE_SCANS),
            "recursive_scan_candidate_file_count": len(
                {scan.path for scan in _LAST_RECURSIVE_SCANS}
            ),
            "workspace_root_direct_scan_count": classes[
                WORKSPACE_ROOT_DIRECT
            ],
            "domain_scoped_recursive_scan_count": classes[DOMAIN_SCOPED],
            "legacy_root_recursive_scan_count": classes[LEGACY_ROOT],
            "unresolved_recursive_receiver_count": unresolved,
            "recursive_scope_semantics_complete": unresolved == 0,
            "workspace_root_recursive_scan_count": classes[
                WORKSPACE_ROOT_DIRECT
            ],
        }
    )
    return result


_legacy.validate_references = validate_references
_legacy.counters = counters
main = _legacy.main


if __name__ == "__main__":
    raise SystemExit(main())
