#!/usr/bin/env python3
"""Run Alembic migrations (convenience script)."""
import os
import sys

# Ensure src is on path when run from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import subprocess

def main() -> None:
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        check=True,
    )

if __name__ == "__main__":
    main()
