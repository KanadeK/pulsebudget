from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from pulsebudget import __version__

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def main() -> int:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    environment = os.environ.copy()
    environment.setdefault("SOURCE_DATE_EPOCH", "1767225600")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--sdist",
            "--outdir",
            str(DIST_DIR),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )

    wheel = DIST_DIR / f"pulsebudget-{__version__}-py3-none-any.whl"
    source_distribution = DIST_DIR / f"pulsebudget-{__version__}.tar.gz"
    if not wheel.is_file() or not source_distribution.is_file():
        raise RuntimeError("build did not create the expected wheel and source distribution")

    pyz = DIST_DIR / f"pulsebudget-{__version__}.pyz"
    with zipfile.ZipFile(pyz, "w") as archive:
        _write_zip_entry(
            archive,
            "__main__.py",
            b"from pulsebudget.cli import main\nraise SystemExit(main())\n",
        )
        package_dir = PROJECT_ROOT / "src" / "pulsebudget"
        for path in sorted(package_dir.glob("*.py")):
            _write_zip_entry(
                archive,
                f"pulsebudget/{path.name}",
                path.read_bytes(),
            )

    examples_zip = DIST_DIR / f"pulsebudget-{__version__}-examples.zip"
    with zipfile.ZipFile(examples_zip, "w") as archive:
        for path in sorted((PROJECT_ROOT / "examples").iterdir()):
            if path.is_file():
                _write_zip_entry(archive, f"examples/{path.name}", path.read_bytes())

    artifacts = sorted((wheel, source_distribution, pyz, examples_zip), key=lambda path: path.name)
    manifest = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in artifacts
    )
    (DIST_DIR / "SHA256SUMS.txt").write_text(
        manifest,
        encoding="utf-8",
        newline="\n",
    )

    print("Release assets:")
    for path in [*artifacts, DIST_DIR / "SHA256SUMS.txt"]:
        print(f"- {path.name}")
    return 0


def _write_zip_entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


if __name__ == "__main__":
    raise SystemExit(main())
