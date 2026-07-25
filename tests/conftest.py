"""Shared pytest fixtures / path setup for the Server-Framework test-suite.

Core modules use flat imports (``from Log import Logs``) that only resolve with the
component directories on ``sys.path``; entry-point scripts normally inject Core
themselves. We replicate that here so the modules are importable under pytest.
"""
import os
import socket
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for _sub in ("Core", "Web", "Admin"):
    _path = os.path.join(PROJECT_ROOT, _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)


def free_port():
    """Return a currently-free TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
