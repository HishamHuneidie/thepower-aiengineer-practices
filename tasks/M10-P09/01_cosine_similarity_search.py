"""
    Semantic search using cosine distance
"""

# imports

from connection import connect, enable_vectors, create_table_phrases, delete_tables
from transformer import transform
from tabulate import tabulate

# connect and activate pgvector

conn = connect(True)
enable_vectors(conn)
create_table_phrases(conn)

# examples

PHRASES: list[str] = [
    'La inteligencia artificial permite automatizar tareas complejas mediante algoritmos avanzados.',
    'Los modelos de aprendizaje automático pueden analizar datos y generar predicciones.',
    'Los desarrolladores utilizan redes neuronales para construir aplicaciones inteligentes.',
    'El machine learning ayuda a las empresas a optimizar procesos y tomar mejores decisiones.',
    'Los sistemas basados en IA pueden aprender patrones y mejorar su rendimiento con el tiempo.',
    'El próximo verano quiero viajar a Japón para conocer su cultura y gastronomía.',
    'Los ejercicios cardiovasculares ayudan a fortalecer el corazón y mejorar la resistencia física.',
]

print()
print(tabulate([[phrase] for phrase in PHRASES], headers=['Dataset'], tablefmt='rounded_grid'))
print()

# save in pg

with conn.cursor() as cursor:
    cursor.executemany('INSERT INTO phrases (content, embedding) VALUES (%s, %s::VECTOR)', list(zip(PHRASES, transform(PHRASES).tolist())))

print()

# embedded questions

questions = [
    '¿Cómo puede la inteligencia artificial ayudar a las empresas a automatizar procesos y mejorar sus decisiones?',
    '¿De qué manera utilizan los desarrolladores las redes neuronales y el aprendizaje automático para crear aplicaciones inteligentes?',
]

# execute search

headers: list[str|float] = ['Question', 'Similar answers', 'Distance']
results_table: list[list[str|float]] = []

for question in questions:
    embedding = transform(question)
    
    results = conn.execute('SELECT content, embedding <=> %s AS distance FROM phrases ORDER BY 2 ASC LIMIT 2', (embedding,))

    contents = []
    distances = []
    for content, distance in results:
        contents.append(f'· {content}')
        distances.append(f'· {distance:.2f}')

    results_table.append([question, '\n'.join(contents), '\n'.join(distances)])

# show results

print('Cosine distance:')
print(tabulate(results_table, headers=headers, tablefmt='rounded_grid'))

# Clean all

delete_tables(conn)