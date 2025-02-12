from peers import Peer
import sys

if len(sys.argv) < 2:
    print("Uso: python start_peer.py <porta>")
    sys.exit(1)

PEER_HOST = "127.0.0.1"
PEER_PORT = int(sys.argv[1])

peer = Peer(PEER_HOST, PEER_PORT)
peer.connect_to_tracker("127.0.0.1", 5000)

peer.start()  # Agora roda em segundo plano

# Loop interativo para aceitar comandos do usuário
while True:
    comando = input("\nDigite um comando(help para mais informações): ").strip().lower()
    
    if comando == "mensagem":
        recipient_id = input("Digite o ID do peer destinatário: ")
        mensagem = input("Digite a mensagem: ")
        peer.send_message_to_peer(recipient_id, mensagem)

    elif comando == "conectar":
        print("[INFO] Iniciando conexão com peers disponíveis no tracker...")
        peer.discover_and_connect_peers()
    
    elif comando == "listar":
        peer.list_connected_peers()

    elif comando == "adicionar":
        file_path = input("Digite o caminho do arquivo para adicionar: ").strip()
        peer.add_file(file_path)

    elif comando == "buscar":
        filename = input("Digite o nome do arquivo que deseja buscar: ").strip()
        peer.search_file(filename)

    elif comando == "baixar":
        peer_id = input("Digite o ID do peer do dowload:")
        filename = input("Nome do arquivo")
        save_path = input("Local de destino para dowload")
        peer.request_file(peer_id, filename, save_path)

    elif comando == "arquivos":
        peer_id = input("Digite o ID de quem você que saber os arquivos")
        peer.request_file_list(peer_id)


    elif comando == "sair":
        print("Encerrando peer...")
        peer.remove_from_tracker()
        sys.exit(0)

    elif comando == "help":
        print("""
            Comandos disponíveis:
            mensagem   - Envia uma mensagem para um peer conectado.
            listar     - Lista os peers conectados.
            conectar   - Conectar aos peers do tracker.
            baixar     - Baixa um arquivo de um peer.
            arquivos   - lista os arquivos de um peer.
            adicionar  - Adiciona arquivo ao peer.
            buscar     - Buscar os peers que tem o arquivo.
            sair       - Remove o peer do tracker e encerra o programa.
            help       - Mostra esta mensagem de ajuda.
                    """)


    else:
        print("Comando desconhecido.")
