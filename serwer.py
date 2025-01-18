import socket
import threading
import os
from time import sleep

HOST = '192.168.1.24'
PORT = 3000
PACKET_SIZE = 2048

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

path = ".\\files\\"
if not os.path.exists(path):
    os.makedirs(path)

class Room:
    def __init__(self, name):
        self.name = name
        self.users = []
        self.directory = ".\\" + self.name
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.files = os.listdir(directory + "\\files")
        print(self.files)

class Server:
    def __init__(self):
        self.clients = []
        self.logged_in = []
        self.users = []
        self.files = os.listdir(".\\files")
        
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

    def broadcast(self, message, sender, username):
        with open("chat.txt", "a") as file:
            file.write(username + ": " + message + "\n")
            
        for client in self.logged_in:
            client.send((username + ": " + message).encode('utf-8'))

    def handle(self, client, address):
        username = ''
        userid = ''
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
                                userid = user["id"]
                                send_error = False
                                self.logged_in.append(client)
                                client.send("[OK]".encode("utf-8"))
                                print(f"client {username} logged in with id {userid}")
                                break
                    if send_error:
                        client.send("[ERROR]".encode("utf-8"))
                
                elif message.startswith("[FILE]"):
                    filename = message.replace("[FILE]", "")
                    filedir = ".\\files\\" + filename
                    try:
                        with open(filedir, "wb") as file:
                            while True:
                                print("kurwa")
                                data = client.recv(PACKET_SIZE)
                                
                                if data == b'END_FILE':
                                    print(f"Otrzymano plik: {filename}")
                                    break
                                
                                if data:
                                    file.write(data)
                                    client.send(b'[OK]')
                                    sleep(0.05)
                                    print("Wysłano OK do klienta")
                                    
                                else:
                                    print("Brak danych od klienta")
                                    break

                        if filename not in self.files:
                            sleep(0.1)
                            self.files.append(filename)
                            for logged_client in self.logged_in:
                                logged_client.send(("[LIST]" + filename).encode('utf-8'))
                                print("Zaktualizowano listę plików")
                        
                        self.broadcast(filename, client, username)
                    
                    except Exception as e:
                        print(f"Wystąpił błąd podczas odbierania pliku: {e}")
                
                elif message.startswith("[LOAD]"):
                    message = message.replace("[LOAD]", "")
                    try:
                        with open("chat.txt", "r") as file:
                            for line in file:
                                if line != "\n":
                                    client.send(line.encode('utf-8'))
                        for f in self.files:
                            sleep(0.2)
                            client.send(("[LIST]" + f).encode('utf-8'))
                    except:
                        print("No file")
                        
                elif message.startswith("[FILEREQUEST]"):
                    try:
                        filename = message.replace("[FILEREQUEST]", "")
                        filedir = ".\\files\\" + filename
                        with open(filedir, "rb") as file:
                            client.send(("[FILE]" + filename).encode("utf-8"))
                            print("wyslano nazwe pliku")
                    
                            data = " "
                            response = b'[OK]'
                            while data and response == b'[OK]':
                                try:
                                    data = file.read(PACKET_SIZE)
                                    if data == b'':
                                        break
                                    client.send(data)
                                    sleep(0.05)
                                    print("sent data" + str(data))
                                    print("czekam na odpowiedz")
                                    response = client.recv(PACKET_SIZE)
                                    #sleep(0.02)
                                    print("Got response" + str(response))
                                    sleep(0.01)
                                except Exception as e:
                                    print(e)
                                    continue
                            
                        sleep(0.5)
                        client.send(b'END_FILE')
                        print("sent end")
                
                    except Exception as e:
                        print(e)
                        pass
                
                elif not message:
                    if client in self.clients:
                        self.clients.remove(client)
                        if client in self.logged_in:
                            self.logged_in.remove(client)
                        print(address[0] + " disconnected from the server.")
                        print("NOMESS")
                        client.close()
                    break
                    
                else:
                    self.broadcast(message, client, username)
            except Exception as e:
                if client in self.clients:
                    self.clients.remove(client)
                    if client in self.logged_in:
                        self.logged_in.remove(client)
                    print(address[0] + " disconnected from the server.")
                    print(e)
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