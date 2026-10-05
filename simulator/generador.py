import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# COMUNICACIÓN
# ============================================================

from Comunicacion.http_client import send_telemetry
from Comunicacion.mqtt_client import MQTTClient
from Comunicacion.config import HTTP_URL, MQTT_BROKER, MQTT_PORT


# ============================================================
# CONFIGURACIÓN
# ============================================================

CONFIG_PATH = Path(__file__).parent / "config" / "device-config.json"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def load_config():
    """
    Lee la configuración del simulador desde device-config.json.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_variable(config, variable_name):
    """
    Busca una variable dentro de la configuración.
    """
    for variable in config["variables"]:
        if variable["name"] == variable_name:
            return variable

    raise ValueError(
        f"No se encontró la variable: {variable_name}"
    )


def limit_value(value, minimum, maximum):
    """
    Mantiene un valor dentro de los límites establecidos.
    """
    return max(minimum, min(value, maximum))


def apply_variation(
    value,
    max_variation,
    minimum,
    maximum,
    decimals
):
    """
    Genera una pequeña variación aleatoria
    sobre el valor anterior.
    """

    variation = random.uniform(
        -max_variation,
        max_variation
    )

    new_value = value + variation

    new_value = limit_value(
        new_value,
        minimum,
        maximum
    )

    return round(
        new_value,
        decimals
    )


# ============================================================
# SIMULADOR DE UN ESPACIO
# ============================================================

class ParkingSimulator:

    def __init__(self, config, space_id):

        self.config = config
        self.device_id = config["device_id"]
        self.space_id = space_id

        self.interval_seconds = config["interval_seconds"]
        self.scenario = config["scenario"]
        self.seed = config["seed"]

        # Semilla diferente para cada espacio
        random.seed(
            self.seed + int(space_id[-2:])
        )

        # Variables de configuración
        self.occupied_config = get_variable(
            config,
            "occupied"
        )

        self.distance_config = get_variable(
            config,
            "distance"
        )

        self.duration_config = get_variable(
            config,
            "parking_duration"
        )

        # Valores iniciales
        self.occupied = self.occupied_config["initial"]

        self.distance = self.distance_config["initial"]

        self.parking_duration = self.duration_config["initial"]

        # Estado inicial
        self.state = "FREE"

        # ----------------------------------------------------
        # Para que podamos ver vehículos rápidamente
        # durante la demostración.
        # ----------------------------------------------------

        if space_id in ["E01", "E03"]:
            self.state = "ARRIVING"

            self.distance = random.uniform(
                150,
                250
            )

    # ========================================================
    # GENERAR DATOS
    # ========================================================

    def generate_data(self):

        # ----------------------------------------------------
        # ESPACIO LIBRE
        # ----------------------------------------------------

        if self.state == "FREE":

            self.occupied = False

            self.parking_duration = 0

            self.distance = random.uniform(
                300,
                self.distance_config["simulation_max"]
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )

            # Probabilidad de que llegue un vehículo
            if random.random() < 0.25:

                self.state = "ARRIVING"

        # ----------------------------------------------------
        # VEHÍCULO LLEGANDO
        # ----------------------------------------------------

        elif self.state == "ARRIVING":

            self.occupied = False

            self.parking_duration = 0

            movement = random.uniform(
                35,
                45
            )

            self.distance -= movement

            self.distance = limit_value(
                self.distance,
                self.distance_config["simulation_min"],
                self.distance_config["simulation_max"]
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )

            # Cuando el vehículo está suficientemente cerca,
            # el espacio queda ocupado.
            if self.distance <= 50:

                self.distance = max(
                    self.distance,
                    2
                )

                self.occupied = True

                self.parking_duration = 0

                self.state = "PARKED"

        # ----------------------------------------------------
        # VEHÍCULO ESTACIONADO
        # ----------------------------------------------------

        elif self.state == "PARKED":

            self.occupied = True

            # Pequeña variación del sensor de distancia
            self.distance = apply_variation(
                self.distance,
                self.distance_config["max_variation"],
                2,
                50,
                self.distance_config["decimals"]
            )

            # El tiempo aumenta según el intervalo real
            # del simulador.
            self.parking_duration += (
                self.interval_seconds / 60
            )

            # Limitar el tiempo máximo de simulación
            self.parking_duration = limit_value(
                self.parking_duration,
                self.duration_config["simulation_min"],
                self.duration_config["simulation_max"]
            )

            # ------------------------------------------------
            # ESCENARIO NORMAL
            # ------------------------------------------------

            if self.scenario == "normal":

                if self.parking_duration >= 1:

                    if random.random() < 0.08:

                        self.state = "LEAVING"

            # ------------------------------------------------
            # ESCENARIO ALERTA
            # ------------------------------------------------

            elif self.scenario == "alert":

                alert_rule = self.duration_config["alert_rule"]

                if (
                    alert_rule is not None
                    and alert_rule["operator"] == ">"
                    and self.parking_duration > alert_rule["value"]
                ):

                    print(
                        f"⚠️ ALERTA: {self.space_id} "
                        f"lleva {self.parking_duration:.2f} minutos ocupado."
                    )

                    if self.parking_duration >= 65:

                        self.state = "LEAVING"

        # ----------------------------------------------------
        # VEHÍCULO SALIENDO
        # ----------------------------------------------------

        elif self.state == "LEAVING":

            self.occupied = True

            # El vehículo se aleja.
            self.distance += random.uniform(
                20,
                40
            )

            self.distance = limit_value(
                self.distance,
                self.distance_config["simulation_min"],
                self.distance_config["simulation_max"]
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )

            # Cuando está suficientemente lejos,
            # el espacio vuelve a quedar libre.
            if self.distance >= 100:

                self.distance = self.distance_config["initial"]

                self.occupied = False

                self.parking_duration = 0

                self.state = "FREE"

        # ====================================================
        # RESULTADO
        # ====================================================

        return {
            "occupied": self.occupied,
            "distance": self.distance,
            "parking_duration": round(
                self.parking_duration,
                2
            )
        }

    # ========================================================
    # GENERAR MENSAJE
    # ========================================================

    def generate_message(self, sequence):

        measurements = self.generate_data()

        message = {

            "message_id": (
                f"{self.device_id}-"
                f"{self.space_id}-"
                f"{sequence:06d}"
            ),

            "device_id": self.device_id,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "sequence": sequence,

            "measurements": {

                "space_id": self.space_id,

                **measurements

            }
        }

        return message


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("=" * 70)
    print("SIMULADOR DE PARQUEADERO INTELIGENTE")
    print("=" * 70)

    config = load_config()

    # ========================================================
    # CONEXIÓN MQTT
    # ========================================================

    mqtt_client = MQTTClient(
        MQTT_BROKER,
        MQTT_PORT
    )

    mqtt_connected = mqtt_client.connect()

    print()
    print("Device ID:", config["device_id"])
    print("Intervalo:", config["interval_seconds"], "segundos")
    print("Escenario:", config["scenario"])
    print("Seed:", config["seed"])

    print(
        "Espacios:",
        ", ".join(config["spaces"])
    )

    print()
    print("=" * 70)
    print()

    # Crear un simulador para cada espacio
    simulators = [

        ParkingSimulator(
            config,
            space_id
        )

        for space_id in config["spaces"]

    ]

    # Número de lecturas
    num_readings = 30

    # ========================================================
    # CICLO PRINCIPAL
    # ========================================================

    for sequence in range(
        1,
        num_readings + 1
    ):

        print()
        print("=" * 70)
        print(
            f"LECTURA #{sequence}"
        )
        print("=" * 70)
        print()

        # Generar datos de todos los espacios
        for simulator in simulators:

            message = simulator.generate_message(
                sequence
            )

            # =================================================
            # ENVÍO HTTP
            # =================================================

            send_telemetry(
                HTTP_URL,
                message
            )

            # =================================================
            # ENVÍO MQTT
            # =================================================

            if mqtt_connected:

                topic = (
                    f"parqueadero/espacios/"
                    f"{message['measurements']['space_id']}"
                )

                mqtt_client.publish(
                    topic,
                    message
                )

            # =================================================
            # MOSTRAR MENSAJE
            # =================================================

            print(
                json.dumps(
                    message,
                    indent=4,
                    ensure_ascii=False
                )
            )

            print()
            print("-" * 70)

        # Esperar el intervalo configurado
        time.sleep(
            config["interval_seconds"]
        )

    # ========================================================
    # DESCONECTAR MQTT
    # ========================================================

    if mqtt_connected:
        mqtt_client.disconnect()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()