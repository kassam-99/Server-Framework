import os
import socket
import sys
import threading
projet_name_admin = "\u001b[34mServer-Framework\u001b[0m - \u001b[32mServer\u001b[0m \u001b[37m#\u001b[0m\u001b[34mAdmin\u001b[0m"

class AdminChatClient:
    def __init__(self, ip, port, credentials):
        self.ip = ip
        self.port = port
        self.credentials = credentials
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MSize = 2048
        

    def connect_to_server(self):
        try:
            self.client.connect((self.ip, self.port))
            self.client.send(self.credentials.encode())  # Send the credentials as a single string

            # Read and validate the auth reply BEFORE starting the chat threads.
            # The server sends a colorized "[+] Authentication successful!" line,
            # so match on the stable substring rather than an exact string.
            authentication_result = self.client.recv(self.MSize).decode(errors='ignore')

            if "Authentication successful" in authentication_result:
                self.get_host_name_ip()
                print(f"\n{projet_name_admin} [$] Chat started")
                self.client_thread()
            else:
                print(f"\n[!] Authentication failed. Exiting.")
                self.client.close()
                os.abort()
    
        except Exception as e:
            print(f"\n[!] Error connecting to the [Project_name] - server: {e}")
            self.client.close()
            

    def get_host_name_ip(self):
        try:
            host_name = socket.gethostname()
            x = socket.gethostbyname(host_name)
            x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            x.connect(('10.0.0.0', 0))
            host_ip = x.getsockname()[0]
            print("[*] Hostname:", host_name)
            print("[*] IP:", host_ip)
            print("[*] Connected!")

        except Exception as e:
            print(f"\n{projet_name_admin} [!] Unable to get Hostname and IP: {e}")
            

    def handle_sent_msg(self):
        while True:
            try:
                msg_send = input()
                
                if not msg_send:
                    break
                
                else:
                    self.client.send(msg_send.encode())

            except Exception as e:
                print(f"\n{projet_name_admin} [!] Error handling message from [Project_name] - server: {e}")
                self.client.close()
                break
            

    def handle_rece_msg(self):
        while True:
            try:
                msg_rece = self.client.recv(self.MSize)
                if not msg_rece:
                    break
                elif msg_rece:
                    decoded_msg = msg_rece.decode(errors='ignore')
                    if decoded_msg.lower() == "exit":
                        self.client.close()
                        sys.exit()
                    else:
                        print(f"\n{decoded_msg}")
                else:
                    self.client.close()
                    break

            except Exception as e:
                print(f"\n{projet_name_admin} [!] Error handling message from [project_name] - server: {e}")
                self.client.close()
                break


    def client_thread(self):
        send = threading.Thread(target=self.handle_sent_msg)
        rece = threading.Thread(target=self.handle_rece_msg)
        send.start()
        rece.start()
        send.join()
        rece.join()
        

if __name__ == "__main__":

    # ANSI escape codes for colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    
    # Fancy welcome message
    
    print(f"{BLUE}========================================{RESET}")
    print(f"{GREEN}      Welcome to [Project_name]        {RESET}")
    print(f"{BLUE}========================================{RESET}")
    print(f"{RED}   Unleash the power of the server!      {RESET}\n")
    

    ip = input(f"{GREEN}[>] Enter IP of server:{RESET} ")
    port = int(input(f"{GREEN}[>] Enter port of server:{RESET} "))
    username = input(f"{GREEN}[>] Enter username of server:{RESET} ")
    password = input(f"{GREEN}[>] Enter password of server:{RESET} ")
    


    credentials = f"{username},{password}"

    admin_client = AdminChatClient(ip, port, credentials)
    admin_client.connect_to_server()

