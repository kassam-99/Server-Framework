import requests

server_address = "http://localhost:8000"  # Replace with the server's actual address and port

def send_message(message):
    data = {"message": message}
    response = requests.post(server_address, data=data)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message:", response.text)

def receive_message():
    response = requests.get(server_address)
    if response.status_code == 200:
        message = response.text
        print("Received message:", message)
    else:
        print("Failed to receive message:", response.text)

if __name__ == "__main__":
    while True:
        command = input("Enter 'send' to send a message, 'receive' to receive a message, or 'quit' to exit: ")
        if command == "send":
            message = input("Enter your message: ")
            send_message(message)
        elif command == "receive":
            receive_message()
        elif command == "quit":
            break
        else:
            print("Invalid command.")
