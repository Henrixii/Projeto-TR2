import unittest
from peers import Peer

class TestPeerIncentiveMechanism(unittest.TestCase):
    def setUp(self):
        peer = Peer("localhost", 8000)

    def test_update_peer_metrics(peer, self):
        peer.update_peer_metrics("peer1", shared_volume=100, connection_time=10)
        self.assertEqual(peer.peer_metrics["peer1"]["shared_volume"], 100)
        self.assertEqual(peer.peer_metrics["peer1"]["connection_time"], 10)

    def test_calculate_incentive_score(self, peer):
        peer.update_peer_metrics("peer1", shared_volume=100, connection_time=10)
        score = peer.calculate_incentive_score("peer1")
        expected_score = 100 * 0.7 + 10 * 0.3
        self.assertEqual(score, expected_score)

    def test_prioritize_peers(self, peer):
        peer.update_peer_metrics("peer1", shared_volume=100, connection_time=10)
        peer.update_peer_metrics("peer2", shared_volume=50, connection_time=20)
        prioritized_peers = peer.prioritize_peers()
        self.assertEqual(prioritized_peers, ["peer1", "peer2"])

if __name__ == "__main__":
    unittest.main()