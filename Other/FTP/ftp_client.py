from ftplib import FTP
import ftplib
import argparse


def interactive_session(host="127.0.0.1", port=2121, username="test", password="test"):
    """Open an interactive FTP session against the given server."""
    ftp = FTP()
    ftp.connect(host, port)
    ftp.login(username, password)

    try:
        while True:
            current_path = ftp.pwd()
            print(f"Current directory: {current_path}")

            ftp.dir()

            user_input = input("Enter path or command (type 'exit' to quit): ")

            if user_input.lower() == 'exit':
                break

            try:
                # Try changing to the specified directory
                ftp.cwd(user_input)
                print(f"Changed to directory: {user_input}")
            except ftplib.error_perm:
                # If changing directory fails, try sending it as an FTP command
                try:
                    response = ftp.sendcmd(user_input)
                    print(f"Command response: {response}")
                except ftplib.error_perm as e:
                    print(f"Error: {e}")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple interactive FTP client")
    parser.add_argument("--host", default="127.0.0.1", help="FTP server host")
    parser.add_argument("--port", type=int, default=2121, help="FTP server port")
    parser.add_argument("--username", default="test", help="FTP username")
    parser.add_argument("--password", default="test", help="FTP password")
    args = parser.parse_args()

    interactive_session(host=args.host, port=args.port,
                        username=args.username, password=args.password)
