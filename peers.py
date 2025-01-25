import socket
import threading
import json

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_conn = None
        self.tracker_host = None
        self.tracker_port = None
        self.connected_peers = {}  # {peer_id: connection}
        self.files = {"file1.txt": "Conteúdo do arquivo"}  # Arquivos disponíveis para compartilhamento

    def connect_to_tracker(self, tracker_host, tracker_port):
        """Conecta ao tracker e registra o peer"""

        self.tracker_host = tracker_host
        self.tracker_port = tracker_port

        try:
            self.tracker_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_conn.connect((tracker_host, tracker_port))
            self.register_with_tracker()
        except Exception as e:
            print(f"Erro ao conectar ao tracker: {e}")

    def register_with_tracker(self):
        """Registra o peer no tracker"""

        message = {
            "command": "REGISTER",
            "peer_id": f"{self.host}:{self.port}",
            "host": self.host,
            "port": self.port,
        }
        try:
            self.tracker_conn.sendall(json.dumps(message).encode())
            response = self.tracker_conn.recv(1024).decode()
            data = json.loads(response)
            if data.get("status") == "success":
                print("Registrado com sucesso no tracker.")
            else:
                print("Erro ao registrar no tracker:", data.get("message"))
        except Exception as e:
            print(f"Erro ao registrar no tracker: {e}")

    def discover_and_connect_peers(self):
        """Obtém a lista de peers do tracker e tenta se conectar a eles."""

        if not self.tracker_conn:
            print("Não está conectado ao tracker.")
            return

        try:
            # Solicitar a lista de peers do tracker
            self.tracker_conn.sendall(json.dumps({"command": "LIST"}).encode())
            response = self.tracker_conn.recv(1024).decode()
            data = json.loads(response)

            if data.get("status") == "success":
                peers = data.get("peers", {})
                for peer_id, info in peers.items():
                    if peer_id not in self.connected_peers and info["host"] != self.host:
                        self.connect_to_peer(peer_id, info["host"], info["port"])
            else:
                print("Erro ao obter lista de peers:", data.get("message"))
        except Exception as e:
            print(f"Erro ao descobrir peers: {e}")

    def connect_to_peer(self, peer_id, peer_host, peer_port):
        """Estabelece uma conexão com outro peer."""

        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, int(peer_port)))
            self.connected_peers[peer_id] = conn
            print(f"Conectado ao peer {peer_id} em {peer_host}:{peer_port}")
        except Exception as e:
            print(f"Erro ao conectar ao peer {peer_id}: {e}")

    def send_message_to_peer(self, recipient_id, message):
        """Envia uma mensagem de chat para um peer específico."""

        if recipient_id in self.connected_peers:
            try:
                payload = {"command": "CHAT", "message": message}
                conn = self.connected_peers[recipient_id]
                conn.sendall(json.dumps(payload).encode())
                print(f"Mensagem enviada para {recipient_id}: {message}")
            except Exception as e:
                print(f"Erro ao enviar mensagem para {recipient_id}: {e}")
        else:
            print(f"Peer {recipient_id} não está conectado.")

    def search_for_files(self):
        """Busca arquivos em todos os peers conectados e imprime os resultados."""

        self.discover_and_connect_peers()  # Conectar-se a todos os peers antes de buscar arquivos
        for peer_id, conn in self.connected_peers.items():
            try:
                conn.sendall(json.dumps({"command": "LIST_FILES"}).encode())
                response = conn.recv(1024).decode()
                data = json.loads(response)
                print(f"Peer {peer_id} possui os arquivos: {data.get('files', [])}")
            except Exception as e:
                print(f"Erro ao buscar arquivos no peer {peer_id}: {e}")

    def handle_message(self, message):
        """Processa mensagens recebidas de outros peers."""

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                command = message.get("command")

                if command == "CHAT":
                    print(f"Mensagem recebida: {message.get('message')}")
                elif command == "LIST_FILES":
                    files_list = list(self.files.keys())
                    conn.sendall(json.dumps({"files": files_list}).encode())
                else:
                    print("Comando desconhecido recebido.")
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")
                break

    def start(self):
        """Inicia o peer para escutar conexões e lidar com mensagens."""
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            print(f"Peer escutando em {self.host}:{self.port}")

            while True:
                conn, addr = self.socket.accept()
                threading.Thread(target=self.handle_message, args=(conn,)).start()
        except Exception as e:
            print(f"Erro ao iniciar o peer: {e}")
