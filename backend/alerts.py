from backend.database import save_alert


MAX_OCCUPANCY_TIME = 120


def check_occupancy_alert(data):

    measurements = data["measurements"]

    space_id = measurements["space_id"]
    occupied = measurements["occupied"]
    parking_duration = measurements["parking_duration"]

    if occupied and parking_duration > MAX_OCCUPANCY_TIME:

        message = (
            f"El espacio {space_id} supera el tiempo máximo "
            f"de permanencia de {MAX_OCCUPANCY_TIME} minutos."
        )

        save_alert(
            space_id,
            message,
            parking_duration,
            data["timestamp"]
        )

        return message

    return None