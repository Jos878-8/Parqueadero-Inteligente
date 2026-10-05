const API_URL = "http://127.0.0.1:5000";


async function loadParking() {

    try {

        const response = await fetch(
            `${API_URL}/api/v1/parking`
        );

        const data = await response.json();

        displayParking(data);

    } catch (error) {

        console.error(
            "Error obteniendo parqueadero:",
            error
        );

    }

}


function displayParking(data) {

    const container =
        document.getElementById(
            "parking-container"
        );

    container.innerHTML = "";

    let occupied = 0;

    let available = 0;


    data.forEach(space => {

        const isOccupied =
            space.occupied === 1;

        if (isOccupied) {

            occupied++;

        } else {

            available++;

        }


        const div =
            document.createElement("div");

        div.className =
            `space ${
                isOccupied
                ? "occupied"
                : "available"
            }`;


        div.innerHTML = `

            <h3>
                Espacio ${space.space_id}
            </h3>

            <p>
                Estado:
                ${
                    isOccupied
                    ? "OCUPADO"
                    : "LIBRE"
                }
            </p>

            <p>
                Distancia:
                ${space.distance} cm
            </p>

            <p>
                Permanencia:
                ${space.parking_duration} min
            </p>

        `;


        container.appendChild(div);

    });


    document.getElementById(
        "occupied"
    ).textContent = occupied;


    document.getElementById(
        "available"
    ).textContent = available;

}


async function loadAlerts() {

    try {

        const response = await fetch(
            `${API_URL}/api/v1/alerts`
        );

        const data = await response.json();

        const container =
            document.getElementById(
                "alerts-container"
            );

        container.innerHTML = "";


        data.forEach(alert => {

            const div =
                document.createElement("div");

            div.className = "alert";

            div.innerHTML = `

                <strong>
                    Espacio ${alert.space_id}
                </strong>

                <p>
                    ${alert.message}
                </p>

                <small>
                    ${alert.timestamp}
                </small>

            `;

            container.appendChild(div);

        });


        document.getElementById(
            "alerts"
        ).textContent = data.length;

    } catch (error) {

        console.error(
            "Error obteniendo alertas:",
            error
        );

    }

}


async function loadHistory() {

    try {

        const response = await fetch(
            `${API_URL}/api/v1/history`
        );

        const data = await response.json();

        const table =
            document.getElementById(
                "history"
            );

        table.innerHTML = "";


        data.forEach(item => {

            const row =
                document.createElement("tr");

            row.innerHTML = `

                <td>
                    ${item.space_id}
                </td>

                <td>
                    ${
                        item.occupied
                        ? "Ocupado"
                        : "Libre"
                    }
                </td>

                <td>
                    ${item.distance} cm
                </td>

                <td>
                    ${item.parking_duration} min
                </td>

                <td>
                    ${item.timestamp}
                </td>

            `;

            table.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Error obteniendo historial:",
            error
        );

    }

}


function updateDashboard() {

    loadParking();

    loadAlerts();

    loadHistory();

}


updateDashboard();


setInterval(
    updateDashboard,
    5000
);
