"""Unit tests for pure logic across the framework."""
import os
import socket

import pytest

from conftest import free_port


# --------------------------------------------------------------------------- #
# Server_Settings helpers
# --------------------------------------------------------------------------- #
def test_check_system_returns_known_platform():
    from Settings import Server_Settings
    result = Server_Settings.check_system()
    assert result in {
        "Linux", "Windows", "Mac", "AIX", "FreeBSD", "NetBSD", "OpenBSD",
        "Solaris", "Cygwin", "MSYS", "OS/2", "RISC OS", "Unknown",
    }


def test_get_available_terminals_unsupported_platform():
    from Settings import Server_Settings
    assert Server_Settings.get_available_terminals("Windows") == []


def test_get_available_terminals_linux_is_iterable():
    from Settings import Server_Settings
    terms = Server_Settings.get_available_terminals("Linux")
    assert list(terms) == sorted(terms)


def test_check_for_port_returns_open_port():
    from Settings import Server_Settings
    port = Server_Settings.check_for_port(49200, 49300)
    assert 49200 <= port <= 49300
    # The returned port should be bindable (i.e. actually free).
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_check_for_port_raises_when_none_free():
    from Settings import Server_Settings
    port = free_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))
        s.listen()
        with pytest.raises(Exception):
            # Single-port window that is occupied -> no open port found.
            Server_Settings.check_for_port(port, port)


# --------------------------------------------------------------------------- #
# EXCLUDED_EXT regression (the ".csv" / ".gitignore" missing-comma bug)
# --------------------------------------------------------------------------- #
def test_excluded_ext_entries_are_distinct():
    from Settings import Path_Settings
    ps = Path_Settings()
    assert ".csv" in ps.EXCLUDED_EXT
    assert ".gitignore" in ps.EXCLUDED_EXT
    assert ".csv.gitignore" not in ps.EXCLUDED_EXT


# --------------------------------------------------------------------------- #
# ModeManager.extract_folders_and_files
# --------------------------------------------------------------------------- #
def test_extract_folders_and_files():
    from Modes import ModeManager
    mm = ModeManager()
    sample = "\n".join([
        "   Cloud:",
        "     server.py",
        "     client.py",
        "   notes",            # no extension -> ignored
    ])
    files = mm.extract_folders_and_files(sample)
    assert "server.py" in files
    assert "client.py" in files
    assert "notes" not in files


# --------------------------------------------------------------------------- #
# ReportGenerator writes real report files
# --------------------------------------------------------------------------- #
def test_report_generator_writes_files(tmp_path, monkeypatch):
    import ReportGenerator as RG
    monkeypatch.setattr(RG, "Data_dir", str(tmp_path) + os.sep)
    gen = RG.Report_Generator()
    data = [{"Name": "A", "Age": 1}, {"Name": "B", "Age": 2}]
    gen.TXT_GenerateReport(data, filename="report.txt")
    gen.JSON_GenerateReport(data, filename="report.json")
    gen.CSV_GenerateReport(data, filename="report.csv")
    written = os.listdir(tmp_path)
    assert any(f.startswith("report") and f.endswith(".txt") for f in written)
    assert any(f.startswith("report") and f.endswith(".json") for f in written)
    assert any(f.startswith("report") and f.endswith(".csv") for f in written)


# --------------------------------------------------------------------------- #
# Web_Logs.Logs verbose regression (undefined self.verbose bug)
# --------------------------------------------------------------------------- #
def test_web_logs_verbose_does_not_raise(tmp_path, monkeypatch, capsys):
    import Web_Logs
    logger = Web_Logs.Logs(verbose=True)   # used to raise TypeError
    # point the log file at a temp location so we don't pollute the repo
    monkeypatch.setattr(logger, "mainloggerfile", str(tmp_path / "main.log"))
    logger.log_to_file("hello", "INFO")    # used to raise AttributeError (self.verbose)
    out = capsys.readouterr().out
    assert "hello" in out
    assert os.path.exists(tmp_path / "main.log")
