from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def assert_jsx(files):
    if not shutil.which("node"):
        pytest.skip("Node.js absent")
    result = subprocess.run(
        ["node", str(ROOT / "Test/check_jsx.cjs"), *(str(ROOT / f) for f in files)],
        cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "OK analyse et compilation JSX" in result.stdout
