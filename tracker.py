import socket
import threading

# Dicionário para armazenar peers
peers = {}

#Função de manipulação do peers
def handle_peer(conn, addr):
    print(f"Novo peer conectado: {addr}")
    while True:
        try:
            # Receber dados do peer
            data = conn.recv(1024).decode()
            if not data:
                break
            command, *args = data.split()

            #Comando que retorna todos os peers registrados
            if command == "LIST":
                peers_info = str(peers)
                conn.send(peers_info.encode())
            
            #Comando para registrar o peer
            elif command == "REGISTER":
                peer_id = args[0]  
                ip, port = addr    
                peers[peer_id] = {"ip": ip, "port": port, "files": []}
                conn.send(b"Peer registrado com sucesso.\n")
                print(f"Peer registrado: {peer_id}, IP: {ip}, Porta: {port}")
            
            #Comando de busca de arquivo
            elif command == "SEARCH":
                filename = args[0]
                # Filtra os peers que possuem o arquivo e inclui suas informações
                results = [
                    {"peer_id": peer, "ip": info["ip"], "port": info["port"]}
                    for peer, info in peers.items()
                    if filename in info.get("files", [])
                ]
                if results:
                    conn.send(str(results).encode())
                else:
                    conn.send(b"Nenhum peer encontrado com o arquivo especificado.")
            
            #Comando de adicionar arquivo ao peer
            elif command == "ADD_FILE":
                peer_id, filename = args
                if peer_id in peers:
                    peers[peer_id]["files"].append(filename)
                    conn.send(b"Arquivo adicionado com sucesso.")
        

        # Captura de erros
        except Exception as e:
            print(f"Erro: {e}")
            #break
    #conn.close()

# Função para iniciar o tracker
def start_tracker(host="0.0.0.0", port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Tracker escutando em {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn, addr)).start()

if __name__ == "__main__":
    start_tracker()