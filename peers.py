import socket
import threading
import json
import os
import time

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_conn = None
        self.tracker_host = None
        self.tracker_port = None
        self.connected_peers = {}  # {peer_id: connection}
        self.files = {}  # Arquivos disponíveis para compartilhamento

    def list_connected_peers(self):
        """Lista os peers atualmente conectados."""
        if self.connected_peers:
            print("Peers conectados:")
            for peer_id in self.connected_peers.keys():
                print(f"- {peer_id}")
        else:
            print("Nenhum peer conectado.")

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
        """Registra o peer no tracker e tenta se conectar aos outros peers"""

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
            self.tracker_conn.sendall(json.dumps({"command": "LIST"}).encode())
            response = self.tracker_conn.recv(1024).decode()
            data = json.loads(response)

            if data.get("status") == "success":
                peers = data.get("peers", {})
                for peer_id, info in peers.items():
                    if peer_id != f"{self.host}:{self.port}":  # Evita conectar a si mesmo
                        self.connect_to_peer(peer_id, info["host"], info["port"])
            else:
                print("Erro ao obter lista de peers:", data.get("message"))
        except Exception as e:
            print(f"Erro ao descobrir peers: {e}")

    def search_file(self, filename):
        """Busca um arquivo entre os peers conectados e lista quais possuem o arquivo."""
        
        if not self.tracker_conn:
            print("[ERRO] Não está conectado ao tracker.")
            return
        
        peers_with_file = []

        try:
            # Pede a lista de peers ao tracker
            self.tracker_conn.sendall(json.dumps({"command": "LIST"}).encode())
            response = self.tracker_conn.recv(1024).decode()
            data = json.loads(response)

            if data.get("status") == "success":
                peers = data.get("peers", {})

                for peer_id, info in peers.items():
                    if peer_id != f"{self.host}:{self.port}":  # Evita perguntar a si mesmo
                        if self.query_peer_for_file(peer_id, info["host"], info["port"], filename):
                            peers_with_file.append(peer_id)

            if peers_with_file:
                print(f"\n[✅] O arquivo '{filename}' está disponível nos seguintes peers:")
                for peer in peers_with_file:
                    print(f"- {peer}")
            else:
                print(f"\n[❌] Nenhum peer possui o arquivo '{filename}'.")

        except Exception as e:
            print(f"[ERRO] Falha ao buscar arquivo: {e}")


    def query_peer_for_file(self, peer_id, peer_host, peer_port, filename):
        """Consulta um peer específico para saber se ele tem o arquivo."""
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, int(peer_port)))

            # Envia a solicitação de busca de arquivo
            conn.sendall(json.dumps({"command": "LIST_FILES"}).encode())

            # Recebe a resposta e verifica se o arquivo está disponível
            response = conn.recv(1024).decode()
            data = json.loads(response)

            conn.close()

            if filename in data.get("files", []):
                return True  # Peer tem o arquivo
            return False  # Peer não tem o arquivo

        except Exception as e:
            print(f"[ERRO] Não foi possível consultar {peer_id}: {e}")
            return False


    def connect_to_peer(self, peer_id, peer_host, peer_port):
        """Estabelece uma conexão com outro peer e mantém a conexão aberta."""
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, int(peer_port)))
            self.connected_peers[peer_id] = conn
            print(f"Conectado ao peer {peer_id} em {peer_host}:{peer_port}")

            # Criar uma thread para ouvir mensagens desse peer
            threading.Thread(target=self.handle_message, args=(conn,), daemon=True).start()
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


    def add_file(self, file_path):
        """Adiciona um arquivo ao peer para compartilhamento."""
        import os

        if not os.path.exists(file_path):
            print(f"Erro: O arquivo '{file_path}' não existe.")
            return

        filename = os.path.basename(file_path)  # Obtém o nome do arquivo
        self.files[filename] = file_path  # Armazena o caminho do arquivo
        print(f"Arquivo '{filename}' adicionado ao peer para compartilhamento.")



    def request_file(self, peer_id, filename, save_path):
        """Solicita o download de um arquivo de outro peer."""
        if peer_id in self.connected_peers:
            try:
                conn = self.connected_peers[peer_id]
                request = {"command": "DOWNLOAD", "filename": filename}
                conn.sendall(json.dumps(request).encode())

                # Primeiro, recebe e interpreta a resposta JSON com o tamanho do arquivo
                response = conn.recv(1024).decode()
                if not response:
                    print("Erro: Resposta vazia recebida.")
                    return

                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    print("Erro: Resposta inválida recebida (não é JSON).")
                    return

                if data.get("status") == "success":
                    file_size = data.get("size")
                    print(f"Iniciando download do arquivo '{filename}' ({file_size} bytes)...")

                    # Agora, recebe o conteúdo do arquivo
                    with open(os.path.join(save_path, filename), "wb") as f:
                        remaining = file_size
                        while remaining > 0:
                            chunk = conn.recv(min(1024, remaining))
                            if not chunk:
                                break
                            f.write(chunk)
                            remaining -= len(chunk)

                    print(f"Download concluído: '{filename}' salvo em {save_path}")
                else:
                    print(f"Erro ao baixar arquivo: {data.get('message')}")

            except Exception as e:
                print(f"Erro ao solicitar arquivo do peer {peer_id}: {e}")
        else:
            print(f"Peer {peer_id} não está conectado.")




    def request_file_list(self, peer_id):
        """Solicita a lista de arquivos de um peer conectado."""
        if peer_id in self.connected_peers:
            try:
                conn = self.connected_peers[peer_id]
                conn.sendall(json.dumps({"command": "LIST_FILES"}).encode())

                response = conn.recv(1024).decode()
                data = json.loads(response)
                print(f"Arquivos disponíveis no peer {peer_id}: {data.get('files', [])}")
            except Exception as e:
                print(f"Erro ao solicitar arquivos do peer {peer_id}: {e}")
        else:
            print(f"Peer {peer_id} não está conectado.")


    def handle_message(self, conn):
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
                
                elif command == "CONNECT":
                    target_host = message.get("target_host")
                    target_port = message.get("target_port")
                    print(f"[DEBUG] Recebido pedido de conexão com {target_host}:{target_port}")
                    if target_host and target_port:
                        target_id = f"{target_host}:{target_port}"
                        self.connect_to_peer(target_id, target_host, int(target_port))

                elif command == "LIST_FILES":
                    files_list = list(self.files.keys())  # Lista apenas os nomes dos arquivos
                    conn.sendall(json.dumps({"files": files_list}).encode())

                elif command == "BUSCAR":
                    filename = input("Digite o nome do arquivo que deseja buscar: ").strip()
                    self.search_file(filename)  

                elif command == "DISCONNECT":
                    leaving_peer = message.get("peer_id")
                    if leaving_peer in self.connected_peers:
                        del self.connected_peers[leaving_peer]
                        print(f"[INFO] Peer {leaving_peer} foi desconectado e removido da lista de peers.")

                elif command == "DOWNLOAD":
                    filename = message.get("filename")
                    if filename in self.files:
                        file_path = self.files[filename]
                        try:
                            file_size = os.path.getsize(file_path)
                            conn.sendall(json.dumps({"status": "success", "size": file_size}).encode())

                            # Aguarda um pequeno intervalo para evitar mistura de JSON com binário
                            time.sleep(0.2)

                            # Agora, envia o arquivo em pedaços de 1024 bytes
                            with open(file_path, "rb") as f:
                                while chunk := f.read(1024):
                                    conn.sendall(chunk)

                            print(f"Arquivo '{filename}' enviado com sucesso.")
                        except Exception as e:
                            conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())
                    else:
                        conn.sendall(json.dumps({"status": "error", "message": "Arquivo não encontrado"}).encode())

                else:
                    print("Comando desconhecido recebido.")
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")
                break

    def remove_from_tracker(self):
        """Remove este peer do Tracker e notifica os peers conectados."""
        if not self.tracker_conn:
            print("Não está conectado ao tracker.")
            return

        # Enviar notificação para peers conectados antes de sair
        self.notify_peers_before_exit()

        message = {"command": "REMOVE", "peer_id": f"{self.host}:{self.port}"}

        try:
            self.tracker_conn.sendall(json.dumps(message).encode())
            response = self.tracker_conn.recv(1024).decode()
            print(response)
        except Exception as e:
            print(f"Erro ao remover peer do Tracker: {e}")


    def notify_peers_before_exit(self):
        """Notifica todos os peers conectados que este peer está saindo."""
        for peer_id, conn in list(self.connected_peers.items()):
            try:
                conn.sendall(json.dumps({"command": "DISCONNECT", "peer_id": f"{self.host}:{self.port}"}).encode())
                conn.close()
            except Exception as e:
                print(f"Erro ao notificar {peer_id} sobre saída: {e}")
        
        # Limpar lista de peers conectados
        self.connected_peers.clear()



    def start(self):
        """Inicia o peer para escutar conexões e lidar com mensagens em uma thread separada."""
        
        def listen():
            try:
                self.socket.bind((self.host, self.port))
                self.socket.listen()
                print(f"Peer escutando em {self.host}:{self.port}")

                while True:
                    conn, addr = self.socket.accept()
                    threading.Thread(target=self.handle_message, args=(conn,)).start()
            except Exception as e:
                print(f"Erro ao iniciar o peer: {e}")

        # Iniciar a thread do listener
        threading.Thread(target=listen, daemon=True).start()

                