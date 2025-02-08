import socket
import threading
import json
import os
import time

class Peer:
    def __init__(self, host, port):
        """
        Inicializa uma nova instância de Peer.

        Args:
            host (str): O nome do host ou endereço IP do peer.
            port (int): O número da porta na qual o peer irá escutar conexões.

        Atributos:
            host (str): O nome do host ou endereço IP do peer.
            port (int): O número da porta na qual o peer irá escutar conexões.
            socket (socket.socket): O objeto socket para comunicação de rede.
            tracker_conn (None ou socket.socket): A conexão com o servidor tracker, se houver.
            tracker_host (None ou str): O nome do host ou endereço IP do servidor tracker, se houver.
            tracker_port (None ou int): O número da porta do servidor tracker, se houver.
            connected_peers (dict): Um dicionário de peers conectados, com IDs de peers como chaves e objetos de conexão como valores.
            files (dict): Um dicionário de arquivos disponíveis para compartilhamento.
        """
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_conn = None
        self.tracker_host = None
        self.tracker_port = None
        self.connected_peers = {}  # {peer_id: connection}
        self.files = {}  # {filename: file_path}

    def list_connected_peers(self):
        """
        Lista os peers atualmente conectados.

        Este método verifica o atributo `connected_peers` e imprime os IDs de todos os peers conectados.
        Se nenhum peer estiver conectado, imprime uma mensagem indicando que não há peers conectados.
        """
        if self.connected_peers:
            print("Peers conectados:")
            for peer_id in self.connected_peers.keys():
                print(f"- {peer_id}")
        else:
            print("Nenhum peer conectado.")

    def connect_to_tracker(self, tracker_host, tracker_port):
        """
        Conecta ao tracker e registra o peer.

        Args:
            tracker_host (str): O nome do host ou endereço IP do tracker.
            tracker_port (int): O número da porta do tracker.

        Raises:
            Exception: Se houver um erro ao conectar ao tracker.
        """
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port

        try:
            self.tracker_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_conn.connect((tracker_host, tracker_port))
            self.register_with_tracker()
        except Exception as e:
            print(f"Erro ao conectar ao tracker: {e}")

    def register_with_tracker(self):
        """
        Registra o peer no tracker.

        Este método envia uma mensagem de registro para o tracker contendo as informações
        de host e porta do peer. Ele aguarda uma resposta do tracker e imprime uma mensagem
        de sucesso se o registro for bem-sucedido, ou uma mensagem de erro se o registro
        falhar.

        Raises:
            Exception: Se houver um erro durante o processo de registro, uma exceção
                   é capturada e uma mensagem de erro é impressa.
        """
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
        """
        Obtém a lista de peers do tracker e tenta se conectar a eles.

        Este método envia uma solicitação ao tracker para obter a lista de peers disponíveis.
        Se a conexão com o tracker não estiver estabelecida, imprime uma mensagem de erro e retorna.
        Se a solicitação for bem-sucedida, itera pela lista de peers e tenta se conectar a cada um,
        evitando conectar-se a si mesmo.

        Raises:
            Exception: Se houver um erro ao comunicar-se com o tracker ou ao processar a resposta.

        Prints:
            Mensagens de erro se não estiver conectado ao tracker, se houver um erro ao obter a lista de peers,
            ou se houver uma exceção durante o processo.
        """
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


    def connect_to_peer(self, peer_id, peer_host, peer_port):
        """
        Estabelece uma conexão com outro peer e mantém a conexão aberta.

        Args:
            peer_id (str): Identificador do peer ao qual se conectar.
            peer_host (str): Endereço do host do peer.
            peer_port (int): Porta do peer.

        Raises:
            Exception: Se ocorrer um erro ao tentar conectar ao peer.

        Side Effects:
            Adiciona a conexão ao dicionário `self.connected_peers`.
            Inicia uma nova thread para ouvir mensagens do peer conectado.
        """
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
        """
        Envia uma mensagem de chat para um peer específico.

        Args:
            recipient_id (str): O ID do peer destinatário.
            message (str): A mensagem de chat a ser enviada.

        Raises:
            Exception: Se houver um erro ao enviar a mensagem.

        Prints:
            str: Mensagem de confirmação se a mensagem for enviada com sucesso.
            str: Mensagem de erro se o peer destinatário não estiver conectado ou se houver um erro ao enviar a mensagem.
        """
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
        """
        Adiciona um arquivo real ao peer.

        Args:
            file_path (str): O caminho do arquivo a ser adicionado.

        Returns:
            None

        Prints:
            Mensagem de erro se o arquivo não existir.
            Mensagem de sucesso se o arquivo for adicionado com sucesso.

        Side Effects:
            Atualiza o dicionário self.files com o nome do arquivo como chave e o caminho do arquivo como valor.
            Chama o método update_tracker_file_sharing com o nome do arquivo.
        """
        if not os.path.exists(file_path):
            print(f"Erro: O arquivo '{file_path}' não existe.")
            return

        filename = os.path.basename(file_path)  # Obtém o nome do arquivo
        self.files[filename] = file_path  # Armazena apenas o caminho do arquivo
        print(f"Arquivo '{filename}' adicionado ao peer.")
        self.update_tracker_file_sharing(filename)

    def update_tracker_file_sharing(self, filename):
        """
        Atualiza o tracker com o volume de compartilhamento de arquivos para um determinado arquivo.

        Args:
            filename (str): O nome do arquivo para atualizar o volume de compartilhamento.

        Raises:
            Exception: Se houver um erro ao atualizar o volume de compartilhamento no tracker.

        Returns:
            None
        """
        if self.tracker_conn:
            try:
                message = {
                    "command": "ADD_FILE",
                    "peer_id": f"{self.host}:{self.port}",
                    "data_shared": os.path.getsize(self.files[filename])
                }
                self.tracker_conn.sendall(json.dumps(message).encode())
                response = self.tracker_conn.recv(1024).decode()
                data = json.loads(response)
                if data.get("status") == "success":
                    print(f"Volume de compartilhamento atualizado no tracker para o arquivo '{filename}'.")
                else:
                    print(f"Erro ao atualizar volume de compartilhamento: {data.get('message')}")
            except Exception as e:
                print(f"Erro ao atualizar volume de compartilhamento no tracker: {e}")

    def request_file(self, peer_id, filename, save_path):
        """
        Solicita o download de um arquivo de outro peer.

        Parâmetros:
        peer_id (str): O ID do peer do qual solicitar o arquivo.
        filename (str): O nome do arquivo a ser baixado.
        save_path (str): O caminho local onde o arquivo baixado será salvo.

        Retorna:
        None

        Levanta:
        Exception: Se houver um erro no processo de solicitação do arquivo.

        O método envia uma solicitação de download para o peer especificado e lida com a resposta.
        Se o peer responder com status de sucesso, o arquivo é baixado em pedaços e salvo
        no caminho especificado. Se o peer não estiver conectado ou ocorrer um erro, mensagens
        de erro apropriadas são impressas.
        """
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
        """
        Solicita a lista de arquivos de um peer conectado.

        Args:
            peer_id (str): O identificador do peer do qual solicitar a lista de arquivos.

        Raises:
            Exception: Se houver um erro ao solicitar a lista de arquivos do peer.

        Prints:
            A lista de arquivos disponíveis do peer especificado ou uma mensagem de erro se a solicitação falhar.
        """
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
        """
        Processa mensagens recebidas de outros peers.

        Args:
            conn (socket.socket): Conexão de socket com o peer.

        Comandos suportados:
            - "CHAT": Exibe a mensagem recebida no console.
            - "LIST_FILES": Envia uma lista de arquivos disponíveis para o peer.
            - "DOWNLOAD": Envia o arquivo solicitado para o peer, se disponível.

        Tratamento de erros:
            - Envia uma mensagem de erro em caso de falha ao processar o comando ou enviar o arquivo.
        """
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
        """
        Envia um pedido para o Tracker remover este peer.
        Este método verifica se o peer está conectado ao tracker. Se estiver conectado, ele envia um 
        comando "REMOVE" junto com o ID do peer para o tracker. Em seguida, aguarda uma resposta 
        do tracker e a imprime. Se não estiver conectado ou se ocorrer um erro durante a 
        comunicação, imprime uma mensagem de erro apropriada.
        Levanta:
            Exception: Se houver um erro ao enviar o pedido ou ao receber a resposta.
        """
        if not self.tracker_conn:
            print("Não está conectado ao tracker.")
            return

        message = {"command": "REMOVE", "peer_id": f"{self.host}:{self.port}"}
        
        try:
            self.tracker_conn.sendall(json.dumps(message).encode())
            response = self.tracker_conn.recv(1024).decode()
            print(response)
        except Exception as e:
            print(f"Erro ao remover peer do Tracker: {e}")

    def start(self):
        """
        Inicia o peer para escutar conexões e lidar com mensagens.
        Este método vincula o socket do peer ao host e porta especificados,
        começa a escutar conexões de entrada e cria uma nova thread
        para lidar com cada mensagem recebida.
        Levanta:
            Exception: Se houver um erro ao iniciar o peer.
        """        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            print(f"Peer escutando em {self.host}:{self.port}")

            while True:
                conn, addr = self.socket.accept()
                threading.Thread(target=self.handle_message, args=(conn,)).start()
        except Exception as e:
            print(f"Erro ao iniciar o peer: {e}")
