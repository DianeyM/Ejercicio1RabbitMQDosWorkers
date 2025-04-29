#!/usr/bin/env bash

# Array con 10 mensajes a enviar
messages=(
  "Hello RabbitMQ!6....."
  "Hello RabbitMQ!7..."
  "Hello RabbitMQ!8.."
  "Hello RabbitMQ!9....."
  "Hello RabbitMQ!10.."
  "Hello RabbitMQ!11..."
  "Hello RabbitMQ!12."
  "Hello RabbitMQ!13."
  "Hello RabbitMQ!14..."
  "Hello RabbitMQ!15."
)

# Recorremos el array y enviamos cada mensaje
for msg in "${messages[@]}"; do
  curl -s -X POST http://localhost:5044/send \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"${msg}\"}" \
    && echo " → Enviado: ${msg}"
  echo "-------------------------"  # Separador
done
