# Projeto-TR2

Este projeto propõe a implementação de um sistema Peer-to-Peer (P2P) simplificado com funcionalidades de chat, busca e compartilhamento de arquivos, além de transferências otimizadas e um mecanismo de incentivo para peers colaborativos. Aqui está um resumo com foco na implementação do tracker centralizado e suas funções no sistema:

## Descrição Geral do Projeto

- Chat entre peers: Comunicação direta entre dois peers.

- Busca de arquivos: Permite que os peers consultem e encontrem arquivos na rede, com base em metadados.

- Transferência de arquivos: Envio e recebimento de arquivos diretamente entre peers, usando múltiplas conexões paralelas (e.g., N conexões simultâneas para melhorar a taxa de download).

- Tracker centralizado: Um servidor responsável por gerenciar os peers ativos e ajudar os clientes a se descobrirem.

- Interface básica: Uma interface para interação com essas funcionalidades.

## Testando o Tracker

1. Execute o tracker pelo comando:

    ```bash
    python3 tracker.py
    ```

    Se no terminal aparecer uma mensagem:

    ```bash
    Tracker escutando em 0.0.0.0:5000
    ```

    O trecker foi iniciado com sucesso.

2. Em outro terminal use um cliente `telnet` para simular peers:

    ```bash
    telnet localhost 5000
    ```

    Uma mensagem de conecxão ira aparecer no trecker.

3. Para testar o tracker tente utilizar os comandos `REGISTER`, `ADD_FILE` e `SEARCH` conforme os exemplos a baixo:

- REGISTER:

    ```bash
    REGISTER <peer_id>
    ```

- ADD_FILE:

    ```bash
    ADD_FILE <peer_id>, <arquivo>
    ```

- SEARCH:

    ```bash
    SEARCH <arquivo>
    ```
