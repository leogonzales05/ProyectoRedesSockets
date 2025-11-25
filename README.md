# ProyectoRedesSockets
Proyecto desarrollado para el curso de Redes de Computadoras
1. Instalación de Dependencias
Antes de empezar, necesitas instalar las librerías de Python que utiliza el proyecto. Abre tu terminal y ejecuta el siguiente comando:

pip install flask flask-socketio scapy

Nota importante para Windows: Para que la funcionalidad de "sniffer" (captura de paquetes) de 
ServidorWeb.py funcione, necesitas tener instalado Npcap. Si no lo tienes, descárgalo e instálalo, asegurándote de marcar la casilla "Install Npcap in WinPcap API-compatible Mode".

2. Configuración de Direcciones
El código tiene configuraciones específicas que probablemente necesites ajustar según tu entorno de prueba (Local o Red):
En ServidorWeb.py:
Busca la línea que dice INTERFACE = "ZeroTier Virtual Port".
Si no estás usando ZeroTier, debes cambiar "ZeroTier Virtual Port" por el nombre de tu adaptador de red real (por ejemplo, "Wi-Fi", "Ethernet" o el nombre que aparezca en tus conexiones de red). Esto es necesario para que el servidor pueda "ver" y capturar el tráfico.
En ClienteTCPWeb.py y ClienteUDPWeb.py:
Busca la línea SERVER_IP = '172.28.94.179'.
Si vas a ejecutar todo en la misma computadora, cambia esa IP por "127.0.0.1".
Si usas computadoras distintas, pon la dirección IP de la computadora que ejecutará el servidor.

3. Ejecución del Servidor
El servidor es el corazón del proyecto y debe iniciarse primero.

Abre una terminal.
Navega hasta la carpeta de tu proyecto.
Ejecuta el comando: python ServidorWeb.py
Ve a tu navegador web e ingresa a: http://127.0.0.1:5000
Verás el panel de control del servidor esperando conexiones.

4. Ejecución del Cliente TCP
Abre una nueva terminal (no cierres la del servidor).
Ejecuta el comando: python ClienteTCPWeb.py
Ve a tu navegador web e ingresa a: http://127.0.0.1:5002
Este cliente intentará conectarse automáticamente al servidor y podrás enviar mensajes.

5. Ejecución del Cliente UDP
.- Abre otra nueva terminal.
.- Ejecuta el comando: python ClienteUDPWeb.py
.- Ve a tu navegador web e ingresa a: http://127.0.0.1:5003
.- Desde aquí podrás enviar paquetes UDP al servidor.

Resumen de Accesos Web
Monitor del Servidor: Puerto 5000
Interfaz Cliente TCP: Puerto 5002
Interfaz Cliente UDP: Puerto 5003
