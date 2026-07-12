"""Convenience wrapper around PyInstaller for the Clinic LOR desktop app.

Usage:

    python scripts/build_exe.py            # folder build (dist/ClinicLOR/)
    python scripts/build_exe.py --onefile  # single-file exe (dist/ClinicLOR.exe)

The heavy lifting lives in ``clinic.spec``. This script just wires arguments
and reports the resulting artefact paths so CI logs stay tidy.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "clinic.spec"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Clinic LOR executable.")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Produce a single-file bundle instead of a folder.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe build/ and dist/ before rebuilding.",
    )
    return parser.parse_args()


def _run_pyinstaller(*, onefile: bool, clean: bool) -> None:
    if clean:
        for name in ("build", "dist"):
            target = ROOT / name
            if target.exists():
                print(f"[clean] removing {target}")
                shutil.rmtree(target)

    env = os.environ.copy()
    env["ONEFILE"] = "1" if onefile else "0"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--log-level",
        "INFO",
        str(SPEC),
    ]
    print("[build] running:", " ".join(cmd))
    result = subprocess.run(cmd, env=env, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller exited with code {result.returncode}")


def _report() -> None:
    dist = ROOT / "dist"
    if not dist.exists():
        return
    print("\nBuild artefacts:")
    for entry in sorted(dist.iterdir()):
        size = entry.stat().st_size if entry.is_file() else _dir_size(entry)
        print(f"  {entry.name}   ({size / 1024 / 1024:,.1f} MB)")


def _dir_size(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def main() -> None:
    args = _parse_args()
    if not SPEC.is_file():
        raise SystemExit(f"Spec file missing: {SPEC}")
    _run_pyinstaller(onefile=args.onefile, clean=args.clean)
    _report()


if __name__ == "__main__":
    main()
