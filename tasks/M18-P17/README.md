# Tarea M18-P17

## Especificaciones

**Lambda:** clasificar-incidencia

**Endpoint HTTP:** https://llpm8x5ng1.execute-api.eu-north-1.amazonaws.com/incidencias

**Body ejemplo:**

```json
{
  "incidencia": "No puedo iniciar sesión en mi cuenta"
}
```

**Credenciales IAM** (usuario: *thepower-hisham-incidencias-profesor-user*)

- **KEY ID:** ****************3KD2
- **SECRET KEY:** ************************************yn8n

**Response:**

```json
{
  "categoria": "Autenticación",
  "prioridad": "Alta",
  "respuesta": "Verifique credenciales y restablezca la contraseña. Contacte soporte si persiste."
}
```

## Ejemplo de cURL al API Gateway que ejecuta el Lambda

```bash
for i in {1..5}; do
  echo -n "Petición $i: "

  curl -sS -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" \
    --aws-sigv4 "aws:amz:eu-north-1:execute-api" \
    --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" \
    -H "Content-Type: application/json" \
    --data-binary @peticion.json \
    "https://llpm8x5ng1.execute-api.eu-north-1.amazonaws.com/incidencias"
done
```

## Latencia, coste y límites

### Petición en frío

- Registra duración total: 1.044,61 ms
- Tiempo del modelo: 920 ms
- Tokens: 145 (96 entrada + 49 salida)
- Errores: 0

### Petición caliente

Promedio de las últimas 6 ejecuciones:

- Registra duración total (promedio): 616,79 ms
- Tiempo del modelo (promedio): 596,83 ms
- Tokens (promedio): 145 (96 entrada + 49 salida)
- Errores: 0

### Comparar 1 petición en fría con 5 calientes

La ejecución fría presentó una duración de 1.044,61 ms, frente a aproximadamente 617 ms de las ejecuciones calientes. La
diferencia se debe principalmente al tiempo adicional de inicialización de Lambda. Las ejecuciones calientes reutilizan
el entorno y evitan ese coste de arranque.

### Cálculo de 1000 peticiones

**Región:** eu-north-1 (Estocolmo).

**Modelo:** Amazon Nova 2 Lite, perfil europeo.

| Servicio                                               | Coste estimado |
|--------------------------------------------------------|----------------|
| Amazon Bedrock (96.000 tokens entrada + 49.000 salida) | 0,1906 USD     |
| AWS Lambda (256 MB, ~617 ms)                           | 0,0028 USD     |
| API Gateway (1.000 solicitudes)                        | 0,0011 USD     |
| CloudWatch (logs estimados)                            | 0,0010 USD     |
| **Total**                                              | **0,1955 USD** |

*Estimación orientativa basada en tarifas de referencia, pendiente de contrastar con los precios oficiales vigentes de
AWS. No incluye descuentos ni capa gratuita.*

**Conclusión:** el coste aproximado sería de **0,20 USD por cada 1.000 solicitudes**. Amazon Bedrock representa
prácticamente todo el coste, mientras que Lambda, API Gateway y CloudWatch tienen un impacto económico mínimo.
