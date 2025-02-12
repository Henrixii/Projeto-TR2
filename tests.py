import json
import time
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from peers import Peer

def run_tests(peer, peer_id, filename, save_path):
    """Executa testes de download com diferentes quantidades de conexões paralelas."""
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        for num_connections in [1, 2, 3, 4]:
            start_time = time.time()
            future = executor.submit(peer.request_file, peer_id, filename, save_path, num_connections)
            try:
                future.result(timeout=60)  # Timeout de 60 segundos por teste
            except TimeoutError:
                print(f"[ERRO] Timeout ao baixar com {num_connections} conexões.")
                results[num_connections] = None
                continue
            except Exception as e:
                print(f"[ERRO] Falha ao baixar com {num_connections} conexões: {e}")
                results[num_connections] = None
                continue
            
            total_time = time.time() - start_time
            results[num_connections] = total_time
            print(f"{num_connections} conexões: {total_time:.2f} segundos")
    
    with open("download_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Resultados salvos em download_results.json")

if __name__ == "__main__":
    peer = Peer('127.0.0.1', 41830)
    run_tests(peer, 41830, "grande_arquivo.dat", "./")
