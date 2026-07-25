import threading
import os
import sys

Project_Folder = "Server-Framework"
project_root = os.path.abspath(__file__)
index = project_root.find(Project_Folder)
index_length_project = len(Project_Folder)
if index != -1:
    core_dir = project_root[:index+index_length_project+1]+"Core"
sys.path.append(core_dir)
        
from Settings import TCP_Server


def handle_rece_msg(server):
    while True:
        try:
            msg_rece = server.recv(4505)
            if msg_rece:
                print("[Client]: ", msg_rece.decode())  # Decode a message
            else:
                server.close()
                break
        except Exception as e:
            print(f'[!] Error handling message from server: {e}')
            server.close()
            break


def handle_sent_msg(server):
    while True:
        try:
            msg_send = input()
            if msg_send:
                server.send(msg_send.encode())  # Encode a message
            else:
                server.close()
                break
        except Exception as e:
            print(f'[!] Error handling message from server: {e}')
            server.close()
            break


def server_thread(client_socket):
    send = threading.Thread(target=handle_sent_msg, args=(client_socket,))
    rece = threading.Thread(target=handle_rece_msg, args=(client_socket,))
    send.start()
    rece.start()
    send.join()
    rece.join()



if __name__ == "__main__":
    while True:
        server = TCP_Server()
        server.start_TCP_Server()

        client_socket, addr = server.tcp_handler.accept()

        print("[>] Accepted connection from: %s:%d" % (addr[0], addr[1]))
        print("[$] Chat started")

        try:
            server_thread(client_socket)

        except Exception as e:
            print(f"Error: {e}")
            server.close()
            break
