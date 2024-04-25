import socket
import threading

HOST = '192.168.1.16'
PORT = 2000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []
users = []

def reloadUsers():
    global users
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
    except:
        pass

def broadcast(message, sender, username, send_address = True):
    for client in clients:
        if client is not sender:
            if send_address:
                client.send(("<" + username + ">" + "   " + message).encode('utf-8'))
            else:
                client.send(message.encode('utf-8'))
        else:
            if send_address:
                client.send(f"<YOU>    {message}".encode('utf-8'))

def handle(client, address):
    username = ''
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
            
            elif message.startswith("[LOGIN]"):
                global users
                send_error = True
                message = message.replace("[LOGIN]", "")
                message = message.split()
                for user in users:
                    if message[0] == user["login"]:
                        if message[1] == user["password"]:
                            username = user["username"]
                            send_error = False
                            client.send("[OK]".encode("utf-8"))
                            break
                if send_error:
                    client.send("[ERROR]".encode("utf-8"))
            
            else:
                broadcast(message, client, username)
        except:
            if client in clients:
                clients.remove(client)
                client.close()
                broadcast("disconnected from the server.", client, username)
                print(username + " disconnected from the server.")
                break
        
def receive():
    while True:
        try:
            client, address = server.accept()
        except:
            break
            
        print(f"{str(address[0])} connected to the server.")
        clients.append(client)
        
        thread = threading.Thread(target = handle, args = (client, address))
        thread.start()
             
print("Server running.")
reloadUsers()
receive()