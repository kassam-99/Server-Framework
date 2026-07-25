from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
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
        


from Settings import HTTP_Server


clients = []


class GroupChatHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        command = input("Server - enter: ")
        self.send_response(HTTP_STATUS)
        self.send_header("Content-type", "text")
        self.end_headers()
        self.wfile.write(command.encode())
        
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        self.send_response(HTTP_STATUS)
        self.end_headers()

        data = parse_qs(self.rfile.read(length).decode())
        if "message" in data:
            message = data["message"][0]
            print("user: " ,message)
        else:
            self.send_message("Invalid request. No message provided.")

if __name__ == "__main__":
    
    HTTPServer_GroupChat = HTTP_Server()
    HTTPServer_GroupChat.HTTP_Handler = GroupChatHandler
    HTTP_STATUS = HTTPServer_GroupChat.HTTP_STATUS_OK
    
    HTTPServer_GroupChat.start_http_server()
    
    while True:  # Keep the server running continuously
        client_connection, client_address = HTTPServer_GroupChat.server.accept()
        client = GroupChatHandler(client_connection, client_address, HTTPServer_GroupChat)
        
        clients.append(client)
        threading.Thread(target=client.handle).start() 
