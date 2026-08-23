from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

from pulsebudget import __version__

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    _run([sys.executable, "-m", "ruff", "check", "."])
    _run([sys.executable, "-m", "mypy", "src", "scripts"])
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=pulsebudget",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ]
    )

    with tempfile.TemporaryDirectory(prefix=".release-check-", dir=PROJECT_ROOT) as temp_name:
        temp_dir = Path(temp_name)
        generated_demo = temp_dir / "demo"
        _run(
            [
                sys.executable,
                "-m",
                "pulsebudget",
                "compare",
                "examples/baseline.csv",
                "examples/candidate.csv",
                "--budget",
                "examples/budget.json",
                "--output",
                str(generated_demo),
            ]
        )
        for name in ("report.json", "report.md", "comparison.svg"):
            generated = (generated_demo / name).read_text(encoding="utf-8")
            committed = (PROJECT_ROOT / "docs" / "demo" / name).read_text(encoding="utf-8")
            if generated != committed:
                raise RuntimeError(f"docs/demo/{name} is stale; regenerate the committed demo")

        _run(
            [
                sys.executable,
                "-m",
                "pulsebudget",
                "compare",
                "examples/baseline.csv",
                "examples/candidate.csv",
                "--budget",
                "examples/budget-strict.json",
                "--output",
                str(temp_dir / "strict-demo"),
            ],
            expected=1,
        )

        _run([sys.executable, "scripts/package_release.py"])
        pyz = PROJECT_ROOT / "dist" / f"pulsebudget-{__version__}.pyz"
        _run([sys.executable, str(pyz), "--version"])
        _run(
            [
                sys.executable,
                str(pyz),
                "compare",
                "examples/baseline.csv",
                "examples/candidate.csv",
                "--budget",
                "examples/budget.json",
                "--output",
                str(temp_dir / "pyz-demo"),
            ]
        )

        smoke_venv = temp_dir / "wheel-venv"
        venv.EnvBuilder(with_pip=True).create(smoke_venv)
        smoke_python = smoke_venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheel = PROJECT_ROOT / "dist" / f"pulsebudget-{__version__}-py3-none-any.whl"
        _run([str(smoke_python), "-m", "pip", "install", "--no-deps", str(wheel)])
        _run([str(smoke_python), "-m", "pulsebudget", "--version"])
        _run(
            [
                str(smoke_python),
                "-m",
                "pulsebudget",
                "analyze",
                "examples/candidate.csv",
                "--budget",
                "examples/budget.json",
                "--output",
                str(temp_dir / "wheel-demo"),
            ]
        )

    print("Release check passed.")
    return 0


def _run(command: list[str], expected: int = 0) -> None:
    print(f"+ {subprocess.list2cmdline(command)}", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if completed.returncode != expected:
        raise subprocess.CalledProcessError(completed.returncode, command)


if __name__ == "__main__":
    raise SystemExit(main())
