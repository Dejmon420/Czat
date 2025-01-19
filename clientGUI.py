from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from time import sleep
import socket
import threading
import sys
import os
import errno

#Definiowanie podstawowych danych do połączenia między klientem a serwerem
HOST = '83.6.73.77'
PORT = 3000
PACKET_SIZE = 2048

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
        self.filenames = []
        
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
    def fileDialog(self):
        try:
            self.status_label.config(text = "Status: wysyłanie")
            client.setblocking(1)
            filepath = filedialog.askopenfilename(title = "Wybierz plik do przesłania")
            filename = filepath.split("/")
            filename = filename[len(filename) - 1]
            
            with open(filepath, "rb") as file:
                self.write("[FILE]" + filename)
                
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
                        response = client.recv(PACKET_SIZE)
                        sleep(0.1)
                        print("Got response")
                        #sleep(0.01)
                    except:
                        continue
            
            sleep(0.5)
            client.send(b'END_FILE')
            self.status_label.config(text = "Status: oczekiwanie")
                
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
                    
            info = "[REGISTER]" + login + " " + password + " " + username
            self.write(info)
            
            self.logIn()

    #Interfejs rejestrowania użytkownika
    def register(self):
        self.clearMainFrame()
        
        Label(self.main_frame, text = "Login", ).grid(column = 0, row = 0, sticky = "w")
        Label(self.main_frame, text = "Hasło").grid(column = 0, row = 1, sticky = "w")
        Label(self.main_frame, text = "Nazwa użytkownika").grid(column = 0, row = 2, sticky = "w")
        
        #Pola do wpisywania danych
        login = Entry(self.main_frame, width = 30)
        login.grid(column = 1, row = 0)
        password = Entry(self.main_frame, width = 30)
        password.grid(column = 1, row = 1)
        username = Entry(self.main_frame, width = 30)
        username.grid(column = 1, row = 2)
        
        #przycisk rejestracji
        Button(self.main_frame, text = "Zarejestruj", command = lambda: self.sendRegisterInfo(login, password, username)).grid(column = 1, row = 3, sticky = "swen")

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
        
        self.status_label = Label(friends_frame, text = "Status: oczekiwanie")
        self.status_label.grid(row = 0)
        
        combo_box = ttk.Combobox(friends_frame)
        combo_box.grid(row = 1)
        
        #Widżet Text, w którym użytkownik wpisuje wiadomość do wysłania
        message_box = Entry(text_frame, width = 110)
        message_box.grid(column = 1, row = 1, sticky = "we")
        
        #Przypisanie funkcji onEnterClick do klawisza enter
        self.app.bind('<Return>', lambda e: self.onEnterClick(message_box))
        
        #Przyciski
        Button(text_frame, text = "Wyślij", command = lambda: self.onEnterClick(message_box)).grid(column = 2, row = 1, sticky = "e")
        Button(text_frame, text = "Wyślij plik...", command = self.fileDialog).grid(column = 3, row = 1, sticky = "e")
        Button(friends_frame, text = "Pobierz plik", command = lambda: self.downloadFiles(combo_box.get())).grid(row = 2)
        #Button(friends_frame, text = "Nowa", command = self.newConversation).grid(row = 1)
        
        #Wątek odbierający wiadomości z serwera
        recv_thread = threading.Thread(target = lambda: self.receive(review_box, combo_box))
        recv_thread.start()
    
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
            info = "[LOGIN]" + login + " " + password
            self.write(info)
        
            response = client.recv(PACKET_SIZE).decode("utf-8")
        
            if response == "[OK]":
                self.user = response.replace("[OK]", "")
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
        Button(self.main_frame, text = "Zaloguj", command = lambda: self.sendLogInInfo(login, password)).grid(column = 1, row = 2, sticky = "w")
        Button(self.main_frame, text = "Zarejestruj", command = self.register).grid(column = 2, row = 2, sticky = "e")

    #Funkcja wysyłająca wiadomość do serwera    
    def write(self, message = ""):
        try:
            client.send(message.encode('utf-8'))
        except:
            print("Failed to connect to the server.")
            client.close()

    #Funkcja odbierająca informacje od serwera    
    def receive(self, box, combo):
        while self.running:
            try:
                client.setblocking(0)
                message = client.recv(PACKET_SIZE).decode('utf-8')
                print(message)

                if message.startswith("[OK]") or message.startswith("[ERROR]"):
                    continue
                        
                elif message.startswith("[LIST]"):
                    client.setblocking(1)
                    message = message.replace("[LIST]", "")
                    self.filenames.append(message)
                    combo.configure(values = self.filenames, state = "readonly")
                        
                elif message.startswith("[FILE]"):
                    self.status_label.config(text = "Status: pobieranie")
                    filename = message.replace("[FILE]", "")
                    filedir = ".\\pobrane\\" + filename
                    try:
                        with open(filedir, "wb") as file:
                            client.setblocking(1)
                            while True:
                                data = client.recv(PACKET_SIZE)
                                
                                if data == b'END_FILE':
                                    print(f"Otrzymano plik: {filename}")
                                    self.status_label.config(text = "Status: oczekiwanie")
                                    break
                                
                                if data:
                                    file.write(data)
                                    client.send(b'[OK]')
                                    sleep(0.1)
                                    print("Wysłano OK do klienta")
                                    
                                else:
                                    print("Brak danych od klienta")
                                    break
                    
                    except Exception as e:
                        print(f"Wystąpił błąd podczas odbierania pliku: {e}")
                    
                elif message:
                    box.configure(state='normal')
                    box.insert(END, message)
                    box.insert(END, "\n")
                    box.yview("end")
                    box.configure(state='disabled')
                    
                else:
                    client.disconnect()
                    break
                    
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