En las otras dos consolas:
### 5.3.2 Ver los logs de los workers para determinar qué worker tomó el trabajo 17:
```
docker logs --tail 0 -f rabbit_worker1
docker logs --tail 0 -f rabbit_worker2
```

### 5.3.3 Detener forzadamente el worker2 (o el que haya tomado el trabajo 17) antes de que pasen los 40 segundos que le toma al trabajo 17 ejecutarse;  
```
docker kill rabbit_worker2 o
docker kill rabbit_worker1
```

### 5.3.4 Iniciar el worker detenido forzosamente: 
```
docker start rabbit_worker2 o
docker start rabbit_worker1
```

-----------------------------------------------------------------------
### 5.4 SI RABBIT SE CAE O FALLA, LOS MENSAJES NO SE PIERDEN (durable=True y pika.DeliveryMode.Persistent)

Antes de seguir puedes aplicar el paso 5.1.2 para truncar los logs.

En la primera consola:
### 5.4.1 Ejecutar el script `send_two_mesajes2.sh`, contenido en la raíz del proyecto:
```
chmod +x send_two_mesajes2.sh
bash send_two_mesajes2.sh
```

O enviar manualmente los trabajos simulados:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!18........................................"}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!19........................................"}'
```

En las otras dos consolas:
### 5.4.2 Ver los logs de los workers:
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```

En la primera consola:
### 5.4.3 Inmediatamente detener forzadamente el servicio de RabbitMQ antes que pasen los 40 segundos que necesitan los workers para procesar los trabajos y enviar el ack;  
```
docker kill rabbitmq9 
```

### 5.4.4 Iniciar el worker detenido forzosamente: 
```
docker start rabbitmq9
```

En las otras dos consolas:
### 5.4.5 Ver que al inicio cada worker tomó un trabajo, antes de completarse estos trabajos y enviar el ack, RabbitMQ se detuvo y al iniciarse nuevamente, los no se borraron sino que se volvieron a enviar para procesarlos por completo. Tener en cuenta que al caerse el servicio de Rabbit se muestra el mensaje: [!] Error al conectar con RabbitMQ: Stream connection lost: ConnectionResetError(104, 'Connection reset by peer') o [!] Error al conectar con RabbitMQ, se detienen los comandos `docker logs -f rabbit_worker1` y `docker logs -f rabbit_worker2` y hay que volver a ejecutarlos hasta que Rabbit inicie y muestre de nuevo: `[*] Waiting for messages. To exit press CTRL+C`.

-----------------------------------------------------------------------

### 5.5 PROBAR QUE NO SE ACEPTAN MENSAJES PARA ENVIAR QUE NO CUMPLAN CON CIERTOS CRITERIOS:
En la primera consola:
### 5.5.1 Si el mensaje tiene más de 5 puntos, o no tiene exactamente 30 o 40 puntos, muestra el error respectivo. Probando con 10 puntos:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!.........."}'
```

### 5.5.2 Si la petición no tiene mensaje o el mensaje está vacío, muestra el error respectivo:
En la primera consola:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "   "}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json"
```

-----------------------------------------------------------------------

### 5.6 INGRESAR COMO USUARIO GUEST AL PANEL DE CONTROL DE RABBITMQ DESDE EL HOST O MÁQUINA VIRTUAL:
En la primera consola:
```
curl -u guest:guest http://localhost:15672/api/overview | jq
```
Desde el navegador:
```
http://localhost:15672/api/overview
usuario: guest
contraseña: guest
```

-----------------------------------------------------------------------

### 5.7 INGRESAR COMO USUARIO EXTERNO AL PANEL DE CONTROL DE RABBIT:
En la primera consola: 
### 5.7.1 Crear un nuevo usuario con permisos adecuados en el contenedor:
```
docker exec -it rabbitmq9 rabbitmqctl add_user dianey 'dianey94*'
```


## 5.7.2 Darle permisos al usuario

```bash
docker exec -it rabbitmq9 rabbitmqctl set_permissions -p / dianey ".*" ".*" ".*"
```

- `" .* "` (tres veces): Esas expresiones regulares significan:
  - **Configure**: Permite declarar/definir exchanges y colas.
  - **Write**: Permite publicar mensajes.
  - **Read**: Permite consumir mensajes.
- Al usar `" .* "` estás diciendo: “dale permiso para todo”.
- `-p /`: Se refiere al **vhost** donde se aplican los permisos. En este caso, el vhost por defecto `/`.

---

## 5.7.3 Activar acceso a la interfaz web con privilegios administrativos

```bash
docker exec -it rabbitmq9 rabbitmqctl set_user_tags dianey administrator
```

Verificamos que el usuario fue creado y tiene los permisos administrativos:

```bash
docker exec -it rabbitmq9 rabbitmqctl list_users
```

---

## 5.7.4 Automatización con script

Para realizar automáticamente lo anterior puedes ejecutar el script `create_external_user.sh`, contenido en la raíz del proyecto:

```bash
chmod +x create_external_user.sh
bash create_external_user.sh
```

---

## 5.7.5 Acceder desde navegador

Puedes acceder desde el navegador de la máquina física con el usuario `dianey` y la contraseña `dianey94*`:

```
http://IP_MÁQUINA_VIRTUAL:15672
```

---

> ⚠️ **Recomendación**: Limita el uso del dashboard de RabbitMQ en entornos de producción y evita permitir el acceso externo al usuario `guest`.


⚠️ Nota: se recomienda no permitir acceso externo al usuario guest en producción.

---

