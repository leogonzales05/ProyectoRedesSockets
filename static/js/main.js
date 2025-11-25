document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const logsContainer = document.getElementById('server-logs');
    const packetsTableBody = document.querySelector('#packets-table tbody');
    const packetDetails = document.getElementById('packet-details');
    const connectionStatus = document.getElementById('connection-status');
    const clock = document.getElementById('clock');

    let packets = []; // Store packets locally for detail view
    const MAX_LOGS = 100;
    const MAX_PACKETS = 50;
    let packetIndexMap = {};  // 🔥 NECESARIO para vincular logs con filas

    // --- Clock ---
    setInterval(() => {
        const now = new Date();
        clock.textContent = now.toLocaleTimeString();
    }, 1000);

    // --- Socket Events ---
    socket.on('connect', () => {
        connectionStatus.textContent = "CONECTADO";
        connectionStatus.classList.remove('offline');
        connectionStatus.classList.add('online');
        addLog('SYSTEM', 'Conectado al servidor WebSocket');
    });

    socket.on('disconnect', () => {
        connectionStatus.textContent = "DESCONECTADO";
        connectionStatus.classList.remove('online');
        connectionStatus.classList.add('offline');
        addLog('SYSTEM', 'Desconectado del servidor WebSocket');
    });

    socket.on('server_log', (data) => {
        addLog(data.source, data.message, data.timestamp);
    });

    socket.on('new_packet', (data) => {
        addPacket(data);
    });

    // --- UI Functions ---
    function addLog(source, message, timestamp = null) {
        if (!timestamp) {
            timestamp = new Date().toLocaleTimeString();
        }

        const div = document.createElement('div');
        div.addEventListener("click", () => {
            trySelectPacketFromLog(message);
        });
        div.className = 'log-entry';
        div.innerHTML = `
            <span class="log-time">[${timestamp}]</span>
            <span class="log-source">${source}:</span>
            <span class="log-msg">${message}</span>
        `;

        logsContainer.appendChild(div);

        // Auto scroll
        logsContainer.scrollTop = logsContainer.scrollHeight;

        // Limit entries
        while (logsContainer.children.length > MAX_LOGS) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
    }

    function addPacket(packet) {
        packets.push(packet);
        if (packets.length > MAX_PACKETS) {
            packets.pop(); // elimina el más viejo de la tabla visual, no el más viejo del array
        }

        const tr = document.createElement('tr');
        tr.dataset.index = packets.length - 1;

        let proto = 'UNK';
        let src = '?';
        let dst = '?';
        let info = packet.summary;

        let packetKey = null; // 🔹 clave para mapear paquete → log

        // --- IP Layer ---
        const ipLayer = packet.layers.find(l => l.name === 'Capa Red (IP)');
        if (ipLayer) {
            src = ipLayer.src;
            dst = ipLayer.dst;
            proto = 'IP';
        }

        // --- TCP Layer ---
        const tcpLayer = packet.layers.find(l => l.name === 'Capa Transporte (TCP)');
        if (tcpLayer) {
            proto = 'TCP';
            info = `${tcpLayer.sport} -> ${tcpLayer.dport} [${tcpLayer.flags}]`;

            // 🔹 Clave para recuperar luego desde log
            packetKey = `${src}_${tcpLayer.sport}`;
        }

        // --- UDP Layer ---
        const udpLayer = packet.layers.find(l => l.name === 'Capa Transporte (UDP)');
        if (udpLayer) {
            proto = 'UDP';
            info = `${udpLayer.sport} -> ${udpLayer.dport} Len=${udpLayer.len}`;

            packetKey = `${src}_${udpLayer.sport}`;
        }

        // --- Guardar clave → fila ---
        if (packetKey) {
            packetIndexMap[packetKey] = tr;
        }

        tr.innerHTML = `
        <td>${new Date().toLocaleTimeString()}</td>
        <td>${proto}</td>
        <td>${src}</td>
        <td>${dst}</td>
        <td>${info}</td>
    `;

        tr.addEventListener('click', () => selectPacket(packet, tr));

        packetsTableBody.insertBefore(tr, packetsTableBody.firstChild);

        while (packetsTableBody.children.length > MAX_PACKETS) {
            packetsTableBody.removeChild(packetsTableBody.lastChild);
        }
    }

    function trySelectPacketFromLog(message) {
        const regex = /\('(\d+\.\d+\.\d+\.\d+)',\s*(\d+)\)/;
        const match = message.match(regex);

        if (!match) return;

        const src = match[1];
        const sport = match[2];

        const key = `${src}_${sport}`;

        const row = packetIndexMap[key];
        if (!row) return;

        // Seleccionar fila
        document.querySelectorAll('#packets-table tr')
            .forEach(r => r.classList.remove('selected'));

        row.classList.add("selected");
        row.scrollIntoView({ behavior: "smooth", block: "center" });

        // Mostrar detalles
        row.click();
    }


    function selectPacket(packet, trElement) {
        // Highlight row
        document.querySelectorAll('#packets-table tr').forEach(r => r.classList.remove('selected'));
        trElement.classList.add('selected');

        // Show details
        packetDetails.innerHTML = '';

        packet.layers.forEach(layer => {
            const section = document.createElement('div');
            section.className = 'detail-section';

            const title = document.createElement('div');
            title.className = 'detail-title';
            title.textContent = layer.name;
            section.appendChild(title);

            for (const [key, value] of Object.entries(layer)) {
                if (key === 'name') continue;

                const row = document.createElement('div');
                row.className = 'detail-row';
                row.innerHTML = `
                    <span class="detail-key">${key}</span>
                    <span class="detail-val">${value}</span>
                `;
                section.appendChild(row);
            }
            packetDetails.appendChild(section);
        });
    }
});
