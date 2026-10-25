# Búsqueda semántica con PostgreSQL y pgvector

Dos scripts que guardan frases en PostgreSQL como vectores y buscan las más parecidas a unas preguntas:

- `01_cosine_similarity_search.py`: búsqueda semántica con distancia coseno.
- `02_multi_tenant.py`: lo mismo, pero con varios clientes (tenants) compartiendo la misma tabla.

## Dependencias

- **PostgreSQL** con la extensión **pgvector** instalada (los scripts ejecutan `CREATE EXTENSION IF NOT EXISTS vector`).
- **Python 3** y los paquetes de `requirements.txt`: `psycopg[binary]`, `pgvector`, `sentence-transformers`, `python-dotenv`, `tabulate`.

## Preparación

1. Crea y activa un entorno virtual e instala los paquetes:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copia `.env.example` a `.env` y pon los datos de tu base de datos:

   ```bash
   cp .env.example .env
   ```

   ```
   DATABASE_URL=postgresql://USUARIO:PASSWORD@localhost:5432/NOMBRE_BD
   ```

La primera vez se descarga el modelo `paraphrase-multilingual-MiniLM-L12-v2`, así que puede tardar un poco.

## 01 · Distancia coseno

```bash
python 01_cosine_similarity_search.py
```

Verás una tabla con las frases del dataset y otra con cada pregunta, las 2 frases más parecidas y su distancia coseno (cuanto más cerca de 0, más parecidas).

![Resultado del script 01](assets/terminal-result-screenshoot.png)

> Nota: el script borra y vuelve a crear la tabla `phrases` cada vez que se ejecuta.

## 02 · Multi-tenant

```bash
python 02_multi_tenant.py
```

Es el multitenant más sencillo: una sola tabla (`phrases_tenant`) con una columna `tenant_id` que indica a qué cliente pertenece cada frase. Las frases se reparten entre el tenant `1` y el `2`, y cada búsqueda filtra con `WHERE tenant_id = ...`.

Las mismas dos preguntas se hacen una vez por tenant. Cada tenant solo recibe sus propias frases, aunque haya otras más parecidas en los datos del otro. Por eso la misma pregunta devuelve respuestas y distancias distintas según el tenant.

![Resultado del script 02](assets/terminal-result-tenant-screenshoot.png)

> Nota: al terminar, el script borra las tablas `phrases` y `phrases_tenant`.
