# Sesión 1 · LangChain: fundamentos prácticos · Prompts para Claude Code

Estos son los prompts que usamos en la práctica, en el mismo orden que en clase. Cópialos y pégalos en Claude Code uno a uno.

**Cómo usarlos**
1. Pega el prompt del paso y deja que Claude Code proponga los cambios.
2. **Lee el código antes de aceptar** (y los comandos, como `pip install`, antes de permitirlos).
3. Ejecuta y compara con el apartado *Qué deberías ver*.
4. Si no sale lo esperado, vuelve a pedírselo con lo que has aprendido.

> Antes de empezar: Python 3.10 o superior, [Ollama](https://ollama.com) instalado y el modelo descargado (`ollama pull llama3.1`, unos 4,9 GB). Abre Claude Code en una carpeta vacía.

El resultado de referencia, con todo el código comentado, está en la carpeta `langchain-basics` del material de la sesión.

---

## Paso 1 · Setup del proyecto

**Qué construye**

- Proyecto + entorno virtual
- requirements.txt: langchain, langchain-community, langchain-ollama
- Comprobar que Ollama tiene llama3.1
- Script minimo que dice hola al modelo

**Prompt**

```text
Crea un proyecto Python nuevo llamado langchain-basics. Inicializa un entorno virtual, crea requirements.txt con langchain, langchain-community y langchain-ollama e instalalo. Verifica que Ollama corre con el modelo llama3.1 y escribe un script minimo que mande 'hola' al modelo y muestre la respuesta.
```

**Qué deberías ver**

El modelo vive en tu disco (ollama list) y devuelve un AIMessage, no un texto: el parser llega en el paso 2.

---

## Paso 2 · Primera cadena LCEL

**Qué construye**

- PromptTemplate que traduce al ingles
- ChatOllama(llama3.1) como modelo
- StrOutputParser para quedarnos con el texto
- Unir las tres piezas con |

**Prompt**

```text
Crea 01_chain.py: una cadena LCEL que una un PromptTemplate (que traduzca un texto al ingles), el modelo ChatOllama(llama3.1) y un StrOutputParser con el operador |. Invocala con un ejemplo y explica en comentarios cada componente.
```

**Qué deberías ver**

ES TEXTO: True. En el paso 1 salia un AIMessage; la diferencia es el parser trabajando.

### Variación en vivo: batch

```text
Anade un ejemplo que traduzca una lista de 3 frases de golpe con cadena.batch y muestre cada original junto a su traduccion.
```

**Qué demuestra**

La misma cadena procesa una lista entera sin escribir un bucle. Y un aviso real: la tercera traduccion se ha comido 'La cadena'. Revisad siempre la salida.

---

## Paso 3 · Cadena compuesta

**Qué construye**

- Etapa 1: generar un parrafo sobre un tema
- Etapa 2: resumirlo en una frase
- RunnablePassthrough para no perder nada
- Ver salida intermedia y final

**Prompt**

```text
Amplia el script a una cadena de 2 etapas con RunnablePassthrough: la 1a genera un parrafo sobre un tema y la 2a lo resume en una frase. Muestra por consola la salida intermedia y la final.
```

**Qué deberías ver**

La salida intermedia: si el resumen fuera malo, aqui sabriamos que etapa falla.

### Variación en vivo: una tercera etapa

```text
Anade una tercera etapa que traduzca el resumen al ingles con otro RunnablePassthrough.assign y muestra las claves finales del diccionario.
```

**Qué demuestra**

Anadir una etapa es anadir una linea. El diccionario acaba con cuatro claves: generar, resumir y traducir, como en la slide de cadenas compuestas.

---

## Paso 4 · Añadir memoria

**Qué construye**

- Envolver la cadena con RunnableWithMessageHistory
- Un historial por session_id
- 3 turnos: recuerda nombre y contexto
- Control: otra sesion no recuerda nada

**Prompt**

```text
Convierte la cadena en un chat con memoria usando RunnableWithMessageHistory e InMemoryChatMessageHistory. Demuestra en 3 turnos que recuerda mi nombre y el contexto anterior, y que otra session_id no comparte memoria.
```

**Qué deberías ver**

El turno 3 sabe tu nombre, la otra sesion no. El aviso amarillo no es un error: es el puente a LangGraph.

### Variación en vivo: qué ve realmente el modelo

```text
Despues de 3 turnos, imprime el historial de la sesion (tipo de mensaje y texto) y cuantos mensajes recibiria el modelo en la siguiente llamada.
```

**Qué demuestra**

La memoria es una lista que se reenvia entera: 6 mensajes guardados + system + pregunta nueva = 8. Por eso recordar cuesta tokens.

---

## Paso 5 · Añadir una herramienta

**Qué construye**

- Dos tools con @tool: sumar y hora_actual
- bind_tools: ensenar el menu al modelo
- Pregunta que obliga a usarlas
- Ver la tool call y la respuesta final

**Prompt**

```text
Anade una tool sencilla (p.ej. devolver la hora actual o sumar dos numeros) con @tool y bind_tools sobre el modelo. Hazle una pregunta que le obligue a llamar la tool y muestra en consola la tool call y el resultado final.
```

**Qué deberías ver**

El modelo no responde: pide. Nuestro codigo ejecuta, le devuelve el resultado y solo entonces contesta.

### Variación en vivo: la tool por dentro

```text
Muestra el esquema que recibe el modelo de la tool sumar (convert_to_openai_tool) y la respuesta en crudo del modelo: content y tool_calls.
```

**Qué demuestra**

El docstring se convierte en la descripcion y los type hints en el esquema. Y la respuesta llega con content vacio: solo una peticion con argumentos.

---

## Paso 6 · Cierre y material

**Qué construye**

- Repasar el codigo con comentarios
- README que explica cada paso
- Extras con las variaciones de clase
- Repo listo para compartir

**Prompt**

```text
Revisa todo el codigo, anade comentarios didacticos y un README breve que explique cada paso. Deja el proyecto limpio para compartirlo como material de clase.
```

**Qué deberías ver**

Un archivo por paso, numerado en el orden de la clase; es el punto de partida del ejercicio.

---

*Material del Master AI Engineer · The Power · Ignacio de Pastors*
