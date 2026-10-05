import json
import paho.mqtt.client as mqtt


class MQTTClient:

    def __init__(self, broker, port=1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()

    def connect(self):
        """
        Conecta con el broker MQTT.
        """

        try:
            self.client.connect(
                self.broker,
                self.port,
                60
            )

            self.client.loop_start()

            print("Conectado al broker MQTT")

            return True

        except Exception as error:
            print(f"Error al conectar MQTT: {error}")
            return False

    def publish(self, topic, payload):
        """
        Publica un JSON en un tópico MQTT.
        """

        try:
            message = json.dumps(payload)

            result = self.client.publish(
                topic,
                message
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Mensaje MQTT enviado: {topic}")
                return True

            print("Error al publicar MQTT")
            return False

        except Exception as error:
            print(f"Error MQTT: {error}")
            return False

    def disconnect(self):
        """
        Desconecta el cliente MQTT.
        """

        self.client.loop_stop()
        self.client.disconnect()