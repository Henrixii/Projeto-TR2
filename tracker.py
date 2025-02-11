import socket
import threading
import json

class Tracker:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.peers = {}  # {peer_id: {"host": host, "port": port, "conn": conn}}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """Inicia o tracker e aceita conexões de peers."""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Tracker escutando em {self.host}:{self.port}")

            while True:
                conn, addr = self.socket.accept()
                print(f"Nova conexão de {addr}")
                threading.Thread(target=self.handle_peer, args=(conn, addr)).start()
        except Exception as e:
            print(f"Erro ao iniciar o tracker: {e}")

    def handle_peer(self, conn, addr):
        """Lida com a comunicação de um peer."""
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                message = json.loads(data.decode())
                command = message.get("command")

                if command == "REGISTER":
                    self.register_peer(conn, message)
                elif command == "LIST":
                    self.list_peers(conn)
                elif command == "CONNECT":
                    self.connect_peers(conn, message)
                elif command == "REMOVE":
                    self.remove_peer(conn, message)

                else:
                    self.send_response(conn, {"status": "error", "message": "Comando inválido"})
        except Exception as e:
            print(f"Erro na comunicação com o peer {addr}: {e}")
        finally:
            self.remove_peer(addr)
            conn.close()
            print(f"Conexão encerrada com {addr}")

    def register_peer(self, conn, message):
        """Registra um peer no tracker e envia a lista de peers."""
        peer_id = message.get("peer_id")
        peer_host = message.get("host")
        peer_port = message.get("port")

        if not peer_id or not peer_host or not peer_port:
            self.send_response(conn, {"status": "error", "message": "Dados de registro incompletos"})
            return

        self.peers[peer_id] = {"host": peer_host, "port": int(peer_port), "conn": conn}
        print(f"Peer registrado: {peer_id}, IP: {peer_host}, Porta: {peer_port}")

        self.send_response(conn, {"status": "success", "message": "Registro feito com sucesso"})

        # Enviar lista de peers conectados
        self.list_peers(conn)

        # Notificar um peer existente para se conectar ao novo peer
        existing_peers = list(self.peers.keys())
        if len(existing_peers) > 1:  # Se já houver pelo menos 1 peer além do novo
            for existing_peer_id in existing_peers:
                if existing_peer_id != peer_id:  # Evita escolher o novo peer
                    existing_peer = self.peers[existing_peer_id]
                    try:
                        print(f"[DEBUG] Notificando {existing_peer_id} para se conectar com {peer_id}")
                        existing_peer["conn"].sendall(json.dumps({
                            "command": "CONNECT",
                            "target_host": peer_host,
                            "target_port": peer_port
                        }).encode())
                        break  # Enviar apenas para um peer
                    except Exception as e:
                        print(f"❌ Erro ao enviar pedido de conexão para {existing_peer_id}: {e}")




    def list_peers(self, conn):
        """Envia a lista de peers registrados para um peer."""
        peers_list = {peer_id: {"host": info["host"], "port": info["port"]} for peer_id, info in self.peers.items()}
        self.send_response(conn, {"status": "success", "peers": peers_list})

    def connect_to_peer(self, peer_id, peer_host, peer_port):
        """Estabelece uma conexão com outro peer e mantém a conexão aberta."""
        try:
            print(f"[DEBUG] Tentando conectar ao peer {peer_id} em {peer_host}:{peer_port}")
            
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, int(peer_port)))
            
            self.connected_peers[peer_id] = conn
            print(f"✅ Conectado ao peer {peer_id} em {peer_host}:{peer_port}")

            # Criar uma thread para ouvir mensagens desse peer
            threading.Thread(target=self.handle_message, args=(conn,), daemon=True).start()
        except Exception as e:
            print(f"❌ Erro ao conectar ao peer {peer_id}: {e}")


    def remove_peer(self, conn, message):
        """Remove um peer da lista do Tracker."""
        peer_id = message.get("peer_id")

        if peer_id in self.peers:
            del self.peers[peer_id]
            print(f"Peer removido: {peer_id}")
            self.send_response(conn, {"status": "success", "message": f"Peer {peer_id} removido do Tracker"})
        else:
            self.send_response(conn, {"status": "error", "message": "Peer não encontrado"})


    def send_response(self, conn, response):
        """Envia uma resposta para o peer."""
        try:
            conn.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")
