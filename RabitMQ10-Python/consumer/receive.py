import pika  # Importa la librería pika, que es utilizada para conectarse a RabbitMQ
import os    # Para acceder a las variables de entorno
import sys   # Para poder manejar la salida del programa
from retry import retry  # Librería para aplicar reintentos automáticos
import time

# Esta función se llama cada vez que se recibe un mensaje de la cola
def callback(ch, method, properties, body):
    try:
        # Imprime el contenido del mensaje recibido. 'body' es en bytes, por lo que se decodifica a string.
        print(f" [x] Received {body.decode()}", flush=True) 

        # Contar la complejidad: número de puntos en el mensaje
        complejidad = body.count(b'.')
        print(f" [~] Complejidad: {complejidad} segundos", flush=True)

        # Guardar tiempo de inicio:
        start_time = time.time() 

        # Simular el procesamiento según la complejidad indicada (número de puntos)
        time.sleep(body.count(b'.'))
        print(" [x] Task Done", flush=True)

        # Guardar tiempo de finalización:
        end_time = time.time()  
        elapsed_seconds = end_time - start_time

        # ← reconocemos (ack) el mensaje sólo al terminar el trabajo
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Tarea completada y ack enviada. Tiempo de procesamiento real: {elapsed_seconds:.2f} segundos\n", flush=True)

    except Exception as e:
        print(f"Error procesando tarea: {e}", flush=True)
        raise  # Cierra la conexión, RabbitMQ reencola el mensaje automáticamente
    

# Función con reintentos automáticos para conectarse a RabbitMQ con autenticación
@retry(tries=5, delay=2)  # Reintenta hasta 5 veces, esperando 2 segundos entre cada intento
def connect_to_rabbitmq():
    # Recuperar configuración de entorno: # Recupera el nombre del host de RabbitMQ desde la variable de entorno RABBIT_HOST,
    # o usa 'localhost' por defecto si no se encuentra la variable
    rabbit_host = os.getenv("RABBIT_HOST", "localhost")
    rabbit_user = os.getenv("RABBIT_USER", "guest")
    rabbit_password = os.getenv("RABBIT_PASSWORD", "guest")

    # Crear credenciales y parámetros de conexión
    credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
    connection_params = pika.ConnectionParameters(
        host=rabbit_host,
        credentials=credentials
    )

    # Establece una conexión con RabbitMQ, utilizando el host proporcionado en la variable de entorno y los otros parámetros de credenciales
    connection = pika.BlockingConnection(connection_params)
    return connection

# Función principal que establece la conexión y empieza a consumir mensajes
def main():
    try:
        # 1. Conectarse a RabbitMQ con reintentos
        connection = connect_to_rabbitmq()
        
        # 2. Crea un canal de comunicación sobre la conexión establecida
        channel = connection.channel()

        # 2.1 Limita a 1 mensaje sin ack pendiente
        channel.basic_qos(prefetch_count=1)

        # 3. Declara la cola 'tareas_distribuidas'. Si la cola ya existe, no hace nada. Esto asegura que la cola está disponible para consumir mensajes
        channel.queue_declare(queue='tareas_distribuidas', durable=True)

        # 4. Comienza a consumir mensajes de la cola 'tareas_distribuidas'. Cada vez que llegue un mensaje, se ejecutará la función 'callback'
        #    - 'auto_ack=True' significa que el mensaje será reconocido automáticamente al ser recibido.
        channel.basic_consume(
            queue='tareas_distribuidas',
            auto_ack=False,
            on_message_callback=callback
        )

        # 5. Imprime un mensaje indicando que el consumidor está esperando mensajes
        print(' [*] Waiting for messages. To exit press CTRL+C')

        # 6. Empieza el ciclo de espera y consumo de mensajes
        #    Esto es un ciclo infinito que espera y procesa mensajes.
        channel.start_consuming() 

    except pika.exceptions.AMQPConnectionError as connection_error:
        # 7. Maneja el caso en el que no se pueda establecer una conexión con RabbitMQ
        #    Si no se puede conectar, imprime el error y sale del programa
        print(f" [!] Error al conectar con RabbitMQ: {connection_error}")
        sys.exit(1)  # Sale del programa con un código de error 1

    except KeyboardInterrupt:
        # 8. Captura una interrupción del teclado (Ctrl+C) para salir del programa de manera controlada
        print(' [!] Interrumpido por el usuario')
        try:
            sys.exit(0)  # Intenta salir limpiamente
        except SystemExit:
            os._exit(0)  # En caso de que sys.exit no funcione, forzamos la salida

# Este bloque asegura que la función main() solo se ejecute cuando este archivo se ejecute directamente, no cuando se importe como módulo
if __name__ == '__main__':
    main()
