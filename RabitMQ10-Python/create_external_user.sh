#!/bin/bash

echo "👉 Creando usuario 'dianey' en RabbitMQ..."
docker exec -it rabbitmq9 rabbitmqctl add_user dianey 'dianey94*'

echo "✅ Usuario 'dianey' creado."
echo "--------------------------------------------------------------"

echo "👉 Asignando permisos de acceso a 'dianey'..."
docker exec -it rabbitmq9 rabbitmqctl set_permissions -p / dianey ".*" ".*" ".*"

echo "✅ Permisos asignados correctamente."
echo "--------------------------------------------------------------"

echo "👉 Estableciendo rol de 'administrator' para 'dianey'..."
docker exec -it rabbitmq9 rabbitmqctl set_user_tags dianey administrator

echo "✅ Rol 'administrator' asignado."
echo "--------------------------------------------------------------"

echo "👉 Listando usuarios actuales en RabbitMQ:"
docker exec -it rabbitmq9 rabbitmqctl list_users
