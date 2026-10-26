import requests


def send_telemetry(url, payload):
    """
    Envía datos del parqueadero mediante HTTP POST.
    """

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5
        )

        print(f"Respuesta HTTP: {response.status_code}")

        if response.status_code in (200, 201, 204):
            print("Telemetría enviada correctamente")
            return True

        elif response.status_code == 400:
            print("Error 400: datos incorrectos")

        elif response.status_code == 404:
            print("Error 404: endpoint no encontrado")

        elif response.status_code == 500:
            print("Error 500: error interno del servidor")

        else:
            print(f"Error HTTP inesperado: {response.status_code}")

        return False

    except requests.exceptions.Timeout:
        print("Error: tiempo de espera agotado")

    except requests.exceptions.ConnectionError:
        print("Error: no se pudo conectar con el backend")

    except requests.exceptions.RequestException as error:
        print(f"Error HTTP: {error}")

    return False