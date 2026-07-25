import os
import sys
import argparse

Project_Folder = "Server-Framework"
project_root = os.path.abspath(__file__)
index = project_root.find(Project_Folder)
index_length_project = len(Project_Folder)
if index != -1:
    core_dir = project_root[:index + index_length_project + 1] + "Core"
    sys.path.append(core_dir)


from Settings import FTP_Server


def build_server(shared_path, host="127.0.0.1", port=2121,
                 username="test", password="test"):
    """Configure and return an FTP_Server ready to serve `shared_path`."""
    server = FTP_Server(ftp_server_ip=host, ftp_server_port=port)

    server.ftp_username = username
    server.ftp_password = password
    server.ftp_user_path = shared_path
    server.ftp_user_permission = "elradfmwMT"

    # Anonymous access shares the same directory (read/list only by default).
    server.ftp_anonymous_path = shared_path
    server.ftp_anonymous_permission = "elr"

    # Throttle transfers to 30 KB/sec when throttling support is available.
    if server.dtp_handler is not None:
        server.dtp_handler.write_limit = 30720   # 30 KB/sec (30 * 1024)
        server.dtp_handler.read_limit = 30720    # 30 KB/sec (30 * 1024)

    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple FTP server (pyftpdlib)")
    parser.add_argument("--path", default=os.path.dirname(os.path.abspath(__file__)),
                        help="Directory to share over FTP (default: this folder)")
    parser.add_argument("--host", default="127.0.0.1", help="Host/interface to bind")
    parser.add_argument("--port", type=int, default=2121, help="Port to listen on")
    parser.add_argument("--username", default="test", help="FTP username")
    parser.add_argument("--password", default="test", help="FTP password")
    args = parser.parse_args(argv)

    shared_path = os.path.abspath(args.path)
    os.makedirs(shared_path, exist_ok=True)

    server = build_server(shared_path, host=args.host, port=args.port,
                          username=args.username, password=args.password)
    server.start_ftp_server()


if __name__ == "__main__":
    main()
