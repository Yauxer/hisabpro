from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_fact5_recette_e2e_complete():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "Test" / "recette_fact5_e2e.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
