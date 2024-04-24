import socket
import threading

HOST = '192.168.1.16'
PORT = 2000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []

def reloadUsers():
    users = []
    
    try:
        with open("users.txt", "r") as users_file:
            for line in users_file.readlines():
                user = {}
                line = line.rstrip("\n")
                line = line.split()
                user["id"] = line[0]
                user["login"] = line[1]
                user["password"] = line[2]
                user["username"] = line[3]
                users.append(user)
            
            print(users)
    except:
        pass

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
                try:
                    with open("uid.txt", "r") as id_file:
                        last_id = int(id_file.readline())
                        last_id += 1
                except:
                    last_id = 1
                    
                with open("uid.txt", "w") as id_file:
                    id_file.write(str(last_id))
                
                message = message.replace("[REGISTER]", "")
                message = str(last_id) + " " + message + "\n"
                
                with open("users.txt", "a") as users_file:
                    users_file.write(message)
                    
                reloadUsers()
                
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
reloadUsers()
receive()