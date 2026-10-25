# Búsqueda semántica con distancia coseno

Script: `01_cosine_similarity_search.py`. Guarda unas frases en PostgreSQL como vectores y busca las más parecidas a dos preguntas.

## Dependencias

- **PostgreSQL** con la extensión **pgvector** instalada (el script ejecuta `CREATE EXTENSION IF NOT EXISTS vector`).
- **Python 3** y los paquetes de `requirements.txt`: `psycopg[binary]`, `pgvector`, `sentence-transformers`, `python-dotenv`, `tabulate`.

## Cómo probarlo

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

3. Ejecuta el script:

   ```bash
   python 01_cosine_similarity_search.py
   ```

La primera vez descarga el modelo `paraphrase-multilingual-MiniLM-L12-v2`, así que puede tardar un poco.

## Qué verás

Una tabla con las frases del dataset y otra con cada pregunta, las 2 frases más parecidas y su distancia coseno (cuanto más cerca de 0, más parecidas).

![Resultado en la terminal](assets/terminal-result-screenshoot.png)

> Nota: el script borra y vuelve a crear la tabla `phrases` cada vez que se ejecuta.
