from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import socket
import threading
import sys
import errno

#Definiowanie podstawowych danych do połączenia między klientem a serwerem
HOST = 'ring-s.hopto.org'
PORT = 2000

#Nawiązywanie połączenia między klientem a serwerem
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.setblocking(0)

#Funkcja otwierająca dialog wyboru pliku
def fileDialog():
    filedialog.askopenfilename(title = "Wybierz plik do przesłania")

#Funkcja czyszcząca główną ramkę programu    
def clearMainFrame():
    for widget in main_frame.winfo_children():
        widget.destroy()

#Funkcja przesyłająca do serwera dane rejestracji
def sendRegisterInfo(login_widget, password_widget, username_widget):
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
                
        info = "[REGISTER]" + login + password + username
        print(info)
        write(info)
        logIn()

#Interfejs rejestrowania użytkownika
def register():
    clearMainFrame()
    
    Label(main_frame, text = "Login", ).grid(column = 0, row = 0, sticky = "w")
    Label(main_frame, text = "Hasło").grid(column = 0, row = 1, sticky = "w")
    Label(main_frame, text = "Nazwa użytkownika").grid(column = 0, row = 2, sticky = "w")
    
    #Pola do wpisywania danych
    login = Entry(main_frame, width = 30)
    login.grid(column = 1, row = 0)
    password = Entry(main_frame, width = 30)
    password.grid(column = 1, row = 1)
    username = Entry(main_frame, width = 30)
    username.grid(column = 1, row = 2)
    
    #przycisk rejestracji
    Button(main_frame, text = "Zarejestruj", command = lambda: sendRegisterInfo(login, password, username)).grid(column = 1, row = 3, sticky = "swen")

#Główny interfejs aplikacji
def mainApp():
    clearMainFrame()
    
    #Ramka znajomych
    friends_frame = Frame(main_frame, width = 200).grid(column = 0, row = 0, rowspan = 2)
    
    #Widżet Text, w którym wyświetlane są wiadomości odebrane z serwera
    review_box = Text(main_frame)
    review_box.grid(column = 1, row = 0, sticky = "swen", columnspan = 3)
    review_box.configure(state='disabled')
    
    #Widżet Text, w którym użytkownik wpisuje wiadomość do wysłania
    message_box = Entry(main_frame)
    message_box.grid(column = 1, row = 1)
    
    #Przypisanie funkcji onEnterClick do klawisza enter
    app.bind('<Return>', lambda e: onEnterClick(message_box))
    
    #Przyciski
    Button(main_frame, text = "Wyślij", command = lambda: onEnterClick(message_box)).grid(column = 2, row = 1)
    Button(main_frame, text = "Wybierz plik...", command = fileDialog).grid(column = 3, row = 1)
    
    #Wątek odbierający wiadomości z serwera
    recv_thread = threading.Thread(target = lambda: receive(review_box))
    recv_thread.start()

#Interfejs logowania użytkownika
def logIn():
    clearMainFrame()
    
    Label(main_frame, text = "Login").grid(column = 0, row = 0, sticky = "w")
    Label(main_frame, text = "Hasło").grid(column = 0, row = 1, sticky = "w")
    
    #Pola do wpisywania informacji
    login = Entry(main_frame, width = 30).grid(column = 1, row = 0, columnspan = 2)
    password = Entry(main_frame, width = 30).grid(column = 1, row = 1, columnspan = 2)
    
    #Przyciski
    Button(main_frame, text = "Zaloguj", command = mainApp).grid(column = 1, row = 2, sticky = "w")
    Button(main_frame, text = "Zarejestruj", command = register).grid(column = 2, row = 2, sticky = "e")

#Funkcja wysyłająca wiadomość do serwera    
def write(message):
    try:
        client.send(message.encode())
    except:
        print("Failed to connect to the server.")
        client.close()

#Funkcja odbierająca informacje od serwera    
def receive(box):
    global running
    while running:
        try:
            message = client.recv(1024)
            box.configure(state='normal')
            box.insert(END, message.decode('utf-8'))
            box.configure(state='disabled')
        except Exception as e:
            if e.errno == errno.WSAEWOULDBLOCK:
                continue
            else:
                client.close()
                break

#Funkcja odpowiadająca za kliknięcie przycisku enter
def onEnterClick(box):
    write(box.get())
    box.delete(0, END)
    return 'break'

#Funkcja odpowiadająca kliknięciu przycisku zamknięcia okna Tkinter
def onClose():
    global running
    running = not running
    app.destroy()

#Stworzenie aplikacji tkinter
app = Tk()
app.title("Wiadomości")

#Główna ramka interfejsu użytkownika
main_frame = ttk.Frame(app, padding = 5)
main_frame.grid()

logIn()
global running
running = True

#Przypisanie funkcji onClose do przycisku zamykającego okno programu
app.protocol("WM_DELETE_WINDOW", onClose)

#Główna pętla programu
app.mainloop()