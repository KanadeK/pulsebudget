from __future__ import annotations

import pytest

from pulsebudget.cli import main


def test_version_prints_public_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "pulsebudget 0.1.0\n"
