import socket
import threading
import time
import json
from flask import Flask, render_template
from flask_socketio import SocketIO
from scapy.all import sniff
import select

# -----------------------------
# CONFIGURACIÓN DE PUERTOS
# -----------------------------
WEB_PORT = 5000
TCP_UDP_PORT = 5001
INTERFACE = "ZeroTier Virtual Port"

# -----------------------------
# FLASK + SOCKET.IO
# -----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode="threading")

@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# ENVIAR MENSAJE AL FRONTEND
# -----------------------------
def send_log(source, message):
    socketio.emit("server_log", {
        "source": source,
        "message": message,
        "timestamp": time.strftime("%H:%M:%S")
    })

# -----------------------------
# SNIFFER
# -----------------------------
def packet_handler(pkt):
    try:
        layers = []
        
        # Agregar Capa Física
        layers.append({
            "name": "Capa Física",
            "Tamaño Total": len(pkt)
        })

        current = pkt

        while current:
            layer_name = current.__class__.__name__
            display_name = layer_name

            if layer_name == "Ether":
                display_name = "Capa Enlace (Ether)"
            elif layer_name == "IP":
                display_name = "Capa Red (IP)"
            elif layer_name == "TCP":
                display_name = "Capa Transporte (TCP)"
            elif layer_name == "UDP":
                display_name = "Capa Transporte (UDP)"
            elif layer_name == "Raw":
                display_name = "Capa Aplicación"

            layer_info = {"name": display_name}

            for field in current.fields_desc:
                value = current.getfieldval(field.name)
                try:
                    json.dumps(value)
                except:
                    value = str(value)

                layer_info[field.name] = value

            layers.append(layer_info)
            current = current.payload

        socketio.emit("new_packet", {
            "summary": pkt.summary(),
            "layers": layers
        })

    except Exception as e:
        send_log("SNIFFER_ERROR", f"Error leyendo paquete: {e}")

def start_sniffer():
    try:
        send_log("SNIFFER", f"Iniciando Sniffer en interfaz: {INTERFACE}")

        sniff(
            iface=INTERFACE,
            prn=packet_handler,
            store=False,
            filter=f"(tcp or udp) and port {TCP_UDP_PORT}"
        )

    except Exception as e:
        send_log("SNIFFER_ERROR", f"Sniffer detenido: {e}")

# -----------------------------
# SERVIDOR TCP + UDP CON SELECT
# -----------------------------
def start_select_server():
    try:
        # TCP
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind(("0.0.0.0", TCP_UDP_PORT))
        tcp_sock.listen(5)
        tcp_sock.setblocking(False)

        # UDP
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(("0.0.0.0", TCP_UDP_PORT))
        udp_sock.setblocking(False)

        send_log("SELECT", f"Servidor SELECT en :{TCP_UDP_PORT}")

        sockets_list = [tcp_sock, udp_sock]
        clients = []  # Lista de sockets TCP conectados

        while True:
            readable, _, _ = select.select(sockets_list + clients, [], [], 1)

            for s in readable:

                # NUEVA CONEXIÓN TCP
                if s is tcp_sock:
                    conn, addr = tcp_sock.accept()
                    conn.setblocking(False)
                    clients.append(conn)
                    send_log("TCP_CONN", f"Conexión entrante: {addr}")

                # MENSAJE UDP
                elif s is udp_sock:
                    data, addr = udp_sock.recvfrom(4096)
                    msg = data.decode(errors='ignore')
                    send_log("UDP_DATA", f"{addr} → {msg}")

                # MENSAJE TCP
                else:
                    try:
                        data = s.recv(4096)

                        if not data:
                            # Se desconectó
                            addr = s.getpeername()
                            send_log("TCP_CLOSE", f"Cierre desde: {addr}")
                            clients.remove(s)
                            s.close()
                            continue

                        msg = data.decode(errors='ignore')
                        addr = s.getpeername()
                        send_log("TCP_DATA", f"{addr} → {msg}")

                    except Exception as e:
                        send_log("TCP_ERROR", f"Error: {e}")
                        if s in clients:
                            clients.remove(s)
                        s.close()

    except Exception as e:
        send_log("SELECT_FATAL", f"Error crítico: {e}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    # HILO DEL SNIFFER
    threading.Thread(target=start_sniffer, daemon=True).start()

    # HILO DEL SERVIDOR SELECT (TCP + UDP)
    threading.Thread(target=start_select_server, daemon=True).start()

    # SERVIDOR WEB + SOCKET.IO
    socketio.run(
        app,
        host="127.0.0.1",
        port=WEB_PORT,
        debug=False,
        use_reloader=False
    )
