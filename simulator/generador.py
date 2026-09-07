import json
import random
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config" / "device-config.json"

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
    Genera una nueva lectura a partir del valor anterior.

    La variación máxima se obtiene desde el archivo
    device-config.json.
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

class ParkingSimulator:

    def __init__(self, config):

        self.config = config

        self.device_id = config["device_id"]
        self.interval_seconds = config["interval_seconds"]
        self.scenario = config["scenario"]
        self.seed = config["seed"]

        random.seed(self.seed)

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

        self.occupied = self.occupied_config["initial"]

        self.distance = self.distance_config["initial"]

        self.parking_duration = self.duration_config["initial"]

        self.state = "FREE"


    def generate_data(self):

        if self.state == "FREE":

            self.occupied = False

            self.parking_duration = 0

            self.distance = random.uniform(
                350,
                self.distance_config["simulation_max"]
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )

            if random.random() < 0.20:

                self.state = "ARRIVING"

        elif self.state == "ARRIVING":

            self.occupied = False

            self.parking_duration = 0

            self.distance = apply_variation(
                self.distance,
                self.distance_config["max_variation"],
                self.distance_config["simulation_min"],
                self.distance_config["simulation_max"],
                self.distance_config["decimals"]
            )

            self.distance -= 4

            self.distance = limit_value(
                self.distance,
                self.distance_config["simulation_min"],
                self.distance_config["simulation_max"]
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )
            if self.distance <= 50:

                self.occupied = True

                self.parking_duration = 0

                self.state = "PARKED"

        elif self.state == "PARKED":

            self.occupied = True

            self.distance = apply_variation(
                self.distance,
                self.distance_config["max_variation"],
                self.distance_config["simulation_min"],
                self.distance_config["simulation_max"],
                self.distance_config["decimals"]
            )

            self.distance = limit_value(
                self.distance,
                2,
                50
            )

            self.distance = round(
                self.distance,
                self.distance_config["decimals"]
            )


            self.parking_duration += 1

            self.parking_duration = limit_value(
                self.parking_duration,
                self.duration_config["simulation_min"],
                self.duration_config["simulation_max"]
            )

            self.parking_duration = round(
                self.parking_duration,
                self.duration_config["decimals"]
            )


            if self.scenario == "normal":

                if random.random() < 0.10:

                    self.state = "LEAVING"


            elif self.scenario == "alert":

                alert_rule = self.duration_config["alert_rule"]

                if (
                    alert_rule is not None
                    and alert_rule["operator"] == ">"
                    and self.parking_duration > alert_rule["value"]
                ):

                    if self.parking_duration >= 65:

                        self.state = "LEAVING"

        elif self.state == "LEAVING":

            self.occupied = True

            self.distance += random.uniform(
                1,
                self.distance_config["max_variation"]
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

            if self.distance >= 100:

                self.distance = self.distance_config["initial"]

                self.occupied = False

                self.parking_duration = 0

                self.state = "FREE"

        return {
            "occupied": self.occupied,
            "distance": self.distance,
            "parking_duration": self.parking_duration
        }

    def generate_message(self, sequence):

        measurements = self.generate_data()

        message = {

            "message_id": (
                f"{self.device_id}-{sequence:06d}"
            ),

            "device_id": self.device_id,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "sequence": sequence,

            "measurements": measurements
        }

        return message


def main():

    print("=" * 65)
    print("SIMULADOR DE PARQUEADERO INTELIGENTE")
    print("=" * 65)

    config = load_config()

    print()
    print("Device ID:", config["device_id"])
    print("Intervalo:", config["interval_seconds"], "segundos")
    print("Escenario:", config["scenario"])
    print("Seed:", config["seed"])
    print()

    print("=" * 65)
    print()

    simulator = ParkingSimulator(config)

    num_readings = 30

    for sequence in range(1, num_readings + 1):

        message = simulator.generate_message(
            sequence
        )

        print(
            json.dumps(
                message,
                indent=4,
                ensure_ascii=False
            )
        )

        print()
        print("-" * 65)
        print()


if __name__ == "__main__":

    main()
