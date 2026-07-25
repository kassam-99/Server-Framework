import asyncio
import time
import websockets
from datetime import datetime
import os
import sys

Project_Folder = "Server-Framework"
project_root = os.path.abspath(__file__)
index = project_root.find(Project_Folder)
index_length_project = len(Project_Folder)
if index != -1:
    core_dir = project_root[:index+index_length_project+1]+"Core"
sys.path.append(core_dir)
        
from Settings import Websockets_Server


clients = set()
clients_dict = {}

async def handle_client(websocket, path):
    try:
        clients.add(websocket)
        client_id = len(clients)
        clients_dict[websocket] = client_id
        print(f"New client connected. Total clients: {len(clients)}")

        while True:
            message = await websocket.recv()
            if not message:
                break

            print(f"Received message from user {client_id}: {message}")

            # Broadcast the message to all clients except the sender (websocket)
            for client in clients:
                if client != websocket:
                    print(f"Broadcasting message from user {client_id} to user {clients_dict[client]}")
                    await client.send(f"User {client_id} says: {message}")

    except websockets.exceptions.ConnectionClosed:
        print(f"User {client_id} disconnected")
    finally:
        clients.remove(websocket)
        del clients_dict[websocket]
        print(f"User {client_id} disconnected. Total clients: {len(clients)}")



async def send_data_to_clients():
    while True:
        message = f"Server sending data: {datetime.datetime.now()}"
        for websocket in clients:
            await websocket.send(message)



if __name__ == "__main__":
    WS_server = Websockets_Server()
    WS_server.Websocket_Handler = handle_client
    WS_server.start_websockets_server()


