import socket
import threading
import json

class Tracker:
    def __init__(self, host="0.0.0.0", port=5000):
        """
        Inicializa a instância do Tracker.

        Args:
            host (str): O nome do host ou endereço IP para vincular o tracker. Padrão é "0.0.0.0".
            port (int): O número da porta para vincular o tracker. Padrão é 5000.

        Atributos:
            host (str): O nome do host ou endereço IP ao qual o tracker está vinculado.
            port (int): O número da porta ao qual o tracker está vinculado.
            peers (dict): Um dicionário para armazenar informações dos peers com peer_id como chave.
            socket (socket.socket): Um objeto socket para comunicação de rede.
        """
        self.host = host
        self.port = port
        self.peers = {}  # {peer_id: {"host": host, "port": port, "conn": conn}}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """
        Inicia o tracker e aceita conexões de peers.

        Este método configura o socket do tracker para escutar em um endereço e porta
        específicos. Ele entra em um loop infinito para aceitar novas conexões de peers
        e cria uma nova thread para lidar com cada conexão.

        Raises:
            Exception: Se ocorrer um erro ao iniciar o tracker.
        """
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
        """
        Lida com a comunicação de um peer.

        Este método escuta continuamente por dados recebidos de uma conexão de peer,
        processa os comandos recebidos e executa as ações correspondentes.

        Args:
            conn (socket.socket): A conexão socket com o peer.
            addr (tuple): O endereço do peer.

        Comandos:
            - REGISTER: Registra um novo peer.
            - LIST: Lista todos os peers conectados.
            - CONNECT: Conecta peers.
            - REMOVE: Remove um peer.
            - ADD_FILE: Adiciona um arquivo à lista do peer.

        Se um comando inválido for recebido, uma resposta de erro é enviada de volta ao peer.

        Exceções:
            Lida com quaisquer exceções que ocorram durante a comunicação e registra uma mensagem de erro.
            Garante que o peer seja removido e a conexão seja fechada em caso de erro.

        """
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
                elif command == "ADD_FILE":
                    self.add_file(conn, message)

                else:
                    self.send_response(conn, {"status": "error", "message": "Comando inválido"})
        except Exception as e:
            print(f"Erro na comunicação com o peer {addr}: {e}")
        finally:
            self.remove_peer(addr)
            conn.close()
            print(f"Conexão encerrada com {addr}")

    def register_peer(self, conn, message):
        """
        Registra um peer no tracker e envia a lista de peers.

        Args:
            conn (socket): Conexão do peer.
            message (dict): Mensagem contendo os dados do peer, incluindo 'peer_id', 'host' e 'port'.

        Returns:
            None

        Ações:
            - Verifica se os dados de registro estão completos.
            - Registra o peer no tracker.
            - Envia uma resposta de sucesso ou erro ao peer.
            - Envia a lista de peers conectados ao peer.
        """
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
        """
        Envia a lista de peers registrados para um peer.

        Args:
            conn: O objeto de conexão para enviar a resposta.

        A resposta contém um dicionário com o status e uma lista de peers.
        Cada peer é representado por um dicionário com suas informações de host e porta.
        """
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
        """
        Remove um peer da lista do Tracker.

        Args:
            conn: Conexão do peer que está sendo removido.
            message: Dicionário contendo informações sobre o peer, incluindo o "peer_id".

        Returns:
            None
        """
        peer_id = message.get("peer_id")

        if peer_id in self.peers:
            del self.peers[peer_id]
            print(f"Peer removido: {peer_id}")
            self.send_response(conn, {"status": "success", "message": f"Peer {peer_id} removido do Tracker"})
        else:
            self.send_response(conn, {"status": "error", "message": "Peer não encontrado"})

    def add_file(self, conn, message):
        """
        Atualiza o compartilhamento de arquivos de um peer.

        Args:
            conn: Conexão do cliente.
            message (dict): Dicionário contendo as informações do peer e o volume de dados compartilhados.
                - peer_id (str): Identificador do peer.
                - data_shared (int, opcional): Volume de dados compartilhados pelo peer. Padrão é 0.

        Responde ao cliente com o status da operação:
            - "success" se o volume de compartilhamento foi atualizado com sucesso.
            - "error" se o peer não foi encontrado.
        """
        peer_id = message.get("peer_id")

        if peer_id in self.peers:
            self.send_response(conn, {"status": "success", "message": "Volume de compartilhamento atualizado"})
        else:
            self.send_response(conn, {"status": "error", "message": "Peer não encontrado"})

    def send_response(self, conn, response):
        """
        Envia uma resposta para o peer.

        Args:
            conn (socket.socket): O objeto de conexão para enviar a resposta.
            response (dict): Os dados da resposta a serem enviados.

        Raises:
            Exception: Se houver um erro ao enviar a resposta.
        """
        try:
            conn.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")
