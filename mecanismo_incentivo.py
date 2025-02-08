import time

class PeerIncentive:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.volume_of_sharing = 0
        self.start_time = time.time()
        self.incentive_score = 0

    def update_volume_of_sharing(self, data_shared):
        self.volume_of_sharing += data_shared
        self.calculate_incentive_score()

    def calculate_incentive_score(self, alpha=0.7, beta=0.3):
        time_of_use = time.time() - self.start_time
        self.incentive_score = alpha * self.volume_of_sharing + beta * time_of_use

class TrackerIncentive:
    def __init__(self):
        self.peers = {}

    def register_peer(self, peer_id):
        if peer_id not in self.peers:
            self.peers[peer_id] = PeerIncentive(peer_id)
            print(f"Peer {peer_id} registrado com sucessos.")

    def update_peer_sharing(self, peer_id, data_shared):
        if peer_id in self.peers:
            self.peers[peer_id].update_volume_of_sharing(data_shared)
            print(f"Peer {peer_id} com volume de compartilhamento atualizado. Novo score de incentivo: {self.peers[peer_id].incentive_score}")

    def get_incentive_score(self, peer_id):
        if peer_id in self.peers:
            return self.peers[peer_id].incentive_score
        return None