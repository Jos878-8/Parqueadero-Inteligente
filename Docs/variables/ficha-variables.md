Ficha Técnica de Variables

**Proyecto:** Parqueadero Inteligente
**Variables:** `occupied`, `distance`, `parking_duration`

| Atributo | occupied | distance | parking_duration |
|---|---|---|---|
| **Nombre** | occupied | distance | parking_duration |
| **Tipo** | boolean | float | int |
| **Unidad** | No aplica | cm | minutos |
| **Descripción** | Indica si el espacio de parqueo está ocupado por un vehículo en el momento de la lectura. | Distancia medida entre el sensor ubicado en el espacio de parqueo y el vehículo estacionado (o ausencia de este). | Tiempo transcurrido desde que el vehículo ocupó el espacio de parqueo hasta la lectura actual. |
| **Valor inicial** | false | 400.0 | 0 |
| **Rango válido** | true / false | 0 a 400 cm | 0 a 1440 min (0 a 24 horas) |
| **Rango de simulación** | true / false | 2 a 400 cm | 0 a 180 min |
| **Rango esperado** | Alterna entre true y false según el escenario de ocupación simulado. | 2 a 50 cm (vehículo correctamente estacionado dentro del espacio). | 0 a 60 min |
| **Variación máxima** | No aplica (cambia por evento discreto, no por incremento numérico). | 5.0 cm por lectura | 1 min por lectura (se incrementa mientras occupied = true; se reinicia a 0 cuando occupied = false). |
| **Decimales** | No aplica | 1 | 0 |
| **Regla de alerta** | No genera alerta directa; se usa como disparador para calcular parking_duration. | distance < 2 (vehículo demasiado cerca del sensor o mal estacionado). | parking_duration > 60 (el vehículo permanece demasiado tiempo en el espacio). |
| **Visualización** | Estado tipo semáforo (verde = libre, rojo = ocupado). | Tarjeta numérica y gráfica de líneas (serie temporal). | Tarjeta, contador y gráfica de barras. |
| **Fuente** | Definición propia del equipo, basada en el comportamiento típico de un sensor de presencia (infrarrojo o ultrasónico) usado en parqueaderos inteligentes. | Rango típico del sensor ultrasónico HC-SR04 (2 cm - 400 cm), según hoja de datos del fabricante. | Supuesto académico del equipo, basado en el tiempo máximo habitual permitido en parqueaderos comerciales. |
