"""Windows compatibility tests.

Added in the windows-compat sweep. mu2edaq-controlcenter is a PyQt6 +
QWebEngineView app with no prior pytest suite. This locks in that the
non-Qt-display modules import on Windows and that the control-room scripts ship
PowerShell ports. (The GUI itself needs a Qt platform; it is exercised
manually / via the start script's OpenGL probe.)
"""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PWSH = shutil.which("pwsh") or shutil.which("powershell")

SCRIPT_STEMS = [
    "bootstrap",
    "start-mu2edaq-controlcenter",
    "stop-mu2edaq-controlcenter",
]


@pytest.mark.parametrize("module", ["config_loader", "stylesheets"])
def test_non_gui_modules_import(module):
    # These modules have no Qt-display dependency and must import on Windows.
    __import__(module)


def test_scripts_have_both_forms():
    for stem in SCRIPT_STEMS:
        assert (REPO / f"{stem}.sh").is_file(), f"missing bash script: {stem}.sh"
        assert (REPO / f"{stem}.ps1").is_file(), f"missing PowerShell port: {stem}.ps1"


def test_symlink_aliases_present():
    # start.sh / stop.sh are thin aliases to the standardized scripts.
    assert (REPO / "start.sh").exists()
    assert (REPO / "stop.sh").exists()


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
@pytest.mark.parametrize("stem", SCRIPT_STEMS)
def test_powershell_scripts_parse(stem):
    path = (REPO / f"{stem}.ps1").as_posix()
    code = (
        "$e=$null;"
        f"[System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$null,[ref]$e)|Out-Null;"
        "if($e){$e|ForEach-Object{Write-Error $_};exit 1}else{exit 0}"
    )
    result = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-Command", code],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
