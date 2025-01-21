import socket
import threading
import os
from time import sleep
import traceback
from datetime import datetime

HOST = '192.168.1.16'
PORT = 2000
PACKET_SIZE = 4096
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    with open("server_config.txt", "r") as f:
        lines = f.readlines()

        HOST = lines[0].strip()
        PORT = int(lines[1].strip())
        PACKET_SIZE = int(lines[2].strip())
        print(f"Config loaded: HOST={HOST}, PORT={PORT}, PACKET_SIZE={PACKET_SIZE}")
except Exception as e:   
    print(f"Using default config: HOST={HOST}, PORT={PORT}, PACKET_SIZE={PACKET_SIZE}")
 
nobroad = []
    
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

class Room:
    def __init__(self, name):
        self.name = name
        self.users = []
        self.directory = self.name
        
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            
        if not os.path.exists(self.directory + "/files"):
            os.makedirs(self.directory + "/files")
            
        self.files = os.listdir(self.directory + "/files")
        print(self.files)
        print("created room {}".format(name))
        
    def broadcast(self, message, sender, username, send_name = True):
        print(self.users)
        if send_name:
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time = "[" + time + "]"
            with open(self.directory + "/chat.txt", "a") as file:
                file.write(time + username + ": " + message + "\n")
                
            for client in self.users:
                if client not in nobroad:
                    client.send(("[MSG]" + time + username + ": " + message).encode('utf-8'))
        else:
            for client in self.users:
                if client not in nobroad:
                    client.send(message.encode('utf-8'))

class Server:
    def __init__(self):
        self.clients = []
        self.logged_in = []
        self.users = []
        self.rooms = []
        
        self.reloadUsers()
        self.loadRooms()
        self.receive()
    
    def createRoom(self, name):
        try:
            create = True
            for r in self.rooms:
                if r.name == name or name == "pobrane":
                    create = False
            if create:
                room = Room(name)
                self.rooms.append(room)
                with open(room.directory + "/chat.txt", "a") as f:
                    f.write("<{}> utworzony [{}]\n".format(room.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                for client in self.logged_in:
                    if client not in nobroad:
                        client.send(("[ROOM]" + name).encode("utf-8"))
                print(self.rooms)
        except Exception as e:
            print(e)
    
    def loadRooms(self):
        dirs = os.listdir()
        print(dirs)
        for d in dirs:
            print(d)
            if not os.path.isfile(d) and not d.startswith(".") and not d == "pobrane":
                room = Room(d)
                self.rooms.append(room)
                print("Dodano pokoj")
    
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

    def handle(self, client, address):
        username = ''
        userid = ''
        active_room = self.rooms[0]
        active_room.users.append(client)
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
                    print("logowanie")
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
                        print("error")
                        
                elif message.startswith("[ROOM]"):
                    message = message.replace("[ROOM]", "")
                    self.createRoom(message)
                                               
                elif message.startswith("[ROOMCHANGE]"):
                    message = message.replace("[ROOMCHANGE]", "")
                    for room in self.rooms:
                        if room.name == message:
                            active_room.users.remove(client)
                            active_room = room
                            active_room.users.append(client)
                            
                elif message.startswith("[FILE]"):
                    filename = message.replace("[FILE]", "")
                    filedir = active_room.name + "/files/" + filename
                    nobroad.append(client)
                    print(filedir)
                    try:
                        with open(filedir, "wb") as file:
                            while True:
                                data = client.recv(PACKET_SIZE)
                                
                                if data == b'END_FILE':
                                    break
                                
                                if data:
                                    file.write(data)
                                    client.send(b'[OK]')
                                    sleep(0.1)
                                    
                                else:
                                    break

                        if filename not in active_room.files:
                            sleep(0.2)
                            active_room.files.append(filename)
                            active_room.broadcast(("[LIST]" + filename), client, username, False)
                        
                        active_room.broadcast(filename, client, username)
                        sleep(0.1)
                    
                    except Exception as e:
                        print(f"Wystąpił błąd podczas odbierania pliku: {e}")
                        
                    finally:
                        nobroad.remove(client)
                
                elif message.startswith("[LOAD]"):
                    nobroad.append(client)
                    message = message.replace("[LOAD]", "")
                    for f in active_room.files:
                        sleep(0.2)
                        client.send(("[LIST]" + f).encode('utf-8'))
                    for room in self.rooms:
                        sleep(0.2)
                        client.send(("[ROOM]" + room.name).encode('utf-8'))
                        
                    try:
                        with open(active_room.name + "/" + "chat.txt", "r") as file:
                            for line in file:
                                if line != "\n":
                                    line = line.replace("\n", "")
                                    client.send(("[MSG]" + line).encode('utf-8'))
                                    sleep(0.2)
                    except:
                        continue
                        
                    finally:
                        nobroad.remove(client)
                        
                elif message.startswith("[FILEREQUEST]"):
                    nobroad.append(client)
                    try:
                        filename = message.replace("[FILEREQUEST]", "")
                        filedir = active_room.name + "/files/" + filename
                        with open(filedir, "rb") as file:
                            client.send(("[FILE]" + filename).encode("utf-8"))
                            sleep(0.1)
                    
                            data = " "
                            response = b'[OK]'
                            while data and response == b'[OK]':
                                try:
                                    data = file.read(PACKET_SIZE)
                                    if data == b'':
                                        break
                                    client.send(data)
                                    sleep(0.1)
                                    print("sent data" + str(data))
                                    print("czekam na odpowiedz")
                                    response = client.recv(PACKET_SIZE)
                                    sleep(0.1)
                                    print("Got response" + str(response))
                                    if not response == b'[OK]':
                                        break
                                    #sleep(0.01)
                                except Exception as e:
                                    print(e)
                                    continue
                            
                        sleep(0.5)
                        client.send(b'END_FILE')
                        sleep(0.1)
                        print("wyslano koniec")
                
                    except Exception as e:
                        print(e)
                        pass
                        
                    finally:
                        nobroad.remove(client)
                
                elif not message:
                    if client in self.clients:
                        self.clients.remove(client)
                    if client in self.logged_in:
                        self.logged_in.remove(client)
                    if client in active_room.users:
                        active_room.users.remove(client)
                    print(address[0] + " disconnected from the server.")
                    client.close()
                    break
                    
                else:
                    active_room.broadcast(message, client, username)
            except Exception as e:
                print("co")
                if client in self.clients:
                    self.clients.remove(client)
                if client in self.logged_in:
                    self.logged_in.remove(client)
                if client in active_room.users:
                    active_room.users.remove(client)
                print(address[0] + " disconnected from the server.")
                print(e)
                print(traceback.format_exc())
                client.close()
                break
            
    def receive(self):
        self.createRoom("global")
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