import socket
import threading

HOST = '192.168.1.24'
PORT = 2000
PACKET_SIZE = 2048

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

class Server:
    def __init__(self):
        self.clients = []
        self.logged_in = []
        self.users = []
        
        self.reloadUsers()
        self.receive()

    def reloadUsers(self):
        self.users = []
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
                    self.users.append(user)
        except:
            pass

    def broadcast(self, message, sender, username, send_address = True):
        for client in self.logged_in:
            if client is not sender:
                if send_address:
                    client.send(("<" + username + ">" + "   " + message).encode('utf-8'))
                else:
                    client.send(message.encode('utf-8'))
            else:
                if send_address:
                    client.send(f"<YOU>    {message}".encode('utf-8'))

    def handle(self, client, address):
        username = ''
        while True:
            try:
                message = client.recv(PACKET_SIZE).decode('utf-8')
                print(message)
                
                if message.startswith("[REGISTER]"):
                    allow = True
                    try:
                        with open("uid.txt", "r") as id_file:
                            last_id = int(id_file.readline())
                            last_id += 1
                    except:
                        last_id = 1
                    
                    message = message.replace("[REGISTER]", "")
                    register_info = message.split()
                    message = str(last_id) + " " + message + "\n"
                    
                    for u in self.users:
                        if register_info[0] == u["login"] or register_info[2] == u["username"]:
                            allow = False
                            break
                            
                    if allow:
                        with open("users.txt", "a") as users_file:
                            users_file.write(message)
                            
                        with open("uid.txt", "w") as id_file:
                            id_file.write(str(last_id))
                            
                        self.reloadUsers()
                
                elif message.startswith("[LOGIN]"):
                    send_error = True
                    message = message.replace("[LOGIN]", "")
                    message = message.split()
                    for user in self.users:
                        if message[0] == user["login"]:
                            if message[1] == user["password"]:
                                username = user["username"]
                                send_error = False
                                self.logged_in.append(client)
                                client.send("[OK]".encode("utf-8"))
                                break
                    if send_error:
                        client.send("[ERROR]".encode("utf-8"))
                
                elif message.startswith("[FILE]"):
                    filename = message.replace("[FILE]", "")
                    with open(filename, "wb") as image_file:
                        image_data = client.recv(PACKET_SIZE)

                        while image_data != b"END_FILE":
                            image_file.write(image_data)
                            image_data = client.recv(PACKET_SIZE)
                
                elif not message:
                    if client in self.clients:
                        self.clients.remove(client)
                        if client in self.logged_in:
                            self.logged_in.remove(client)
                        print(address[0] + " disconnected from the server.")
                        client.close()
                    break
                    
                else:
                    self.broadcast(message, client, username)
            except:
                if client in self.clients:
                    self.clients.remove(client)
                    if client in self.logged_in:
                        self.logged_in.remove(client)
                    print(address[0] + " disconnected from the server.")
                    client.close()
                break
            
    def receive(self):
        while True:
            try:
                client, address = server.accept()
            except:
                break
                
            print(f"{str(address[0])} connected to the server.")
            self.clients.append(client)
            
            thread = threading.Thread(target = self.handle, args = (client, address))
            thread.start()

if __name__ == "__main__":          
    print("Server running.")
    server_app = Server()