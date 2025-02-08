#!/bin/bash

echo "Iniciando o Tracker..."
python start_tracker.py &
TRACKER_PID=$!
sleep 2  # Tempo para garantir que o tracker iniciou


# Iniciar a Interface Web
echo "Iniciando a Interface Web..."
python app.py &
WEB_PID=$!

# Capturar saída e aguardar comandos
echo "Sistema P2P iniciado! Pressione Ctrl+C para encerrar."
trap "echo 'Encerrando processos...'; kill $TRACKER_PID $PEER_PID $WEB_PID; exit" SIGINT

wait
