
# Sistema Distribuido con RabbitMQ, Flask y Docker

Este proyecto demuestra el uso de RabbitMQ como sistema de mensajería en una arquitectura distribuida con múltiples servicios Dockerizados. Basicamente consiste en una arquitectura de microservicios que utiliza **RabbitMQ** como un sistema de mensajería para desacoplar los diferentes componentes del sistema. Los servicios están dockerizados y se comunican entre sí a través de colas de mensajes gestionadas por RabbitMQ. 

El sistema está compuesto por tres servicios:

1. **rabbitmq-service**: El contenedor que aloja el servidor RabbitMQ con interfaz de administración para gestionar las colas.
2. **sender**: Una API basada en Flask que recibe solicitudes HTTP y publica mensajes en una cola de RabbitMQ.
3. **worker1 y worker2**: Un consumidor que recibe y procesa mensajes desde la cola.

##  1. Estructura del Proyecto

```plaintext
.
├── api/                          # Carpeta que contiene el código y configuración de la API
│   ├── api.py                    # Archivo Python que implementa la API Flask para enviar mensajes a RabbitMQ
│   ├── Dockerfile                # Dockerfile para construir el contenedor de la API
│   ├── requirements.txt          # Archivo con las dependencias de Python para la API (como Flask y Pika)
├── consumer/                     # Carpeta que contiene el código y configuración de los consumidores (workers)
│   ├── receiver.py               # Archivo Python que implementa la lógica de los consumidores que procesan mensajes
│   ├── Dockerfile                # Dockerfile para construir el contenedor de los consumidores
│   ├── requirements.txt          # Archivo con las dependencias necesarias para los consumidores (como Pika)
├── docker-compose.yml            # Archivo de configuración de Docker Compose que define los servicios (RabbitMQ, API, Consumers)
├── send_five_uniform_messages.sh # Script para enviar cinco mensajes uniformes a RabbitMQ
├── send_ten_messages.sh          # Script para enviar diez mensajes a RabbitMQ
├── send_two_messages.sh          # Script para enviar dos mensajes a RabbitMQ
├── send_two_messages2.sh         # Script para enviar otros dos mensajes a RabbitMQ
├── create_external_user.sh       # Script para crear un usuario externo en RabbitMQ con permisos de administrador
├── .env                          # Archivo de configuración que contiene las variables de entorno necesarias para el proyecto
└── README.md                     # Archivo de documentación de este proyecto
```

## 2. Requisitos

- Docker  
- Docker Compose  
- curl
- Python 3.9 o superior


## 3. Instalación

```bash
git clone <repositorio>
cd <proyecto>
docker-compose up --build
```

## 4. Verificar servicios en ejecución

```bash
docker ps
```

## 5. Probar: 
Por comodidad y para ver en tiempo real, puedes abrir tres terminales; uno para ejecutar los mensajes, otra para ver los registro de un worker y otro para ver los registros del otro worker. Deja estas tres terminales activas durante las pruebas para que vayas viendo el flujo enviado por el publicador y el flujo recibido por los workers:

### 5.1 DISTRIBUCIÓN UNIFORME DE TAREAS:

*En la primera consola:
#### 5.1.1 Enviar trabajos simulados:
##### A. Enviar trabajos simulados manualmente, uno por uno:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!1."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!2.."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!3..."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!4...."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!5....."}'
```

##### B. O dar permisos a `send_five_uniform_messages.sh` y ejecutarlo. Este script está en la raíz del proyecto.
Solo se deben enviar los trabajos simulados por consola o solo se debe ejecutar el archivo `.sh` correspondiente, no las dos cosas, porque en ese caso, quedarían DUPLICADOS los trabajos. Para dar los permisos y ejecutar el script:

```
chmod +x send_five_uniform_messages.sh
bash send_five_uniform_messages.sh
```

*En las otras dos consolas:
#### 5.1.2 Ver que los mensajes se distribuyeron uniformemente entre los dos workers:
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```

#### 5.1.3 ℹ️Nota importante: 
Como se van a hacer una cantidad considerable de pruebas, si en algún momento se acumulan mucha información con los comandos `docker logs -f rabbit_worker1` y `docker logs -f rabbit_worker2`, se pueden limpiar logs antes de cada prueba: 

##### 5.1.3.1 Se puede borrar el contenido del archivo: 
```
/var/lib/docker/containers/<container_id>/<container_id>-json.log
```
Esto, mediante:
```
sudo truncate -s 0 $(docker inspect --format='{{.LogPath}}' rabbit_worker1) && sudo truncate -s 0 $(docker inspect --format='{{.LogPath}}' rabbit_worker2)
```
---

> ⚠️ Precauciones: Usa truncate solo si estás seguro de que no necesitas revisar esos logs después.Sin embargo, truncate esto no afecta al funcionamiento del contenedor ni a sus volúmenes, colas o estado:

---

##### 5.1.3.2 Para que el truncamiento no altere los prints y se muestren inmediatamente, se reinician los dos workers:
```
docker restart rabbit_worker1 rabbit_worker2
```
Este proceso puede tardar un poco.

##### 5.1.3.3 Luego vuelves a engancharte, una vez los dos workers se hayan reiniciado:
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```

---

> ℹ️⚠️ Importante: `docker logs -f` no muestra nada inmediatamente después de `truncate`, si no se reinician los workers, debido a que truncar no  reinicia el proceso ni le dice que vuelva a escribir en el log. Si el proceso interno (como tu script Python en `rabbit_worker1`) ya tenía el archivo abierto, puede que aún esté escribiendo en un "descriptor de archivo" apuntando a un archivo que ahora está vacío, pero no ha forzado escritura nueva. Si no ha ocurrido nueva salida (print) desde el truncado, no verás nada hasta que haya algo nuevo que escribir.
Por ello se usa `docker restart rabbit_worker1 rabbit_worker2` para asegurarnos que se muestre `[*] Waiting for messages. To exit press CTRL+C` y siga el proceso sin contratiempos.

---

-----------------------------------------------------------------------

### 5.2 NO PERMITIR SOBRECARGAR WORKERS OCUPADOS EN TAREAS QUE TOMAN MÁS TIEMPO (prefetch_count=1)

A cada worker se le puede pasar un nuevo mensaje o tarea solo si confirma que ya terminó el trabajo actual. Si un worker está ocupado, con una tarea actual, los trabajos se le pasan al otro worker, si este está desocupado, o lo que es lo mismo, no tiene trabajos en desarrollo actual: 

En la primera consola:
#### 5.2.1 Enviar trabajos simulados:
##### A. Dar permisos a `send_ten_messages.sh` y ejecutarlo. Este script está en la raíz del proyecto:

```
chmod +x send_ten_messages.sh
bash send_ten_messages.sh
```

##### B. O, si no quieres ejecutar el script `send_ten_messages.sh`, puedes enviar los trabajos simulados uno por uno:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!6....."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!7..."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!8.."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!9....."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!10.."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!11..."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!12."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!13."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!14..."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!15."}'
```

En las otras dos consolas:
#### 5.2.2 Ver cómo los trabajos se distribuyen entre los workers conforme estos se desocupan y reciben un nuevo trabajo:
```
docker logs --tail 0 -f rabbit_worker1
docker logs --tail 0 -f rabbit_worker2
```
`--tail 0` se usa para no imprimir ninguna línea del historial previo de logs del contenedor, solo mostrará lo que llegue en tiempo real 
si lo usas con `-f`.

Para ver todo el histórico se puede quitar el `--tail 0`:
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```

-----------------------------------------------------------------------
### 5.3 ANTE LA CAÍDA DE UN WORKER, EL OTRO TOMA SU TRABAJO, EVITANDO QUE LOS TRABAJOS SE PIERDAN (auto_ack=False y back_ack - Confirmación manual de la finalización del trabajo mediante ack))

Simular la caída de un worker que tenía un trabajo en desarrollo antes de que termine el trabajo o antes de que envíe el ack respectivo que indica que terminó de procesar el trabajo, para ver cómo el otro worker toma el trabajo que no pudo completar el primero. De tal manera, que no se pierda el trabajo con la caida de un worker. 

En la primera consola:
#### 5.3.1 Enviar trabajos simulados:
##### A. Ejecutar el script `send_two_mesajes.sh`, contenido en la raíz del proyecto:
```
chmod +x send_two_mesajes.sh
bash send_two_mesajes.sh
```

##### B. O enviar manualmente los trabajos simulados, uno por uno:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!16.."}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!17........................................"}'
```

En las otras dos consolas:
#### 5.3.2 Ver los logs de los workers para determinar qué worker tomó el trabajo 17:
```
docker logs --tail 0 -f rabbit_worker1
docker logs --tail 0 -f rabbit_worker2
```

#### 5.3.3 Detener forzadamente el worker2 (o el que haya tomado el trabajo 17) antes de que pasen los 40 segundos que le toma al trabajo 17 ejecutarse;  
```
docker kill rabbit_worker2 o
docker kill rabbit_worker1
```

#### 5.3.4 Iniciar el worker detenido forzosamente: 
```
docker start rabbit_worker2 o
docker start rabbit_worker1
```
Docker detiene y luego inicia el contenedor, y durante ese reinicio:  
    *Si el worker aún no había hecho ack, la tarea queda pendiente.
    *RabbitMQ detecta que la conexión del consumidor se cerró sin confirmar el mensaje.
    *RabbitMQ reentrega esa tarea a otro worker disponible.
    *Se debe hacer el reinicio antes de que pasen los 40 segundos que le toma al trabajo 17 ejecutarse. Se dejo la ventana de tiempo de 40
    segundos para esta prueba.

En las consolas de los logs:
#### 5.3.5 Ver que el trabajo 17 lo tomó un worker, pero al matar ese worker, el trabajo lo tomó el otro worker; pero el mensaje no se perdió con la caida del worker que lo tomó inicialmente. 
Tener en cuenta que cuando uno de los workers se detienen forzosamente, el comando para ver los logs se detiene y hay que volver a ejecutarlo:

```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```
-----------------------------------------------------------------------
### 5.4 SI RABBIT SE CAE O FALLA, LOS MENSAJES NO SE PIERDEN (durable=True y pika.DeliveryMode.Persistent)

Antes de seguir puedes aplicar el paso 5.1.2 para truncar los logs.

En la primera consola:
#### 5.4.1 Enviar trabajos simulados:
##### A. Ejecutar el script `send_two_mesajes2.sh`, contenido en la raíz del proyecto:
```
chmod +x send_two_mesajes2.sh
bash send_two_mesajes2.sh
```

##### B. O enviar manualmente los trabajos simulados, uno por uno:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!18........................................"}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!19........................................"}'
```

En las otras dos consolas:
#### 5.4.2 Ver los logs de los workers:
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```

En la primera consola:
#### 5.4.3 Inmediatamente detener forzadamente el servicio de RabbitMQ antes que pasen los 40 segundos que necesitan los workers para procesar los trabajos y enviar el ack;  
```
docker kill rabbitmq9 
```

#### 5.4.4 Iniciar el worker detenido forzosamente: 
```
docker start rabbitmq9
```

En las otras dos consolas:
#### 5.4.5 Ver que al inicio cada worker tomó un trabajo, antes de completarse estos trabajos y enviar el ack, RabbitMQ se detuvo y al iniciarse nuevamente, los trabajos no se borraron sino que se volvieron a enviar para procesarlos por completo. 

Tener en cuenta que al caerse el servicio de Rabbit se muestra el mensaje: 🚨[!] Error al conectar con RabbitMQ: Stream connection lost: ConnectionResetError(104, 'Connection reset by peer') o 🚨[!] Error al conectar con RabbitMQ, se detienen los comandos `docker logs -f rabbit_worker1` y `docker logs -f rabbit_worker2` y hay que volver a ejecutarlos hasta que Rabbit inicie y muestre de nuevo: `[*] Waiting for messages. To exit press CTRL+C`. para que vuleva a estar arriba el sistema y se envieen los trabajos a los consumidores. Y se toma unos minutos en que rabit inice de nuevo y los workers se  onecten a él.
```
docker logs -f rabbit_worker1
docker logs -f rabbit_worker2
```
-----------------------------------------------------------------------

### 5.5 PROBAR QUE NO SE ACEPTAN MENSAJES PARA ENVIAR QUE NO CUMPLAN CON CIERTOS CRITERIOS:

#### 5.5.1 Si el mensaje tiene más de 5 puntos, o no tiene exactamente 30 o 40 puntos, muestra el error respectivo. 
Probando con 10 puntos (En la primera consola):
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "Hello RabbitMQ!.........."}'
```

#### 5.5.2 Si la petición no tiene mensaje o el mensaje está vacío, muestra el error respectivo:
En la primera consola:
```
curl -X POST http://localhost:5044/send -H "Content-Type: application/json" -d '{"message": "   "}'
curl -X POST http://localhost:5044/send -H "Content-Type: application/json"
```

-----------------------------------------------------------------------

### 5.6 INGRESAR COMO USUARIO GUEST AL PANEL DE CONTROL DE RABBITMQ DESDE EL HOST O MÁQUINA VIRTUAL:
#### A. En la primera consola:
```
curl -u guest:guest http://localhost:15672/api/overview | jq
```
#### A.Desde el navegador:
```
http://localhost:15672/api/overview

Ingresando los campos:
usuario: guest
contraseña: guest
```

-----------------------------------------------------------------------

### 5.7 INGRESAR COMO USUARIO EXTERNO AL PANEL DE CONTROL DE RABBIT:
En la primera consola: 
#### 5.7.1 Crear y configurar usuario manualmente:
##### 5.7.1.1 Crear un nuevo usuario con permisos adecuados en el contenedor:
```
docker exec -it rabbitmq9 rabbitmqctl add_user dianey 'dianey94*'
```

##### 5.7.1.2 Darle permisos al usuario

```bash
docker exec -it rabbitmq9 rabbitmqctl set_permissions -p / dianey ".*" ".*" ".*"
```

- `" .* "` (tres veces): Esas expresiones regulares significan:
  - **Configure**: Permite declarar/definir exchanges y colas.
  - **Write**: Permite publicar mensajes.
  - **Read**: Permite consumir mensajes.
- Al usar `" .* "` estás diciendo: “dale permiso para todo”.
- `-p /`: Se refiere al **vhost** donde se aplican los permisos. En este caso, el vhost por defecto `/`.


##### 5.7.1.3 Activar acceso a la interfaz web con privilegios administrativos

```bash
docker exec -it rabbitmq9 rabbitmqctl set_user_tags dianey administrator
```

##### 5.7.1.4 Verificamos que el usuario fue creado y tiene los permisos administrativos:

```bash
docker exec -it rabbitmq9 rabbitmqctl list_users
```

#### 5.7.2 O crear y configurar el usuario por medio de script:

##### 5.7.2.1 Para realizar automáticamente los pasos del numeral 5.7.1 puedes ejecutar el script `create_external_user.sh`, contenido en la raíz del proyecto:

```bash
chmod +x create_external_user.sh
bash create_external_user.sh
```

---

>⚠️ Tenga en cuenta que solo puede seguir el paso 5.7.1 o 5.7.2, no los dos, porque al ejecutar el script  create_external_user.sh se indicará que el usuario ya existe.
En dado caso, si siguió los pasos de numeral 5.7.1 y quiere probar el scrip del numeral 5.7.2, deberá eliminar el usuario creado: 

```bash
docker exec -it rabbitmq9 rabbitmqctl delete_user <nombre_usuario>  --> docker exec -it rabbitmq9 rabbitmqctl delete_user dianey
```
---
##### 5.7.2.1 Acceder desde navegador al dashboard de RabbitMQ:

Puedes acceder desde el navegador de la máquina física con el usuario `dianey` y la contraseña `dianey94*`:

```
http://IP_MÁQUINA_VIRTUAL:15672
```

---

> ⚠️ **Recomendación**: Se recomienda no permitir acceso externo al usuario guest en producción; limita el uso del dashboard de RabbitMQ en entornos de producción y evita >permitir el acceso externo al usuario `guest`. Minimamente y por ahora se podría por lo menos cambiar el nombre y/o contraseña del usuario por defecto para que no quede >como guest y pasword guest. 

---


