import threading
import queue

import os
import sys

Project_Folder = "Server-Framework"
project_root = os.path.abspath(__file__)
index = project_root.find(Project_Folder)
index_length_project = len(Project_Folder)
if index != -1:
    core_dir = project_root[:index+index_length_project+1]+"Core"
sys.path.append(core_dir)
        

from Settings import UDP_Server


server = None


def RecvData(sock,recvPackets):
    while True:
        data,addr = server.udp_server.recvfrom(1024)
        print(data,addr)
        recvPackets.put((data,addr))

def RunServer():
    clients = set()
    recvPackets = queue.Queue()


    threading.Thread(target=RecvData,args=(server.udp_server,recvPackets)).start()

    while True:
        while not recvPackets.empty():
            data,addr = recvPackets.get()
            print(addr)
            if addr not in clients:
                clients.add(addr)
                continue
            
            clients.add(addr)
            data = data.decode('utf-8')
            
            if data.endswith('qqq'):
                clients.remove(addr)
                continue
            
            print(str(addr)+data)
            for c in clients:
                if c!=addr:
                    server.udp_server.sendto(data.encode('utf-8'),c)



if __name__ == "__main__":
    server = UDP_Server()
    server.start_udp_server()
    RunServer()