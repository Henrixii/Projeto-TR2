from peers import Peer
import sys

if len(sys.argv) < 2:
    print("Uso: python start_peer.py <porta>")
    sys.exit(1)

PEER_HOST = "127.0.0.1"
PEER_PORT = int(sys.argv[1])

peer = Peer(PEER_HOST, PEER_PORT)
peer.connect_to_tracker("127.0.0.1", 5000)
peer.add_file("./arquivos/peer1/teste.txt")

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

    elif comando == "sair":
        print("Encerrando peer...")
        peer.remove_from_tracker()
        sys.exit(0)

    elif comando == "help":
        print("""
            Comandos disponíveis:
            mensagem   - Envia uma mensagem para um peer conectado.
            listar     - Lista os peers conectados.
            conectar   - Conectar aos peers do tracker
            baixar     - Baixa um arquivo de um peer.
            arquivos   - Lista os arquivos disponíveis de um peer.
            sair       - Remove o peer do tracker e encerra o programa.
            help       - Mostra esta mensagem de ajuda.
                    """)


    else:
        print("Comando desconhecido.")
