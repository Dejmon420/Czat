import socket
import threading

HOST = '192.168.1.16'
PORT = 2000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []

def broadcast(message, sender, address, send_address=True):
    for client in clients:
        if client is not sender:
            if send_address:
                client.send(f"<{str(address[0])}>    {message}".encode('utf-8'))
            else:
                client.send(message.encode('utf-8'))
        else:
            if send_address:
                client.send(f"<YOU>    {message}".encode('utf-8'))

def handle(client, address):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith("[REGISTER]"):
                reg = open("users.txt", "a")
                uid = open("uid.txt", "w")
                last_id = int(uid.read())
                print(last_id)  
                reg.writelines(message)
                reg.close()
                uid.close()
                
            else:
                broadcast(message, client, address)
        except:
            if client in clients:
                clients.remove(client)
                client.close()
                broadcast(f"{address[0]} disconnected from the server.\n", client, address, False)
                print(f"{address[0]} disconnected from the server.")
        
def receive():
    while True:
        try:
            client, address = server.accept()
        except:
            break
            
        print(f"{str(address[0])} connected to the server.")
        clients.append(client)
        
        broadcast(f"{str(address[0])} connected to the server.\n", client, address, False)
        client.send(f"Connected to {str(HOST)}\n".encode('utf-8'))
        
        thread = threading.Thread(target=handle, args=(client, address))
        thread.start()
             
print("Server running.")
receive()