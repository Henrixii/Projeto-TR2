from peers import Peer
import sys

if len(sys.argv) < 2:
    print("Uso: python peers.py <porta>")
    sys.exit(1)

# Defina o endereço e porta do peer
PEER_HOST = "127.0.0.1"
PEER_PORT = int(sys.argv[1])

# Criar e conectar o peer ao tracker
peer = Peer(PEER_HOST, PEER_PORT)
peer.connect_to_tracker("127.0.0.1", 5000)  # Conectar ao tracker na porta 5000

# Descobrir e conectar a outros peers
peer.discover_and_connect_peers()

# Mantém o peer rodando para aceitar conexões
peer.start()
