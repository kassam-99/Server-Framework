# Libraries to handle I/O files, folders and Manage a system
import builtins
import json
import re
import os
import platform
from pathlib import Path

# Libraries to setup and handle a connection settings   Server-Framework
import shutil
import socket
import asyncio
import subprocess
import websockets
from http.server import HTTPServer


# Other:
from Log import Logs
from Emergency import EmergencyPathManager





class Path_Settings:
    
    
    def __init__(self):
        self.Log = Logs()
        self.Log.LogEngine("Settings - Path_Settings", "LogCore_Settings")
        self.EXCLUDED_DIRS = ["server_env","Core", "Logs", "Admin", ".vscode", "__pycache__", ".git", ".env"]
        self.EXCLUDED_Files = ["Admin", "AdminPanel", "Dashboard", "Commands", ".env", ".gitignore", "requirements.txt", ".git"]
        self.EXCLUDED_EXT = [
            # Temporary & Log Files
            ".tmp", ".log", ".bak", ".gz",
            
            # Compiled Files
            ".pyc", ".pyo", ".class", ".o", ".obj", ".so", ".dll", ".exe", ".out",
            
            # Configuration & Environment Files
            ".env", ".cfg", ".config", ".ini", ".toml", ".lock",
            
            # Documentation & ReadMe Files
            ".md", ".txt", ".rst", ".adoc", ".rtf", ".doc", ".docx", ".pdf", ".CSV", ".csv",

            # Version Control & Git
            ".gitignore", ".gitattributes", ".gitmodules",
            
            # Archives & Compressed Files
            ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz",
            
            # Virtual Environment & Package Files
            ".whl", ".egg", ".dist-info", ".tar.gz",
            
            # Shell & Executable Scripts
            ".sh", ".bat", ".cmd", ".ps1",
            
            # Image, Video & Media Files
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".tiff",
            ".mp3", ".wav", ".flac", ".mp4", ".avi", ".mov", ".mkv", ".webm",
            
        ]
        
        self.EXCLUDED_PATHS = []

        self.EmergencyMode = False
        
        self.Frameworkpaths = __file__
        self.script_dir = os.path.dirname(self.Frameworkpaths)
        self.Pathsfile = os.path.join(self.script_dir, "Paths.json")
        self.ProcessesFile = os.path.join(self.script_dir, "ProcessesLab.json")
        
        # Ensure Paths.json exists with a default structure
        if not os.path.exists(self.Pathsfile):
            self.EmergencyPaths()
        else:
            try:
                with open(self.Pathsfile, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                if not data or "ProjectRoot" not in data or "Server-FrameworkPath" not in data["ProjectRoot"]:
                    self.EmergencyPaths()
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.Log.LogsMessages(f"[!] Invalid or missing Paths.json: {e}", "CRITICAL")
                self.EmergencyPaths()
    
        self.file_path = os.path.abspath(__file__)
        # Corrected project path detection
        index = self.file_path.find("Server-Framework")  # Fixed string case
        if index != -1:
            self.Project_Path = self.file_path[:index + 16]  
            
        else:
            error_message = "[!] Project directory 'Server-Framework' not found in file path"
            self.Log.LogsMessages(error_message, "CRITICAL")
            raise ValueError(error_message)
    

    def checkpath(self, targetpath):
        try:
            with open(self.Pathsfile, 'r', encoding="utf-8") as f:
                data = json.load(f)
            # Search through all sections for the target path
            for section in data.values():
                if isinstance(section, dict) and targetpath in section:
                    path = section[targetpath]
                    if os.path.exists(path):
                        return path
                    else:
                        self.Log.LogsMessages(f"[!] Path {path} for {targetpath} does not exist", "WARNING")
            self.Log.LogsMessages(f"[!] {targetpath} not found in Paths.json", "DEBUG")
            return None
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.Log.LogsMessages(f"[!] Error reading Paths.json: {e}", "CRITICAL")
            self.EmergencyPaths()
            return None
        except Exception as e:
            self.Log.LogsMessages(f"[!] Unexpected error in checkpath: {e}", "CRITICAL")
            return None


    def EmergencyPaths(self):
        self.Log.LogsMessages("[!] Emergency Script is called", "CRITICAL")
        # Determine project root by walking up the directory tree
        project_root = self.script_dir
        while project_root != os.path.dirname(project_root):  # Stop at filesystem root
            if os.path.basename(project_root) == "Server-Framework":
                break
            project_root = os.path.dirname(project_root)
        else:
            project_root = self.script_dir  # Fallback to script directory if not found
        
        # Define default paths
        default_paths = {
            "ProjectRoot": {
                "Server-FrameworkPath": project_root
            },
            "Logs": {
                "Server-FrameworkLogs": os.path.join(project_root, "Logs")
            },
            "Core": {
                "Server-FrameworkCore": os.path.join(project_root, "Core")
            }
        }
        
        # Create directories if they don’t exist
        for section in default_paths.values():
            for path in section.values():
                os.makedirs(path, exist_ok=True)
        
        # Write to Paths.json
        try:
            with open(self.Pathsfile, 'w', encoding="utf-8") as f:
                json.dump(default_paths, f, indent=4)
            self.Log.LogsMessages(f"[!] Created Paths.json with default paths at {self.Pathsfile}", "INFO")
        except Exception as e:
            self.Log.LogsMessages(f"[!] Failed to create Paths.json: {e}", "CRITICAL")
        
        # Optionally call EmergencyPathManager if needed
        EmergencyPathManager().StartEmergencyModePath()

    
        
        
    




class Server_Settings:
    
    DEFAULT_IP = "localhost"
    DEFAULT_PORT = 3000
    DEFAULT_ServerUsername = "admin"
    DEFAULT_ServerPassword = "admin"
        
    def __init__(self, server_main_ip=DEFAULT_IP, server_main_port=DEFAULT_PORT, ServerName=DEFAULT_ServerUsername, ServerPassword=DEFAULT_ServerPassword):
        """
        Initialize server settings.
        """
        self.Log = Logs()
        self.Log.LogEngine("Settings - Server_Settings", "LogCore_Settings")
        self.ServerName = ServerName
        self.ServerPassword = ServerPassword
        self.server_main_ip = server_main_ip
        self.server_main_port = server_main_port
        self.max_connections = None
        self.timeout = None
        self.malware_threads_max = None


    def set_max_connections(self, max_connections):
        """
        Set the maximum number of connections.
        """
        if not isinstance(max_connections, int) or max_connections < 0:
            self.Log.print_and_log("[!] max_connections must be a non-negative integer", "WARNING")
        self.max_connections = max_connections


    def set_timeout(self, timeout):
        """
        Set the timeout value.
        """
        if not isinstance(timeout, (int, float)) or timeout < 0:
            self.Log.print_and_log("[!] timeout must be a non-negative numeric value", "WARNING")
        self.timeout = timeout


    def set_malware_threads_max(self, malware_threads_max):
        """
        Set the maximum number of threads for handling malware.
        """
        if not isinstance(malware_threads_max, int) or malware_threads_max < 0:
            self.Log.print_and_log("[!] malware_threads_max must be a non-negative integer", "WARNING")
        self.malware_threads_max = malware_threads_max
        
        
    @staticmethod    
    def ConnectionPath():
        """
        import os
        import sys
        
        project_root = os.path.abspath(__file__)
        index = project_root.find("Server-Framework")
        if index != -1:
            core_dir = project_root[:index+6]+"Core"
        sys.path.append(core_dir)
        
        from Settings import *
        """
        pass


    @staticmethod
    def check_system():
        system_platform = platform.system().lower()
        platform_mapping = {
            'linux': 'Linux',
            'windows': 'Windows',
            'darwin': 'Mac',
            'aix': 'AIX',
            'freebsd': 'FreeBSD',
            'netbsd': 'NetBSD',
            'openbsd': 'OpenBSD',
            'sunos': 'Solaris',
            'cygwin': 'Cygwin',
            'msys': 'MSYS',
            'os2': 'OS/2',
            'riscos': 'RISC OS'
        }
        return platform_mapping.get(system_platform, 'Unknown')
    
        
    @staticmethod
    def get_available_terminals(system_type, list_param=False):
        if system_type != "Linux":
            print("[!] Unsupported platform")
            return []
        
        common_terminals = [
            "konsole",
            "xfce4-terminal",
            "lxterminal",
            "xterm",
            "terminator",
            "screen"
        ]
        search_paths = ["/usr/bin", "/usr/local/bin", "/bin", "/snap/bin"]
        
        available_terminals = set()

        # Use `shutil.which()` for direct binary detection
        for term in common_terminals:
            if shutil.which(term):
                available_terminals.add(term)
        
        # Manual directory scan (only if needed)
        for path in search_paths:
            if not os.path.isdir(path):
                continue
            try:
                for binary in Path(path).iterdir():
                    if binary.is_file() and os.access(binary, os.X_OK):
                        name = binary.name
                        if name in common_terminals:
                            available_terminals.add(name)
            except Exception as e:
                print(f"[!] Error scanning {path}: {e}")

        available_terminals = sorted(available_terminals)

        if list_param:
            print("[*] Available terminals:")
            if available_terminals:
                for i, terminal in enumerate(available_terminals, start=1):
                    print(f"[{i}] {terminal}")
            else:
                print("    None detected from supported list.")
            
            # Recommend missing terminals
            missing_terminals = [term for term in common_terminals if term not in available_terminals]
            if missing_terminals:
                print("[*] Recommended terminals to install:")
                for i, terminal in enumerate(missing_terminals, start=1):
                    print(f"    [{i}] {terminal} (e.g., 'sudo apt install {terminal}')")

        return available_terminals
    

    @staticmethod
    def check_for_port(p1, p2):
        for port in range(p1, p2+1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_port:
                socket_port.settimeout(1)
                available_port = socket_port.connect_ex(('localhost', port))
                if available_port != 0:
                    return port
        raise Exception("[!] Couldn't find an open port")
    
    
    @staticmethod
    def start_server():
        print("Select the server type:")
        print("[1] Socket_tcp_Server")
        print("[2] Websockets_Server")
        print("[3] HTTP_Server")
        print("[6] Exit")

        try:
            choice = int(input("[>] Enter the number corresponding to the server type: "))

            if choice == 1:
                server = TCP_Server()
                server.start_TCP_Server()
                
            elif choice == 2:
                server = Websockets_Server()
                server.start_websockets_server()

            elif choice == 3:
                server = HTTP_Server()
                server.start_http_server()

            elif choice == 4:
                print("Exiting the program.")
                return

            else:
                print("[!] Invalid choice. Please enter a valid number.")

        except ValueError:
            print("[!] Invalid input. Please enter a valid number.")


    def server_details(self, connection_type, server_ip, server_port):
        try:

            if len(server_ip) >= 1:
                lserver = f"[*] \033[34m{connection_type}\033[0m Server is \033[32mrunning!\033[0m, listening on, \033[33m{server_ip}:{server_port}\033[0m"
            else:
                server_ip = socket.gethostbyname(socket.gethostname())
                lserver = f"[*] \033[34m{connection_type}\033[0m Server is \033[32mrunning!\033[0m, listening on, \033[33m{server_ip}:{server_port}\033[0m"
                
            host_name = socket.gethostname()
            x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            x.connect(('10.0.0.0', 0))
            server_ip = x.getsockname()[0]
                
            self.Log.print_and_log(f"{lserver}")
            self.Log.print_and_log(f"[-] Hostname: \033[31m{host_name}\033[0m")
            self.Log.print_and_log(f"[-] Platform: \033[31m{self.check_system()}\033[0m")
            self.Log.print_and_log(f"[-] IP: \033[33m{server_ip}\033[0m")
            self.Log.print_and_log(f"[-] Port: \033[33m{server_port}\033[0m")
            self.Log.print_and_log(f"[-] Connection type: \033[34m{connection_type}\033[0m")
            self.Log.print_and_log(f"[-] Share IP and port with the client")
            
        except Exception as e:
            self.Log.print_and_log(f"[!] Unable to get Hostname and IP: {e}", "CRITICAL")





class TCP_Server(Server_Settings):
    def __init__(self, tcp_server_ip=None, tcp_server_port=None):
        super().__init__()
        try:
            if tcp_server_ip is None:
                self.tcp_server_ip = "localhost"
            elif not isinstance(tcp_server_ip, str):
                self.Log.print_and_log("[!] tcp_server_ip must be a string", "CRITICAL")
            else:
                self.tcp_server_ip = tcp_server_ip

            if tcp_server_port is None:
                self.tcp_server_port = self.check_for_port(8000, 8099)
            elif not isinstance(tcp_server_port, int):
                self.Log.print_and_log("[!] tcp_server_port must be an integer", "CRITICAL")
            else:
                self.tcp_server_port = tcp_server_port

            self.tcp_handler = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_handler.bind((self.tcp_server_ip, self.tcp_server_port))
            self.tcp_handler.listen() # Number of Bad Connections to Allow before Refusing
            
        except ValueError as ve:
    
            self.Log.print_and_log(f"[!] Error: {ve}", "ERROR")
            
        except Exception as e:
            self.Log.print_and_log(f"[!] Error setting up server: {e}", "ERROR")
            raise
        """        
        # In order to accept connections you need to add TCP_Server variable
          to your code ex:
          server = TCP_Server()
          server.start_TCP_Server()
          client_socket, addr = server.tcp_handler.accept()
        """
    def start_TCP_Server(self):
        try:
            self.server_details("TCP", self.tcp_server_ip, self.tcp_server_port)
            
        except Exception as e:
            self.Log.print_and_log(f"[!] Error accepting connection: {e}", "ERROR")





            

            
            
            
             
class Websockets_Server(Server_Settings):
    def __init__(self, Websocket_server_ip=None, Websocket_server_port=None):
        super().__init__()
        try:
            
            if Websocket_server_ip is None:
                self.Websocket_server_ip = "localhost"
            elif not isinstance(Websocket_server_ip, str):
                self.Log.print_and_log("[!] Websocket_server_ip must be a string", "CRITICAL")
            else:
                self.Websocket_server_ip = Websocket_server_ip

            if Websocket_server_port is None:
                self.Websocket_server_port = self.check_for_port(8200, 8299)
            elif not isinstance(Websocket_server_port, int):
                self.Log.print_and_log("[!] Websocket_server_port must be an integer", "CRITICAL")
            else:
                self.Websocket_server_port = Websocket_server_port
                
            self.Server_Websocket = f"ws://{self.Websocket_server_ip}:{self.Websocket_server_port}"
            self.Websocket_Handler = None 
            # self.Websocket_Handler: Main function to Run a server.
            # It must be assigned in a server script

        except Exception as e:
            self.Log.print_and_log(f"[!] Error setting up websockets server: {e}", "ERROR")
            raise
        """        
        # To run a Websocket server:
          def Main_handler():
                   ...
          WS_server = Websockets_Server()
          WS_server.Websocket_Handler = Main_handler => Main function
          WS_server.start_websockets_server()
        """
    def start_websockets_server(self):
        if self.Websocket_Handler is None:
            self.Log.print_and_log("[!] websocket_handler must be set before starting the server", "WARNING")
        
        self.server_details("Websockets", self.Websocket_server_ip, self.Websocket_server_port)
        try:
            async def main():
                async with websockets.serve(self.Websocket_Handler, self.Websocket_server_ip, self.Websocket_server_port):
                    await asyncio.Future()
    
            asyncio.run(main())
    
        except websockets.WebSocketException as e:
            self.Log.print_and_log(f"[!] WebSocket error: {e}", "ERROR")
        except OSError as e:
            self.Log.print_and_log(f"[!] OS error: {e}", "ERROR")
        except Exception as e:
            self.Log.print_and_log(f"[!] Error during websocket server startup: {e}", "ERROR")
    
        finally:
            self.Log.print_and_log("[!] Closing Websockets server", "CRITICAL")

            





class HTTP_Server(Server_Settings):
    def __init__(self, http_server_ip=None, http_server_port=None):
        super().__init__()
        
        try:
            if http_server_ip is None:
                self.http_server_ip = "localhost"
            elif not isinstance(http_server_ip, str):
                self.Log.print_and_log("[!] http_server_ip must be a string", "CRITICAL")
            else:
                self.http_server_ip = http_server_ip

            if http_server_port is None:
                self.http_server_port = self.check_for_port(8300, 8399)
            elif not isinstance(http_server_port, int):
                self.Log.print_and_log("[!] http_server_port must be an integer", "CRITICAL")
            else:
                self.http_server_port = http_server_port
                
            self.HTTP_STATUS_OK = 200
            self.HTTP_STATUS_BAD_REQUEST = 400
            self.HTTP_Handler = None
        
        except Exception as e:
            self.Log.print_and_log(f"[!] Error setting up HTTP connection: {e}", "ERROR")
            
        """
        HTTPServer_GroupChat = HTTP_Server()
        HTTPServer_GroupChat.HTTP_Handler = GroupChatHandler
        HTTP_STATUS = HTTPServer_GroupChat.HTTP_STATUS_OK
        
        HTTPServer_GroupChat.start_http_server()
        
        while True:  # Keep the server running continuously
        client_connection, client_address = HTTPServer_GroupChat.server.accept()
        client = GroupChatHandler(client_connection, client_address, HTTPServer_GroupChat)
        
        clients.append(client)
        threading.Thread(target=client.handle).start() 
        """
    
    def start_http_server(self):
        if self.HTTP_Handler is None:
            self.Log.print_and_log("[!] HTTP_Handler must be set before starting the server", "WARNING")
            return  # Don't proceed if the handler is not set
        self.server_details("HTTP", self.http_server_ip, self.http_server_port)

        Run_server = None
        try:
            Run_server = HTTPServer((self.http_server_ip, self.http_server_port), self.HTTP_Handler)
            Run_server.serve_forever()

        except Exception as e:
            self.Log.print_and_log(f"[!] Error accepting HTTP connection: {e}", "ERROR")
            if Run_server is not None:
                Run_server.server_close()

        
     
            
            
            
            





class UDP_Server(Server_Settings):
    def __init__(self, udp_server_ip=None, udp_server_port=None):
        super().__init__()
        try:
            if udp_server_ip is None:
                self.udp_server_ip = "localhost"
            elif not isinstance(udp_server_ip, str):
                self.Log.print_and_log("[!] udp_server_ip must be a string", "CRITICAL")
                self.udp_server_ip = "localhost"
            else:
                self.udp_server_ip = udp_server_ip

            if udp_server_port is None:
                self.udp_server_port = self.check_for_port(8100, 8199)
            elif not isinstance(udp_server_port, int):
                self.Log.print_and_log("[!] udp_server_port must be an integer", "CRITICAL")
                self.udp_server_port = 8100
            else:
                self.udp_server_port = udp_server_port

            self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_server.bind((self.udp_server_ip, self.udp_server_port))

        except Exception as e:
            self.Log.print_and_log(f"[!] Error setting up UDP server: {e}", "ERROR")
            raise

    def start_udp_server(self):
        try:
            self.server_details("UDP", self.udp_server_ip, self.udp_server_port)
        except Exception as e:
            self.Log.print_and_log(f"[!] Error starting UDP server: {e}", "ERROR")


class FTP_Server(Server_Settings):
    """A thin wrapper around pyftpdlib exposing a simple, configurable FTP server.

    pyftpdlib is imported lazily so that importing Settings never fails when the
    optional dependency is missing; the feature degrades gracefully instead.
    """

    def __init__(self, ftp_server_ip=None, ftp_server_port=None):
        super().__init__()
        self.ftp_server_ip = ftp_server_ip if isinstance(ftp_server_ip, str) else "127.0.0.1"
        if ftp_server_port is None:
            self.ftp_server_port = self.check_for_port(2121, 2199)
        elif isinstance(ftp_server_port, int):
            self.ftp_server_port = ftp_server_port
        else:
            self.ftp_server_port = 2121

        # Default credentials / shared directory (override before starting).
        self.ftp_username = "user"
        self.ftp_password = "12345"
        self.ftp_user_path = os.getcwd()
        self.ftp_user_permission = "elradfmwMT"
        self.ftp_anonymous_path = None
        self.ftp_anonymous_permission = "elr"
        self.server = None

        # dtp_handler is a class (ThrottledDTPHandler) whose write_limit/read_limit
        # class attributes callers may tune before start_ftp_server().
        try:
            from pyftpdlib.handlers import ThrottledDTPHandler
            self.dtp_handler = ThrottledDTPHandler
        except ImportError:
            self.dtp_handler = None
            self.Log.print_and_log("[!] pyftpdlib not installed; FTP throttling unavailable", "WARNING")

    def start_ftp_server(self):
        try:
            from pyftpdlib.authorizers import DummyAuthorizer
            from pyftpdlib.handlers import FTPHandler
            from pyftpdlib.servers import FTPServer
        except ImportError:
            self.Log.print_and_log("[!] pyftpdlib not installed; cannot start FTP server", "CRITICAL")
            return

        authorizer = DummyAuthorizer()
        user_path = self.ftp_user_path or os.getcwd()
        os.makedirs(user_path, exist_ok=True)
        authorizer.add_user(self.ftp_username, self.ftp_password, user_path, perm=self.ftp_user_permission)
        if self.ftp_anonymous_path:
            os.makedirs(self.ftp_anonymous_path, exist_ok=True)
            authorizer.add_anonymous(self.ftp_anonymous_path, perm=self.ftp_anonymous_permission)

        handler = FTPHandler
        handler.authorizer = authorizer
        if self.dtp_handler is not None:
            handler.dtp_handler = self.dtp_handler

        try:
            self.server_details("FTP", self.ftp_server_ip, self.ftp_server_port)
        except Exception:
            pass

        self.server = FTPServer((self.ftp_server_ip, self.ftp_server_port), handler)
        try:
            self.server.serve_forever()
        except Exception as e:
            self.Log.print_and_log(f"[!] Error running FTP server: {e}", "ERROR")
        finally:
            self.server.close_all()


if __name__ == "__main__":
    # Test the method
    terminals = Server_Settings.get_available_terminals("Linux", list_param=False)
    print(f"Detected terminals: {terminals}")

