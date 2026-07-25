"""Contract tests for the canonical launcher, dashboard.py.

These exercise the two robustness guarantees of the shared dashboard contract:
  * ``dashboard.py --demo`` runs the real features end-to-end and exits 0.
  * ``dashboard.py < /dev/null`` (non-TTY stdin) exits promptly with bounded output.
"""
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD = os.path.join(PROJECT_ROOT, "dashboard.py")


def test_demo_runs_and_exits_zero():
    proc = subprocess.run(
        [sys.executable, DASHBOARD, "--demo"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout.decode("utf-8", "replace")
    text = proc.stdout.decode("utf-8", "replace")
    assert "Demo complete" in text
    assert "Traceback" not in text


def test_demo_json_summary():
    proc = subprocess.run(
        [sys.executable, DASHBOARD, "--demo", "--json"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    assert proc.returncode == 0
    assert '"project_root"' in proc.stdout.decode("utf-8", "replace")


def test_eof_stdin_exits_promptly():
    with open(os.devnull, "rb") as devnull:
        proc = subprocess.run(
            [sys.executable, DASHBOARD],
            cwd=PROJECT_ROOT,
            stdin=devnull,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=12,
        )
    assert proc.returncode == 0
    # Bounded output: must be well under 1 MB.
    assert len(proc.stdout) < 1_000_000


def test_help_exits_zero():
    proc = subprocess.run(
        [sys.executable, DASHBOARD, "--help"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=12,
    )
    assert proc.returncode == 0
    assert "--demo" in proc.stdout.decode("utf-8", "replace")
