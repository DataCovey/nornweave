#!/usr/bin/env python3
"""Run Alembic migrations (convenience script)."""
import subprocess
import sys
from pathlib import Path

# Ensure src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))


def main() -> None:
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )

if __name__ == "__main__":
    main()
