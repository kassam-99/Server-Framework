"""Loopback FTP test: the handshake (USER/PASS login) AND an end-to-end
file transfer (STOR then RETR) over an ephemeral port, all with timeouts."""
import io
import threading
import time

import pytest
from ftplib import FTP, error_perm

from conftest import free_port

pyftpdlib = pytest.importorskip("pyftpdlib", reason="pyftpdlib required for FTP test")


def _start_server(share_dir, port):
    from Settings import FTP_Server
    srv = FTP_Server(ftp_server_ip="127.0.0.1", ftp_server_port=port)
    srv.ftp_username = "test"
    srv.ftp_password = "test"
    srv.ftp_user_path = str(share_dir)
    srv.ftp_user_permission = "elradfmwMT"
    srv.ftp_anonymous_path = None
    thread = threading.Thread(target=srv.start_ftp_server, daemon=True)
    thread.start()
    # Wait (bounded) for the server object to be created and bound.
    for _ in range(50):
        if srv.server is not None:
            break
        time.sleep(0.1)
    assert srv.server is not None, "FTP server failed to start"
    return srv, thread


def test_ftp_handshake_and_file_transfer(tmp_path):
    share = tmp_path / "share"
    share.mkdir()
    port = free_port()
    srv, thread = _start_server(share, port)
    payload = b"Server-Framework FTP loopback payload\n" * 10

    try:
        # --- Handshake: successful USER/PASS login ---
        ftp = FTP()
        ftp.connect("127.0.0.1", port, timeout=5)
        ftp.login("test", "test")
        assert ftp.pwd() == "/"

        # --- File transfer: upload (STOR) then download (RETR) ---
        ftp.storbinary("STOR uploaded.txt", io.BytesIO(payload))
        assert (share / "uploaded.txt").read_bytes() == payload

        buf = io.BytesIO()
        ftp.retrbinary("RETR uploaded.txt", buf.write)
        assert buf.getvalue() == payload

        ftp.quit()
    finally:
        if srv.server is not None:
            srv.server.close_all()


def test_ftp_handshake_rejects_bad_password(tmp_path):
    share = tmp_path / "share2"
    share.mkdir()
    port = free_port()
    srv, thread = _start_server(share, port)
    try:
        ftp = FTP()
        ftp.connect("127.0.0.1", port, timeout=5)
        with pytest.raises(error_perm):
            ftp.login("test", "wrong-password")
        ftp.close()
    finally:
        if srv.server is not None:
            srv.server.close_all()
