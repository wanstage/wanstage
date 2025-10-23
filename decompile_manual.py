import marshal
import sys
from typing import Any


def load_code_from_pyc(pyc_path: str) -> Any:
    # .pycの先頭16バイトはヘッダー
    with open(pyc_path, "rb") as f:
        _header = f.read(16)
        code_obj = marshal.load(f)
    return code_obj


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python decompile_manual.py <file.pyc>")
        return 2
    pyc = sys.argv[1]
    try:
        code = load_code_from_pyc(pyc)
        print(f"Loaded code object: {type(code)}")
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
