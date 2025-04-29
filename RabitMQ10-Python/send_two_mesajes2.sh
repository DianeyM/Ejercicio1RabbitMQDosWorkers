#!/usr/bin/env bash

# Array con 2 mensajes a enviar v2
messages=(
  "Hello RabbitMQ!18........................................"
  "Hello RabbitMQ!19........................................"
)

# Recorremos el array y enviamos cada mensaje
for msg in "${messages[@]}"; do
  curl -s -X POST http://localhost:5044/send \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"${msg}\"}" \
    && echo " → Enviado: ${msg}"
  echo "-------------------------"  # Separador
done