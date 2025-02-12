import time

class PeerIncentive:
    def __init__(self, peer_id):
        """
        Inicializa uma nova instância da classe.

        Parâmetros:
            peer_id (str): O identificador único para o peer.

        Atributos:
            peer_id (str): O identificador único para o peer.
            volume_of_sharing (int): O volume de dados compartilhados pelo peer, inicializado em 0.
            start_time (float): O tempo em que a instância foi criada, inicializado com o tempo atual.
            incentive_score (int): O score de incentivo para o peer, inicializado em 0.
        """
        self.peer_id = peer_id
        self.volume_of_sharing = 0
        self.start_time = time.time()
        self.incentive_score = 0

    def update_volume_of_sharing(self, data_shared):
        """
        Atualiza o volume de dados compartilhados e recalcula o score de incentivo.

        Parâmetros:
            data_shared (float): O valor de dados que foi compartilhado.

        Returna:
            None
        """
        self.volume_of_sharing += data_shared
        self.calculate_incentive_score()

    def calculate_incentive_score(self, alpha=0.7, beta=0.3):
        """
        Calcula o score de incentivo com base no volume de compartilhamento e no tempo de uso.

        O score de incentivo é calculado usando a fórmula:
        incentive_score = alpha * volume_of_sharing + beta * time_of_use

        Parâmetros:
        alpha (float): O peso para o volume de compartilhamento. O padrão é 0.7.
        beta (float): O peso para o tempo de uso. O padrão é 0.3.

        Retorna:
        None: O resultado é armazenado na variável de instância `incentive_score`.
        """
        time_of_use = time.time() - self.start_time
        self.incentive_score = alpha * self.volume_of_sharing + beta * time_of_use

class TrackerIncentive:
    def __init__(self):
        """
        Inicializa a classe TrackerIncentive.

        Atributos:
            peers (dict): Um dicionário para armazenar informações dos peers.
        """
        self.peers = {}

    def register_peer(self, peer_id):
        """
        Registra um peer com o peer_id fornecido.

        Se o peer_id ainda não estiver no dicionário de peers, um novo objeto PeerIncentive
        é criado e adicionado ao dicionário com o peer_id como chave.
        Uma mensagem de sucesso é impressa para indicar que o peer foi registrado.

        Parâmetros:
            peer_id (str): O identificador único para o peer a ser registrado.
        """
        if peer_id not in self.peers:
            self.peers[peer_id] = PeerIncentive(peer_id)
            print(f"Peer {peer_id} registrado com sucessos.")

    def update_peer_sharing(self, peer_id, data_shared):
        """
        Atualiza o volume de dados compartilhados por um peer específico e imprime o novo score de incentivo.

        Parâmetros:
            peer_id (str): O identificador único do peer.
            data_shared (int): A quantidade de dados compartilhados pelo peer.

        Returna:
            None
        """
        if peer_id in self.peers:
            self.peers[peer_id].update_volume_of_sharing(data_shared)
            print(f"Peer {peer_id} com volume de compartilhamento atualizado. Novo score de incentivo: {self.peers[peer_id].incentive_score}")

    def get_incentive_score(self, peer_id):
        """
        Recupera a pontuação de incentivo para um determinado par.

        Parâmetros:
            peer_id (str): O identificador único do par.

        Retorna:
            float: A pontuação de incentivo do par, se o par existir, caso contrário, None.
        """
        if peer_id in self.peers:
            return self.peers[peer_id].incentive_score
        return None