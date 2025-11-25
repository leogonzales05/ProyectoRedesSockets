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
should_reconnect = True

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
    global tcp_socket, connected, should_reconnect
    while True:
        if not should_reconnect:
            time.sleep(1)
            continue
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
            # Si el socket ya fue puesto a None por otro hilo → salir
            if tcp_socket is None:
                break
            try:
                data = tcp_socket.recv(4096)
            except OSError:
                # Evita WinError 10038 cuando el socket ya no existe
                break
            if not data:
                break
            msg = data.decode(errors='ignore')
            socketio.emit("server_response", {"message": f"Servidor: {msg}"})
    finally:
        connected = False
        socketio.emit("client_log", {"message": "Desconectado del servidor."})
        if tcp_socket:
            try:
                tcp_socket.close()
            except:
                pass
            tcp_socket = None

# -----------------------------
# EVENTOS SOCKET.IO
# -----------------------------
@socketio.on("send_message")
def handle_send_message(data):
    global tcp_socket, connected, should_reconnect
    msg = data.get("message")

    if msg and msg.strip().lower() == "salir":
        should_reconnect = False
        if connected and tcp_socket:
            try:
                # --- Cierre limpio TCP ---
                try:
                    tcp_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                tcp_socket.close()
                socketio.emit("client_log", {"message": "Conexión cerrada voluntariamente."})
            except Exception as e:
                socketio.emit("client_log", {"message": f"Error cerrando: {e}"})
            finally:
                connected = False
                tcp_socket = None
        else:
            socketio.emit("client_log", {"message": "Ya estabas desconectado."})
        return

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
