from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.tix import *
from time import sleep
import hashlib
import socket
import threading
import sys
import os
import errno

#Definiowanie podstawowych danych do połączenia między klientem a serwerem
HOST = 'pawelksi.mywire.org'
PORT = 2000
PACKET_SIZE = 4096

#Nawiązywanie połączenia między klientem a serwerem
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

path = ".\\pobrane\\"
if not os.path.exists(path):
    os.makedirs(path)

class Client():
    def __init__(self):
        self.user = ""
        self.running = True
        self.block = False
        self.load = False
        self.filenames = []
        self.roomnames = []
        
        self.key = ''
        self.iv = ''
        
        #Tworzenie aplikacji tkinter
        self.app = Tk()
        self.app.title("Wiadomości")
        self.app.resizable(False, False)

        #Główna ramka interfejsu użytkownika
        self.main_frame = ttk.Frame(self.app, padding = 5)
        self.main_frame.grid()

        #Przypisanie funkcji onClose do przycisku zamykającego okno programu
        self.app.protocol("WM_DELETE_WINDOW", self.onClose)
        
        self.logIn()
        self.app.mainloop()

    #Funkcja otwierająca dialog wyboru pliku
    def fileDialog(self, file_combo, room_combo, text):
        try:
            self.status_label.config(text = "Status pobierania: wysyłanie")
            client.setblocking(1)
            filepath = filedialog.askopenfilename(title = "Wybierz plik do przesłania")
            filename = filepath.split("/")
            filename = filename[len(filename) - 1]
            
            with open(filepath, "rb") as file:
                self.write("[FILE]" + filename)
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
                        print("sent data" + str(data))
                        response = client.recv(PACKET_SIZE)
                        sleep(0.2)
                        print("Got response")
                        #sleep(0.01)
                    except:
                        continue
            
            sleep(0.5)
            client.send(b'END_FILE')
            self.status_label.config(text = "Status pobierania: oczekiwanie")
            self.clearData(file_combo, room_combo, text)
            self.write("[LOAD]")
            print("wtf")
                
        except Exception as e:
            pass

    #Funkcja czyszcząca główną ramkę programu    
    def clearMainFrame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    #Funkcja przesyłająca do serwera dane rejestracji
    def sendRegisterInfo(self, login_widget, password_widget, username_widget):
        #Lista znaków dozwolonych przy rejestracji
        allowed_chars = []
        for i in range(65, 91):
            allowed_chars.append(chr(i))
        for i in range(97, 123):
            allowed_chars.append(chr(i))
        allowed_chars.extend(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "!", "@", "#", "$", "%", "^", "&", "*", "_", "-"])
        
        login = login_widget.get()
        password = password_widget.get()
        username = username_widget.get()
        
        if login != '' and password != '' and username != '':
            if len(login) < 5 or len(login) > 16:
                login_widget.delete(0, END)
                return
                    
            if len(password) < 5 or len(password) > 16:
                password_widget.delete(0, END)
                return
                    
            if len(username) < 5 or len(username) > 16:
                username_widget.delete(0, END)
                return
                    
            for char in login:
                if char not in allowed_chars:
                    login_widget.delete(0, END)
                    return
                    
            for char in password:
                if char not in allowed_chars:
                    password_widget.delete(0, END)
                    return
                    
            for char in username:
                if char not in allowed_chars:
                    username_widget.delete(0, END)
                    return
                    
            
            salt = "salt"
            dataBase_password = password+salt
            hashed = hashlib.md5(dataBase_password.encode())
             
            password = hashed.hexdigest()

            
            info = "[REGISTER]" + login + " " + password + " " + username
            client.send(info.encode("utf-8"))
            
            self.logIn()

    #Interfejs rejestrowania użytkownika
    def register(self):
        self.clearMainFrame()
        
        Label(self.main_frame, text = "Login", ).grid(column = 0, row = 0, sticky = "w")
        Label(self.main_frame, text = "Hasło").grid(column = 0, row = 1, sticky = "w")
        Label(self.main_frame, text = "Nazwa użytkownika").grid(column = 0, row = 2, sticky = "w")
        
        tooltip = Balloon(self.main_frame)
        
        #Pola do wpisywania danych
        login = Entry(self.main_frame, width = 30)
        login.grid(column = 1, row = 0)
        password = Entry(self.main_frame, width = 30)
        password.grid(column = 1, row = 1)
        username = Entry(self.main_frame, width = 30)
        username.grid(column = 1, row = 2)
        
        #przycisk rejestracji
        Button(self.main_frame, text = "Zarejestruj", command = lambda: self.sendRegisterInfo(login, password, username)).grid(column = 1, row = 3, sticky = "swen")
        Button(self.main_frame, text = "Logowanie", command = lambda: self.logIn()).grid(column = 0, row = 3, sticky = "swen")
        
        tooltip.bind_widget(login, balloonmsg="Tutaj wpisz login.\nLogin powinien zawierać od 5 do 16 znaków.\nDozwolone znaki to a-z, A-Z, 0-9 oraz znaki ze zbioru (!, @, #, $, %, ^, &, *, _ , -)")
        tooltip.bind_widget(password, balloonmsg="Tutaj wpisz hasło.\nHasło powinno zawierać od 5 do 16 znaków.\nDozwolone znaki to a-z, A-Z, 0-9 oraz znaki ze zbioru (!, @, #, $, %, ^, &, *, _ , -)")
        tooltip.bind_widget(username, balloonmsg="Tutaj wpisz wyświetlaną nazwę użytkownika.\nNazwa użytkownika powinna zawierać od 5 do 16 znaków.\nDozwolone znaki to a-z, A-Z, 0-9 oraz znaki ze zbioru (!, @, #, $, %, ^, &, *, _ , -)")

    #Główny interfejs aplikacji
    def mainApp(self):
        self.clearMainFrame()
        self.write("[LOAD]")
        
        #Ramka znajomych
        friends_frame = Frame(self.main_frame, width = 200)
        friends_frame.grid(column = 0, row = 0, sticky = "n")
        text_frame = Frame(self.main_frame)
        text_frame.grid(column = 1, row = 0)
        
        #Widżet Text, w którym wyświetlane są wiadomości odebrane z serwera
        review_box = Text(text_frame)
        review_box.grid(column = 1, row = 0, sticky = "swen", columnspan = 3)
        review_box.configure(state='disabled')
        
        scrollbar = ttk.Scrollbar(text_frame, orient = 'vertical', command = review_box.yview)
        scrollbar.grid(row = 0, column = 3, sticky = "nse")
        review_box['yscrollcommand'] = scrollbar.set
        
        self.status_label = Label(friends_frame, text = "Status pobierania: oczekiwanie")
        self.status_label.grid(row = 0)
        
        file_combo_box = ttk.Combobox(friends_frame)
        file_combo_box.grid(row = 1, sticky = "we")
        file_combo_box.configure(state = "readonly")
        
        room_combo_box = ttk.Combobox(friends_frame)
        room_combo_box.grid(row = 6, sticky = "swe")
        room_combo_box.configure(state = "readonly")
        
        create_room_entry = Entry(friends_frame)
        create_room_entry.grid(row = 4, sticky = "swe")
        
        #Widżet Text, w którym użytkownik wpisuje wiadomość do wysłania
        message_box = Entry(text_frame, width = 110)
        message_box.grid(column = 1, row = 1, sticky = "we")
        
        #Przypisanie funkcji onEnterClick do klawisza enter
        self.app.bind('<Return>', lambda e: self.onEnterClick(message_box))
        
        #Przyciski
        Button(text_frame, text = "Wyślij", command = lambda: self.onEnterClick(message_box)).grid(column = 2, row = 1, sticky = "e")
        Button(text_frame, text = "Wyślij plik...", command = lambda: self.fileDialog(file_combo_box, room_combo_box, review_box)).grid(column = 3, row = 1, sticky = "e")
        Button(friends_frame, text = "Pobierz plik", command = lambda: self.downloadFiles(file_combo_box.get())).grid(row = 2, pady = (0, 200))
        Button(friends_frame, text = "Utwórz pokój", command = lambda: self.createRoom(create_room_entry.get())).grid(row = 5, sticky = "s", pady = (0, 30))
        Button(friends_frame, text = "Zmień pokój", command = lambda: self.changeRoom(room_combo_box.get(), file_combo_box, room_combo_box, review_box)).grid(row = 7, sticky = "s", pady = (0, 30))
        #Button(friends_frame, text = "Nowa", command = self.newConversation).grid(row = 1)
        
        #Wątek odbierający wiadomości z serwera
        recv_thread = threading.Thread(target = lambda: self.receive(review_box, file_combo_box, room_combo_box, message_box))
        recv_thread.start()
    
    def changeRoom(self, name, file_combo, room_combo, text):
        if name:
            self.clearData(file_combo, room_combo, text)
            self.write("[ROOMCHANGE]" + name)
            sleep(0.1)
            self.write("[LOAD]")
            
    def clearData(self, file_combo, room_combo, text):
        file_combo.configure(values = [])
        file_combo.delete(0, END)
        room_combo.configure(values = [])
        self.filenames = []
        self.roomnames = []
        text.configure(state='normal')
        text.delete(1.0, END)
        text.configure(state='disabled')
    
    def createRoom(self, name):
        if name:
            self.write("[ROOM]" + name)
            print("[ROOM]" + name)
    
    def downloadFiles(self, filename):
        if filename:
            self.write("[FILEREQUEST]" + filename)
    
    def newConversation(self):
        pop = Toplevel(self.app)
        pop.title("Nowa konwersacja")
        pop.resizable(False, False)
        pop.grab_set()
        Label(pop, text = "Wpisz nazwę użytkownika: ").grid(column = 0, row = 0)
        user_entry = Entry(pop, width = 30)
        user_entry.grid(column = 1, row = 0)
        Button(pop, text = "Zatwierdź", command = lambda: self.requestNewConversation(user_entry.get())).grid(columnspan = 2, row = 1)
        
    def sendLogInInfo(self, login_widget, password_widget):
        login = login_widget.get()
        password = password_widget.get()
        
        if login != "" and password != "":
            salt = "salt"
            dataBase_password = password+salt
            hashed = hashlib.md5(dataBase_password.encode())
             
            password = hashed.hexdigest()
            info = "[LOGIN]" + login + " " + password
            
            client.send(info.encode("utf-8"))
            response = client.recv(PACKET_SIZE).decode("utf-8")
            
            print(response)
        
            if response.startswith("[OK]"):
                response = response.replace("[OK]", "")
                response = response.split("<div>")
                self.key = eval(response[0])
                self.iv = eval(response[1])
                print(self.key)
                print(self.iv)
                self.mainApp()
            else:
                return
        

    #Interfejs logowania użytkownika
    def logIn(self):
        self.clearMainFrame()
        
        Label(self.main_frame, text = "Login").grid(column = 0, row = 0, sticky = "w")
        Label(self.main_frame, text = "Hasło").grid(column = 0, row = 1, sticky = "w")
        
        #Pola do wpisywania informacji
        login = Entry(self.main_frame, width = 30)
        login.grid(column = 1, row = 0, columnspan = 2)
        password = Entry(self.main_frame, width = 30)
        password.grid(column = 1, row = 1, columnspan = 2)
        
        #Przyciski
        Button(self.main_frame, text = "Zaloguj", command = lambda: self.sendLogInInfo(login, password)).grid(column = 1, row = 2, sticky = "swen")
        Button(self.main_frame, text = "Rejestracja", command = self.register).grid(column = 2, row = 2, sticky = "swen")

    def decryptMessage(self, ciphertext):
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_message = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_message = unpadder.update(decrypted_padded_message) + unpadder.finalize()
        
        return decrypted_message
    
    def encryptMessage(self, message):
        message_bytes = message.encode('utf-8')
                
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_message = padder.update(message_bytes) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_message) + encryptor.finalize()
        
        return ciphertext
    
    #Funkcja wysyłająca wiadomość do serwera    
    def write(self, message = ""):
        if not self.block:
            try:
                message = self.encryptMessage(message)
                client.send(message)
            except Exception as e:
                print(e)
                print("Failed to connect to the server.")
                client.close()

    #Funkcja odbierająca informacje od serwera    
    def receive(self, box, file_combo, room_combo, entry):
        while self.running:
            try:
                client.setblocking(0)
                if self.load:
                    self.load = False
                    self.clearData(file_combo, room_combo, box)
                    self.write("[LOAD]")
                    
                message = client.recv(PACKET_SIZE)
                sleep(0.1)
                print(message)

                if not message:
                    continue

                try:
                    message = self.decryptMessage(message)
                    message = message.decode('utf-8')
                except ValueError as e:
                    print(f"Error while decrypting message: {e}")
                    continue  # Ignoruj wiadomości, które nie mogą zostać odszyfrowane

                print(message)

                if message.startswith("[OK]") or message.startswith("[ERROR]"):
                    continue
                        
                elif message.startswith("[LIST]"):
                    client.setblocking(1)
                    message = message.replace("[LIST]", "")
                    self.filenames.append(message)
                    file_combo.configure(values = self.filenames)
                    
                elif message.startswith("[ROOM]"):
                    client.setblocking(1)
                    message = message.replace("[ROOM]", "")
                    self.roomnames.append(message)
                    room_combo.configure(values = self.roomnames)
                        
                elif message.startswith("[FILE]"):
                    self.status_label.config(text = "Status pobierania: pobieranie")
                    filename = message.replace("[FILE]", "")
                    filedir = ".\\pobrane\\" + filename
                    try:
                        with open(filedir, "wb") as file:
                            client.setblocking(1)
                            self.block = True
                            while True:
                                print("czekam na dane")
                                sleep(0.2)
                                data = client.recv(PACKET_SIZE)
                                print(data)
                                if data == b'':
                                        continue
                            
                                elif data == b'END_FILE':
                                    print("otrzymano koniec")                                
                                    print(f"Otrzymano plik: {filename}")
                                    self.status_label.config(text = "Status pobierania: oczekiwanie")
                                    self.load = True
                                    break
                                    
                                elif data:
                                    print("otrzymano {}".format(data))
                                    file.write(data)
                                    sleep(0.2)
                                    client.send(b'[OK]')
                                    
                                else:
                                    print("Brak danych od klienta")
                                    break
                                    
                        self.block = False
                    
                    except Exception as e:
                        print(f"Wystąpił błąd podczas odbierania pliku: {e}")
                    
                elif message.startswith("[MSG]"):
                    message = message.replace("[MSG]", "")
                    box.configure(state='normal')
                    box.insert(END, message)
                    box.insert(END, "\n")
                    box.yview("end")
                    box.configure(state='disabled')
                    
            except Exception as e:
                if e.errno == errno.WSAEWOULDBLOCK:
                    continue
                else:
                    client.close()
                    print(e)
                    break
                    
    #Funkcja odpowiadająca za kliknięcie przycisku enter
    def onEnterClick(self, box):
        self.write(box.get())
        box.delete(0, END)
        return 'break'

    #Funkcja odpowiadająca kliknięciu przycisku zamknięcia okna Tkinter
    def onClose(self):
        self.running = False
        self.app.destroy()

if __name__ == "__main__":
    client_app = Client()