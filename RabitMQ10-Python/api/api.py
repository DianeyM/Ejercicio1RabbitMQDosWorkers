# Importamos las librerías necesarias para crear la API y conectarnos a RabbitMQ
from flask import Flask, request, jsonify  # Flask para la API y jsonify para la respuesta JSON
import pika  # Librería para conectarse a RabbitMQ
import os  # Librería para acceder a variables de entorno
from retry import retry  # Librería para aplicar reintentos automáticos
from werkzeug.exceptions import BadRequest
import re

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Función con reintentos automáticos para conectarse a RabbitMQ y enviar un mensaje
@retry(tries=5, delay=2)  # Reintenta hasta 5 veces, esperando 2 segundos entre cada intento
def send_to_rabbitmq(message):
    # 1. Recupera la configuración desde variables de entorno;Recupera el nombre del host de RabbitMQ desde la variable de entorno RABBIT_HOST,o usa 
    # 'localhost' por defecto si no se encuentra la variable
    rabbit_host = os.getenv("RABBIT_HOST", "localhost")
    rabbit_user = os.getenv("RABBIT_USER", "guest")
    rabbit_password = os.getenv("RABBIT_PASSWORD", "guest")

    # 2. Establece las credenciales
    credentials = pika.PlainCredentials(rabbit_user, rabbit_password)

     # 3. Crea los parámetros de conexión incluyendo las credenciales
    connection_params = pika.ConnectionParameters(
        host=rabbit_host,
        credentials=credentials
    )

    # 4. Establece una conexión con RabbitMQ, utilizando el host proporcionado en la variable de entorno
    connection = pika.BlockingConnection(connection_params)

    # 5. Crea un canal de comunicación con RabbitMQ
    channel = connection.channel()

    # 6. Asegura que la cola 'tareas_distribuidas' exista (la crea si no existe) y es durable ante caidas de Rabbit
    channel.queue_declare(queue='tareas_distribuidas', durable=True)

    #7. Habilitamos confirms de publisher
    channel.confirm_delivery()

    try:
        # 8. Publica el mensaje en la cola 'tareas_distribuidas' con espera de confirmación 
        channel.basic_publish(
            exchange='',                         # Usamos el exchange por defecto
            routing_key='tareas_distribuidas',   # La cola destino del mensaje
            body=message,                        # El contenido del mensaje
            properties=pika.BasicProperties(delivery_mode = pika.DeliveryMode.Persistent) #Almacena el mensaje en disco, de modo que sobreviva a un reinicio del broker.
        )
        # Si llegamos aquí, el broker confirmó el almacenamiento
        print("Mensaje confirmado por el broker")

    except pika.exceptions.UnroutableError:
        # Si el broker no pudo enrutar o almacenar el mensaje
        print("El broker no pudo enrutar o almacenar el mensaje")
        # Opcional: relanzar para que retry lo vuelva a intentar
        raise
        #El raise sin argumentos vuelve a lanzar exactamente esa excepción (UnroutableError) hacia arriba, de modo que el decorador @retry la vea y dispare un nuevo intento según tu configuración (hasta 5 veces).
 
    finally:
        # 9. Cierra la conexión con RabbitMQ; Nos aseguramos de cerrar la conexión siempre, exitoso o no
        connection.close()

# Definir la ruta '/send' para el endpoint que recibe los mensajes y los envía a RabbitMQ
@app.route('/send', methods=['POST'])
def send_message():
    try:
        # 1. Intentar obtener el JSON del cuerpo de la solicitud
        data = request.get_json(force=True)
    except BadRequest:
        return jsonify({"status": "Error", "details": "Cuerpo inválido. Se esperaba JSON con el mensaje a enviar."}), 400

    # 2. Verificar que haya contenido en el cuerpo y que incluya el campo "message"
    if not data or "message" not in data:
        return jsonify({"status": "Error", "details": "Se requiere el campo 'message'"}), 400

    # 3. Obtener el mensaje, y eliminar espacios al inicio y al final
    message = data["message"].strip()

    if not message:
        return jsonify({"status": "Error", "details": "El mensaje no puede estar vacío"}), 400
    
    # 4. Verificar que el mensaje contiene entre 1 y 5 puntos en cualquier parte del mensaje
    match = re.findall(r'\.', message)  # Buscamos todos los puntos en el mensaje

    # Contamos cuántos puntos encontramos
    num_dots = len(match)

    # Validamos que el número de puntos sea entre 1 y 5 o, exactamente 30 o exactamente 40 para pruebas 
    if not (1 <= num_dots <= 5 or num_dots == 30 or num_dots == 40):
        return jsonify({"status": "Error", "details": "El mensaje debe contener entre 1 y 5 puntos."}), 400


    # 5. Intenta enviar el mensaje a RabbitMQ. Si RABBIT_HOST no está definido, usa 'localhost' por defecto.
    # Si ocurre un error, lo capturamos y respondemos con un mensaje de error.
    try:
        # Advertencia si no se define RABBIT_HOST
        if os.getenv("RABBIT_HOST") is None:
            print("[Advertencia] No se encontró la variable de entorno RABBIT_HOST. Usando 'localhost' por defecto en send.py.")

        # Enviar mensaje a RabbitMQ con reintentos automáticos
        send_to_rabbitmq(message)

        # Devolver una respuesta JSON indicando que el mensaje fue enviado con éxito
        return jsonify({"status": "Message sent", "message": message}), 200

    except Exception as e:
        # Si ocurre algún error, devolver un mensaje de error en formato JSON
        return jsonify({"status": "Error", "details": str(e)}), 500

# Ejecutar la aplicación Flask en todas las interfaces de red (0.0.0.0) y en el puerto 5000 (Puerto interno)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)