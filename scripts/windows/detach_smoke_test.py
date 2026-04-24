from __future__ import annotations

import sys
import time
from pathlib import Path


def main() -> int:
    out = Path(r"C:\Users\sethcodex\work\virtue-bench-2\results\detach_smoke_test_python.txt")
    out.write_text(f"started {time.strftime('%Y-%m-%dT%H:%M:%S')}\n", encoding="utf-8")
    time.sleep(8)
    out.write_text(f"finished {time.strftime('%Y-%m-%dT%H:%M:%S')}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
