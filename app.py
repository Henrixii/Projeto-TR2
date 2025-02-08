from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import json
import threading
from peers import Peer

def generate_random_port():
    """Gera uma porta aleatória entre 6000 e 7000"""
    return random.randint(6000, 7000)

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

# Definir endereço e porta do peer
PEER_HOST = "127.0.0.1"
PEER_PORT = generate_random_port()

# Inicializar o peer (mas sem rodá-lo ainda)
peer = Peer(PEER_HOST, PEER_PORT)

def start_peer():
    """Inicia o peer em uma thread separada."""
    peer.connect_to_tracker("127.0.0.1", 5000)
    peer.start()

threading.Thread(target=start_peer, daemon=True).start()

@app.route("/")
def index():
    """Renderiza a página inicial."""
    return render_template("index.html")

@socketio.on("list_files")
def handle_list_files():
    """Solicita lista de arquivos disponíveis no peer."""
    file_list = list(peer.files.keys())
    emit("file_list", file_list)

@socketio.on("list_peers")
def handle_list_peers():
    """Solicita a lista de peers conectados ao tracker."""
    peer.tracker_conn.sendall(json.dumps({"command": "LIST"}).encode())
    response = peer.tracker_conn.recv(1024).decode()
    peers = json.loads(response).get("peers", {})
    peer.discover_and_connect_peers()
    emit("peer_list", peers)

@socketio.on("request_file_list")
def handle_request_file_list(peer_id):
    """Solicita lista de arquivos disponíveis de um peer."""
    peer_file_list = list(peer.request_file_list(peer_id))
    emit("peer_file_list", peer_file_list)



if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=8080, debug=True)
