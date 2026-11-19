
import json
import os
import boto3

bedrock = boto3.client("bedrock-runtime")

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        incidencia = body.get("incidencia", "")

        if not isinstance(incidencia, str) or not 0 < len(incidencia) <= 1000:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Incidencia invalida"})
            }

        response = bedrock.converse(
            modelId=os.environ["BEDROCK_MODEL_ID"],
            messages=[{
                "role": "user",
                "content": [{
                    "text": (
                        "Clasifica esta incidencia. Devuelve solo JSON "
                        "con categoria, prioridad y respuesta: "
                        + incidencia
                        + ". Pero es imprescindible ser extremadamente breve en la respuesta. "
                        + "Usa una respuesta corta de menos de 30 palabras. "
                    )
                }]
            }],
            inferenceConfig={"maxTokens": 300, "temperature": 0}
        )

        texto = response["output"]["message"]["content"][0]["text"]
        texto = texto.strip()

        if texto.startswith("```"):
            texto = texto.split("\n", 1)[1]
            texto = texto.rsplit("```", 1)[0]

        print("RESPUESTA BEDROCK:", repr(texto))
        resultado = json.loads(texto)

        if not isinstance(resultado, dict) or not all(
            isinstance(resultado.get(k), str)
            for k in ("categoria", "prioridad", "respuesta")
        ):
            raise ValueError("Respuesta JSON invalida")

        print(json.dumps({
            "tokens": response.get("usage"),
            "latencia_modelo": response.get("metrics")
        }))

        return {
            "statusCode": 200,
            "body": json.dumps(resultado, ensure_ascii=False)
        }

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return {
            "statusCode": 502,
            "body": json.dumps({"error": "Error procesando incidencia"})
        }
