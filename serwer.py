from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import socket
import threading
import os
from time import sleep
import traceback
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

HOST = '192.168.1.16'
PORT = 2000
PACKET_SIZE = 4096
try:
    with open("server_config.txt", "r") as f:
        lines = f.readlines()

        HOST = lines[0].strip()
        PORT = int(lines[1].strip())
        PACKET_SIZE = int(lines[2].strip())
        print(f"Config loaded: HOST={HOST}, PORT={PORT}, PACKET_SIZE={PACKET_SIZE}")
except Exception as e:   
    print(f"Using default config: HOST={HOST}, PORT={PORT}, PACKET_SIZE={PACKET_SIZE}")

key = os.urandom(32)
iv = os.urandom(16)
print("Wygenerowano parę (klucz AES, wektor IV): ({}, {})".format(key, iv))
 
nobroad = []
    
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

def decryptMessage(ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    
    decryptor = cipher.decryptor()
    decrypted_padded_message = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_message = unpadder.update(decrypted_padded_message) + unpadder.finalize()
    
    return decrypted_message

def encryptMessage(message):
    message_bytes = message.encode('utf-8')
    
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_message = padder.update(message_bytes) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_message) + encryptor.finalize()
    
    return ciphertext

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
        
    def broadcast(self, message, sender, username, send_name = True):
        if send_name:
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time = "[" + time + "]"
            with open(self.directory + "/chat.txt", "a") as file:
                file.write(time + username + ": " + message + "\n")
                
            for client in self.users:
                if client not in nobroad:
                    client.send(encryptMessage("[MSG]" + time + username + ": " + message))
        else:
            for client in self.users:
                if client not in nobroad:
                    client.send(encryptMessage(message))

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
                        client.send(encryptMessage("[ROOM]" + name))
        except Exception as e:
            pass
    
    def loadRooms(self):
        dirs = os.listdir()
        for d in dirs:
            if not os.path.isfile(d) and not d.startswith(".") and not d == "pobrane":
                room = Room(d)
                self.rooms.append(room)
    
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
        
        while not client in self.logged_in:
            message = client.recv(PACKET_SIZE).decode("utf-8")
            
            if message.startswith("[REGISTER]"):
                allow = True
                print(message)
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
                    print("zarejestrowano użytkownika")
                else:
                    print("błąd przy rejestracji użytkownika")
            
            elif message.startswith("[LOGIN]"):
                send_error = True
                print(message)
                message = message.replace("[LOGIN]", "")
                message = message.split()
                for user in self.users:
                    if message[0] == user["login"]:
                        if message[1] == user["password"]:
                            username = user["username"]
                            userid = user["id"]
                            send_error = False
                            self.logged_in.append(client)
                            client.send(("[OK]{}<div>{}".format(key, iv)).encode("utf-8"))
                            print(f"client {username} logged in with id {userid}")
                            break
                if send_error:
                    client.send("[ERROR]".encode("utf-8"))
        
        while True:
            try:
                message = client.recv(PACKET_SIZE)
                message = decryptMessage(message)
                message = message.decode("utf-8")
                        
                if message.startswith("[ROOM]"):
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
                    try:
                        with open(filedir, "wb") as file:
                            while True:
                                data = client.recv(PACKET_SIZE)
                                data = (data)
                                
                                if data == b'END_FILE':
                                    break
                                
                                if data:
                                    file.write(data)
                                    client.send(b'[OK]')
                                    sleep(0.2)
                                    
                                else:
                                    break

                        if filename not in active_room.files:
                            sleep(0.2)
                            active_room.files.append(filename)
                            print("odebrano plik {} prawidłowo".format(filename))
                            active_room.broadcast(("[LIST]" + filename), client, username, False)
                        
                        active_room.broadcast(filename, client, username)
                        sleep(0.1)
                    
                    except Exception as e:
                        print(f"Wystąpił błąd podczas odbierania pliku: {e}")
                        
                    finally:
                        nobroad.remove(client)
                
                elif message.startswith("[LOAD]"):
                    nobroad.append(client)
                    for f in active_room.files:
                        sleep(0.2)
                        client.send(encryptMessage("[LIST]" + f))
                    for room in self.rooms:
                        sleep(0.2)
                        client.send(encryptMessage("[ROOM]" + room.name))
                        
                    try:
                        with open(active_room.name + "/" + "chat.txt", "r") as file:
                            for line in file:
                                if line != "\n":
                                    line = line.replace("\n", "")
                                    client.send(encryptMessage("[MSG]" + line))
                                    sleep(0.15)
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
                            client.send(encryptMessage("[FILE]" + filename))
                            sleep(0.1)
                    
                            data = " "
                            response = b'[OK]'
                            while data and response == b'[OK]':
                                try:
                                    data = file.read(PACKET_SIZE)
                                    if data == b'':
                                        break
                                    client.send(data)
                                    sleep(0.2)
                                    response = client.recv(PACKET_SIZE)
                                    sleep(0.2)
                                    if not response == b'[OK]':
                                        break
                                    #sleep(0.01)
                                except Exception as e:
                                    continue
                            
                        sleep(0.5)
                        client.send(b'END_FILE')
                
                    except Exception as e:
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
                if client in self.clients:
                    self.clients.remove(client)
                if client in self.logged_in:
                    self.logged_in.remove(client)
                if client in active_room.users:
                    active_room.users.remove(client)
                print(address[0] + " disconnected from the server.")
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