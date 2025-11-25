import socket
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
SERVER_IP = '172.28.94.179'
SERVER_PORT = 5001
WEB_PORT = 5002

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_tcp!'
socketio = SocketIO(app, async_mode="threading")

tcp_socket = None
connected = False

# -----------------------------
# RUTAS FLASK
# -----------------------------
@app.route("/")
def index():
    return render_template("client.html", mode="TCP")

# -----------------------------
# LÓGICA TCP
# -----------------------------
def connect_tcp():
    global tcp_socket, connected
    while True:
        try:
            if not connected:
                socketio.emit("client_log", {"message": f"Intentando conectar a {SERVER_IP}:{SERVER_PORT}..."})
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.connect((SERVER_IP, SERVER_PORT))
                connected = True
                socketio.emit("client_log", {"message": "¡Conectado al servidor TCP!"})
                
                # Hilo para escuchar respuestas del servidor
                threading.Thread(target=receive_tcp, daemon=True).start()
            
            time.sleep(5) # Reintentar si se desconecta
        except Exception as e:
            socketio.emit("client_log", {"message": f"Error de conexión: {e}"})
            connected = False
            time.sleep(5)

def receive_tcp():
    global connected, tcp_socket
    try:
        while connected:
            data = tcp_socket.recv(4096)
            if not data:
                break
            msg = data.decode(errors='ignore')
            socketio.emit("server_response", {"message": f"Servidor: {msg}"})
    except Exception as e:
        socketio.emit("client_log", {"message": f"Error recibiendo datos: {e}"})
    finally:
        connected = False
        socketio.emit("client_log", {"message": "Desconectado del servidor."})
        if tcp_socket:
            tcp_socket.close()

# -----------------------------
# EVENTOS SOCKET.IO
# -----------------------------
@socketio.on("send_message")
def handle_send_message(data):
    global tcp_socket, connected
    msg = data.get("message")
    if connected and tcp_socket:
        try:
            tcp_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            socketio.emit("client_log", {"message": f"Error enviando: {e}"})
            connected = False
    else:
        socketio.emit("client_log", {"message": "No estás conectado al servidor."})

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    # Iniciar hilo de conexión TCP
    threading.Thread(target=connect_tcp, daemon=True).start()
    
    socketio.run(
        app,
        host="127.0.0.1",
        port=WEB_PORT,
        debug=False,
        use_reloader=False
    )
