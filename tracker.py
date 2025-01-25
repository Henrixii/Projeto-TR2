import socket
import threading
import json


class Tracker:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.peers = {}  # {peer_id: {"host": host, "port": port}}
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
        """Lida com a comunicação com um peer."""

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                # Processa a mensagem recebida
                try:
                    message = json.loads(data.decode())
                    command = message.get("command")

                    if command == "REGISTER":
                        self.register_peer(conn, message)
                    elif command == "LIST":
                        self.list_peers(conn)
                    else:
                        self.send_response(conn, {"status": "error", "message": "Comando inválido"})
                except json.JSONDecodeError:
                    self.send_response(conn, {"status": "error", "message": "Mensagem inválida"})
        except Exception as e:
            print(f"Erro na comunicação com o peer {addr}: {e}")
        finally:
            self.remove_peer(addr)
            conn.close()
            print(f"Conexão encerrada com {addr}")

    def register_peer(self, conn, message):
        """Registra um peer no tracker."""

        try:
            peer_id = message.get("peer_id")
            peer_host = message.get("host")
            peer_port = message.get("port")

            if not peer_id or not peer_host or not peer_port:
                self.send_response(conn, {"status": "error", "message": "Dados de registro incompletos"})
                return

            self.peers[peer_id] = {"host": peer_host, "port": int(peer_port)}
            self.send_response(conn, {"status": "success", "message": "Registro feito com sucesso"})
            print(f"Peer registrado: {peer_id}, IP: {peer_host}, Porta: {peer_port}")
        except Exception as e:
            print(f"Erro ao registrar peer: {e}")
            self.send_response(conn, {"status": "error", "message": "Erro ao registrar peer"})

    def list_peers(self, conn):
        """Retorna a lista de peers registrados."""

        try:
            self.send_response(conn, {"status": "success", "peers": self.peers})
        except Exception as e:
            print(f"Erro ao listar peers: {e}")
            self.send_response(conn, {"status": "error", "message": "Erro ao listar peers"})

    def remove_peer(self, addr):
        """Remove um peer da lista ao desconectar."""

        for peer_id, info in list(self.peers.items()):
            if info["host"] == addr[0] and info["port"] == addr[1]:
                del self.peers[peer_id]
                print(f"Peer removido: {peer_id}")
                break

    def send_response(self, conn, response):
        """Envia uma resposta para o peer."""
        
        try:
            conn.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")
