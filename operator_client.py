import socket, tkinter as tk

HOST = "18.222.158.163"
PORT = 8080

def actualizar():
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(b"GET_STATUS")
    data = s.recv(4096).decode()
    s.close()

    text.delete(1.0, tk.END)
    text.insert(tk.END, data)

root = tk.Tk()
root.title("Operador IoT")

btn = tk.Button(root, text="Actualizar", command=actualizar)
btn.pack()

text = tk.Text(root)
text.pack()

root.mainloop()