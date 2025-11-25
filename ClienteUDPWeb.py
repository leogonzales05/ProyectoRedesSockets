import socket
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
SERVER_IP = '172.28.94.179'
SERVER_PORT = 5001
WEB_PORT = 5003

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_udp!'
socketio = SocketIO(app, async_mode="threading")

udp_socket = None

# -----------------------------
# RUTAS FLASK
# -----------------------------
@app.route("/")
def index():
    return render_template("client.html", mode="UDP")

# -----------------------------
# LÓGICA UDP
# -----------------------------
def init_udp():
    global udp_socket
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socketio.emit("client_log", {"message": f"Socket UDP listo para enviar a {SERVER_IP}:{SERVER_PORT}"})
    except Exception as e:
        socketio.emit("client_log", {"message": f"Error creando socket UDP: {e}"})

# -----------------------------
# EVENTOS SOCKET.IO
# -----------------------------
@socketio.on("send_message")
def handle_send_message(data):
    global udp_socket
    msg = data.get("message")
    if udp_socket:
        try:
            udp_socket.sendto(msg.encode('utf-8'), (SERVER_IP, SERVER_PORT))
            # En UDP no hay "conexión", así que asumimos enviado
        except Exception as e:
            socketio.emit("client_log", {"message": f"Error enviando UDP: {e}"})
    else:
        socketio.emit("client_log", {"message": "Socket UDP no inicializado."})

@socketio.on("connect")
def handle_connect():
    if not udp_socket:
        init_udp()
    else:
         socketio.emit("client_log", {"message": f"Socket UDP listo."})

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=WEB_PORT,
        debug=False,
        use_reloader=False
    )
