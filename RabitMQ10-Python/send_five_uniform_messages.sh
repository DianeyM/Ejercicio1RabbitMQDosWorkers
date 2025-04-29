#!/usr/bin/env bash

# Array con los primeros 5 mensajes a enviar
messages=(
  "Hello RabbitMQ!1."
  "Hello RabbitMQ!2.."
  "Hello RabbitMQ!3..."
  "Hello RabbitMQ!4...."
  "Hello RabbitMQ!5....."
)

# Recorremos el array y enviamos cada mensaje
for msg in "${messages[@]}"; do
  curl -s -X POST http://localhost:5044/send \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"${msg}\"}" \
    && echo " → Enviado: ${msg}"
  echo "-------------------------"  # Separador
done
